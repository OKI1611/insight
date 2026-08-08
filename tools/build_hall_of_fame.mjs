/**
 * 명예의 전당 자동 집계 — content/hall-of-fame.json 갱신
 *
 * 유튜브 댓글을 모아 점수를 매기고 순위를 만든다. GitHub Actions 가 매일 실행 →
 * 변경분 커밋 → Cloudflare 자동 배포 → 홈 화면 반영.
 *
 * 실행: YT_API_KEY=xxxx node tools/build_hall_of_fame.mjs
 *   (테스트) MOCK=1 node tools/build_hall_of_fame.mjs   ← API 없이 가짜 데이터로 로직 점검
 *
 * 환경변수
 *   YT_API_KEY   (필수) 유튜브 Data API v3 키
 *   WINDOW_DAYS  집계 구간(기본 30). 'month' 로 두면 이번 달 1일부터 집계
 *   TOP_N        노출 인원(기본 15)
 *   SCAN_VIDEOS  훑을 최근 영상 수(기본 120)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// 저장소 경로에 한글이 있어도 안전하도록 fileURLToPath 사용(퍼센트 인코딩 방지)
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'content', 'hall-of-fame.json');

const CHANNEL_ID = 'UC82IOMnZud8NNt3BYzAxTMg';
const API = 'https://www.googleapis.com/youtube/v3';
const KEY = process.env.YT_API_KEY || '';
const MOCK = process.env.MOCK === '1';
const TOP_N = Number(process.env.TOP_N || 15);
const SCAN_VIDEOS = Number(process.env.SCAN_VIDEOS || 120);
const WINDOW = process.env.WINDOW_DAYS || '30';

// ── 점수 규칙 (그대로 화면 안내문에 쓰이니 바꾸면 basis 문구도 함께 바뀜) ──
const PT_COMMENT = 3;   // 댓글 1건
const PT_LIKE    = 1;   // 받은 좋아요 1개
const PT_RECENT  = 2;   // 최근 7일 이내 댓글은 건당 추가
const RECENT_DAYS = 7;

function windowStart() {
  const now = new Date();
  if (WINDOW === 'month') return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
  const d = new Date(now); d.setUTCDate(d.getUTCDate() - Number(WINDOW)); return d;
}

async function api(pathname, params) {
  const u = new URL(API + pathname);
  Object.entries(params).forEach(([k, v]) => u.searchParams.set(k, v));
  u.searchParams.set('key', KEY);
  const r = await fetch(u);
  if (!r.ok) throw new Error(pathname + ' ' + r.status + ' ' + (await r.text()).slice(0, 200));
  return r.json();
}

/** 최근 영상 ID 목록 */
async function recentVideoIds() {
  const ch = await api('/channels', { part: 'contentDetails', id: CHANNEL_ID });
  const uploads = ch.items?.[0]?.contentDetails?.relatedPlaylists?.uploads;
  if (!uploads) throw new Error('업로드 재생목록을 찾지 못했습니다');
  const ids = [];
  let pageToken = '';
  while (ids.length < SCAN_VIDEOS) {
    const p = await api('/playlistItems', {
      part: 'contentDetails', playlistId: uploads, maxResults: 50, ...(pageToken ? { pageToken } : {})
    });
    (p.items || []).forEach(it => { const v = it.contentDetails?.videoId; if (v) ids.push(v); });
    pageToken = p.nextPageToken || '';
    if (!pageToken) break;
  }
  return ids.slice(0, SCAN_VIDEOS);
}

/** 한 영상의 댓글을 최신순으로 훑되, 집계 구간보다 오래되면 멈춘다(할당량 절약) */
async function commentsOf(videoId, since) {
  const out = [];
  let pageToken = '';
  for (let page = 0; page < 10; page++) {
    let p;
    try {
      p = await api('/commentThreads', {
        part: 'snippet', videoId, order: 'time', maxResults: 100, textFormat: 'plainText',
        ...(pageToken ? { pageToken } : {})
      });
    } catch (e) {
      if (/commentsDisabled|videoNotFound|403|404/.test(String(e.message))) return out;  // 댓글 막힌 영상은 조용히 건너뜀
      throw e;
    }
    let hitOld = false;
    for (const it of (p.items || [])) {
      const s = it.snippet?.topLevelComment?.snippet; if (!s) continue;
      const at = new Date(s.publishedAt);
      if (at < since) { hitOld = true; continue; }
      out.push({
        authorId: s.authorChannelId?.value || s.authorDisplayName,
        handle: s.authorDisplayName,
        likes: Number(s.likeCount || 0),
        at
      });
    }
    if (hitOld) break;                       // 최신순이므로 오래된 게 나오면 이후는 볼 필요 없음
    pageToken = p.nextPageToken || '';
    if (!pageToken) break;
  }
  return out;
}

/** 가짜 데이터(로직 점검용) */
function mockComments(since) {
  const names = ['@디카페인-k9b', '@마라나타144', '@PERHAPSTODAY-vf2bn', '@w24hourprayhouse11',
                 '@고창휘-y8r', '@Hur-hd4vo', '@문이재76587', '@TV-cute-u9w', '@신규참여자-a1b'];
  const out = [];
  names.forEach((h, i) => {
    const n = 12 - i;                                  // 앞사람일수록 댓글 많게
    for (let k = 0; k < n; k++) {
      const daysAgo = (i + k) % 20;
      const at = new Date(Date.now() - daysAgo * 86400000);
      if (at < since) continue;
      out.push({ authorId: 'uid_' + i, handle: h, likes: (i + k) % 5, at });
    }
  });
  return out;
}

function aggregate(comments) {
  const now = Date.now();
  const recentCut = now - RECENT_DAYS * 86400000;
  const by = new Map();
  for (const c of comments) {
    if (!c.authorId) continue;
    const cur = by.get(c.authorId) || { handle: c.handle, comments: 0, likes: 0, recent: 0, lastAt: 0 };
    cur.handle = c.handle || cur.handle;
    cur.comments += 1;
    cur.likes += c.likes;
    if (c.at.getTime() >= recentCut) cur.recent += 1;
    cur.lastAt = Math.max(cur.lastAt, c.at.getTime());
    by.set(c.authorId, cur);
  }
  const rows = [...by.entries()].map(([id, v]) => ({
    id, handle: v.handle, comments: v.comments, likes: v.likes, recent: v.recent, lastAt: v.lastAt,
    score: v.comments * PT_COMMENT + v.likes * PT_LIKE + v.recent * PT_RECENT
  }));
  rows.sort((a, b) => b.score - a.score || b.comments - a.comments || b.lastAt - a.lastAt);
  return rows;
}

function main() {
  return (async () => {
    const since = windowStart();
    let comments;
    if (MOCK) {
      comments = mockComments(since);
      console.log('[MOCK] 가짜 댓글', comments.length, '건으로 로직 점검');
    } else {
      if (!KEY) { console.error('YT_API_KEY 가 없습니다. 기존 파일을 그대로 두고 종료합니다.'); process.exit(0); }
      const vids = await recentVideoIds();
      console.log('영상', vids.length, '편 훑는 중… (집계 시작일 ' + since.toISOString().slice(0, 10) + ')');
      comments = [];
      for (const v of vids) comments = comments.concat(await commentsOf(v, since));
      console.log('수집한 댓글', comments.length, '건');
    }

    const rows = aggregate(comments);
    if (!rows.length) { console.log('집계할 댓글이 없어 기존 파일을 유지합니다.'); return; }

    // 이전 순위를 읽어 변동(delta)·연속 진입(streak) 계산
    let prev = {};
    try {
      const old = JSON.parse(fs.readFileSync(OUT, 'utf8'));
      (old.members || []).forEach(m => { prev[m.handle] = { rank: m.rank, streak: m.streak || 1 }; });
    } catch (e) {}

    const top = rows.slice(0, TOP_N).map((r, i) => {
      const rank = i + 1;
      const p = prev[r.handle];
      return {
        rank,
        handle: r.handle,
        score: Math.round(r.score),
        comments: r.comments,
        likes: r.likes,
        prev: p ? p.rank : null,
        delta: p ? (p.rank - rank) : null,     // 양수면 상승
        isNew: !p,
        streak: p ? (p.streak || 1) + 1 : 1
      };
    });

    const now = new Date();
    const kst = new Date(now.getTime() + 9 * 3600000);
    const windowLabel = WINDOW === 'month' ? '이번 달' : ('최근 ' + WINDOW + '일');
    const out = {
      period: kst.toISOString().slice(0, 7),
      updated: kst.toISOString().slice(0, 19).replace('T', ' ') + ' KST',
      cadence: 'daily',
      windowLabel,
      basis: windowLabel + ' 댓글 ' + comments.length.toLocaleString() + '건 집계 · '
           + '댓글 ' + PT_COMMENT + '점 + 좋아요 ' + PT_LIKE + '점 + 최근 ' + RECENT_DAYS + '일 댓글 ' + PT_RECENT + '점',
      note: '매일 자동 집계됩니다. 점수 규칙은 tools/build_hall_of_fame.mjs 상단에서 바꿀 수 있습니다.',
      members: top
    };

    fs.writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n', 'utf8');
    console.log('저장 완료:', OUT);
    console.log('1~5위:', top.slice(0, 5).map(m => m.rank + '.' + m.handle + '(' + m.score + '점'
      + (m.isNew ? ' NEW' : m.delta > 0 ? ' ▲' + m.delta : m.delta < 0 ? ' ▼' + (-m.delta) : ' -') + ')').join('  '));
  })();
}

main().catch(e => { console.error('실패:', e.message); process.exit(1); });
