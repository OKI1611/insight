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
 *   WINDOW_DAYS  집계 구간(기본 90 = 최근 3개월). 'month' 로 두면 이번 달 1일부터
 *   TOP_N        노출 인원(기본 15)
 *   SCAN_VIDEOS  훑을 최근 영상 수(기본 200)
 *   MIN_DAYS     최소 활동 일수(기본 3) — 하루에 몰아쓴 사람이 상위에 오르지 않게
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// 저장소 경로에 한글이 있어도 안전하도록 fileURLToPath 사용(퍼센트 인코딩 방지)
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const CHANNEL_ID = 'UC82IOMnZud8NNt3BYzAxTMg';
const API = 'https://www.googleapis.com/youtube/v3';
const KEY = process.env.YT_API_KEY || '';
const MOCK = process.env.MOCK === '1';
// 로직 점검(MOCK)이 실제 명단 파일을 덮어쓰지 않도록 출력 경로를 분리한다.
const OUT = path.join(ROOT, 'content', MOCK ? 'hall-of-fame.mock.json' : 'hall-of-fame.json');
const TOP_N = Number(process.env.TOP_N || 10);
const SCAN_VIDEOS = Number(process.env.SCAN_VIDEOS || 200);
const WINDOW = process.env.WINDOW_DAYS || '90';        // 최근 3개월 누적
const MIN_DAYS = Number(process.env.MIN_DAYS || 3);    // 최소 활동 일수

// ── 점수 규칙 (그대로 화면 안내문에 쓰이니 바꾸면 basis 문구도 함께 바뀜) ──
//   설계 의도: '많이 쓴 사람'이 아니라 '꾸준히 쓰고 공감받은 사람'이 위로 오도록 한다.
//   ① 하루에 몰아쓰는 것을 막기 위해 하루 인정 댓글 수에 상한을 둔다.
//   ② 좋아요(=다른 시청자의 공감)에 큰 가중치를 준다. 적대적 댓글은 좋아요를 못 받는다.
//   ③ 여러 날에 걸쳐 참여한 사람에게 꾸준함 점수를 준다.
const PT_COMMENT   = 3;   // 댓글 1건
const PT_LIKE      = 4;   // 받은 좋아요 1개 (공감 = 가장 신뢰할 신호이므로 가장 큰 가중치)
const PT_ACTIVEDAY = 3;   // 댓글을 남긴 날 하루당 (꾸준함)
const DAILY_CAP    = 8;   // 하루에 점수로 인정하는 댓글 최대 건수
                          //  ↑ 댓글 참여도를 더 반영하려고 5→8 로 올림. 도배 방어는 아래 공감
                          //    관문(좋아요 절대치·비율)이 맡는다 — 많이 쓸수록 비율 관문이 빡빡해진다.

// ④ 공감 관문 — 아무도 공감하지 않는 댓글만 잔뜩 쓴 사람은 후보에서 제외한다.
//    (적대적·일방적 댓글은 다른 시청자의 좋아요를 받지 못한다는 점을 이용)
const MIN_LIKES = Number(process.env.MIN_LIKES || 3);        // 받은 좋아요 총합 최소치
const MIN_LIKE_RATIO = Number(process.env.MIN_LIKE_RATIO || 0.2);  // 댓글 1건당 최소 평균 좋아요

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
  const out = [];
  const push = (id, handle, daysAgo, likes) => {
    const at = new Date(Date.now() - daysAgo * 86400000);
    if (at >= since) out.push({ authorId: id, handle, likes, at });
  };
  // 정상 참여자: 여러 날에 걸쳐 꾸준히, 공감(좋아요)도 받음
  const names = ['@디카페인-k9b', '@마라나타144', '@PERHAPSTODAY-vf2bn', '@w24hourprayhouse11',
                 '@고창휘-y8r', '@Hur-hd4vo', '@문이재76587', '@TV-cute-u9w'];
  names.forEach((h, i) => {
    for (let k = 0; k < 12 - i; k++) push('uid_' + i, h, (k * 3 + i) % 80, (i + k) % 6);
  });
  // ① 도배형: 하루에 60건 몰아씀, 좋아요 0 → 하루 상한 + 최소 활동일수로 걸러져야 함
  for (let k = 0; k < 60; k++) push('uid_spam', '@도배테스트-zzz', 1, 0);
  // ② 안티형: 여러 날 쓰지만 아무도 공감 안 함(좋아요 0) → 상위권 진입 못해야 함
  for (let k = 0; k < 25; k++) push('uid_anti', '@안티테스트-yyy', k * 2, 0);
  // ③ 신규 진입자
  for (let k = 0; k < 6; k++) push('uid_new', '@신규참여자-a1b', k * 4, 3);
  return out;
}

/** 명예의 전당에서 제외할 핸들 (관리자가 content/hall-of-fame-exclude.json 에서 관리) */
function loadExcludes() {
  try {
    const p = path.join(ROOT, 'content', 'hall-of-fame-exclude.json');
    const d = JSON.parse(fs.readFileSync(p, 'utf8'));
    return new Set((d.exclude || []).map(s => String(s).trim().toLowerCase()).filter(Boolean));
  } catch (e) { return new Set(); }
}

function aggregate(comments) {
  const excludes = loadExcludes();
  const by = new Map();
  for (const c of comments) {
    if (!c.authorId) continue;
    const cur = by.get(c.authorId) || { handle: c.handle, comments: 0, likes: 0, days: new Map(), lastAt: 0 };
    cur.handle = c.handle || cur.handle;
    cur.comments += 1;
    cur.likes += c.likes;
    const day = c.at.toISOString().slice(0, 10);              // 날짜별로 묶어 하루 상한 적용
    cur.days.set(day, (cur.days.get(day) || 0) + 1);
    cur.lastAt = Math.max(cur.lastAt, c.at.getTime());
    by.set(c.authorId, cur);
  }

  const rows = [];
  for (const [id, v] of by) {
    if (excludes.has(String(v.handle || '').trim().toLowerCase())) continue;   // 제외 명단
    const activeDays = v.days.size;
    if (activeDays < MIN_DAYS) continue;                                       // 하루 몰아쓰기 배제
    if (v.likes < MIN_LIKES) continue;                                         // 공감 관문(절대치)
    if (v.likes / Math.max(1, v.comments) < MIN_LIKE_RATIO) continue;          // 공감 관문(비율)
    // 하루 DAILY_CAP 건까지만 점수로 인정 (도배 방지)
    let counted = 0;
    for (const n of v.days.values()) counted += Math.min(n, DAILY_CAP);
    rows.push({
      id, handle: v.handle, comments: v.comments, counted, likes: v.likes,
      activeDays, lastAt: v.lastAt,
      score: counted * PT_COMMENT + v.likes * PT_LIKE + activeDays * PT_ACTIVEDAY
    });
  }
  rows.sort((a, b) => b.score - a.score || b.likes - a.likes || b.activeDays - a.activeDays || b.lastAt - a.lastAt);
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

    // 이전 순위를 읽어 변동(delta)·순위 유지 일수(streak) 계산
    //  streak = '같은 순위를 며칠째 지키고 있는가'. 순위가 바뀌면 1로 초기화한다.
    //  (예전에는 명단에 남아 있기만 하면 계속 더해져, 2위가 1위보다 큰 값을 갖는 일이 있었다)
    let prev = {};
    let prevDay = '';
    try {
      const old = JSON.parse(fs.readFileSync(OUT, 'utf8'));
      (old.members || []).forEach(m => { prev[m.handle] = { rank: m.rank, streak: m.streak || 1 }; });
      prevDay = String(old.updated || '').slice(0, 10);
    } catch (e) {}
    // 같은 날 두 번 이상 돌려도 하루로만 센다(수동 실행으로 부풀지 않도록)
    const todayKst = new Date(Date.now() + 9 * 3600000).toISOString().slice(0, 10);
    const sameDay = prevDay === todayKst;

    const top = rows.slice(0, TOP_N).map((r, i) => {
      const rank = i + 1;
      const p = prev[r.handle];
      return {
        rank,
        handle: r.handle,
        score: Math.round(r.score),
        comments: r.comments,
        likes: r.likes,
        activeDays: r.activeDays,
        prev: p ? p.rank : null,
        delta: p ? (p.rank - rank) : null,     // 양수면 상승
        isNew: !p,
        // 순위를 그대로 지켰을 때만 하루 더한다
        streak: (p && p.rank === rank) ? ((p.streak || 1) + (sameDay ? 0 : 1)) : 1
      };
    });

    const now = new Date();
    const kst = new Date(now.getTime() + 9 * 3600000);
    const windowLabel = WINDOW === 'month' ? '이번 달'
                      : (Number(WINDOW) % 30 === 0 ? ('최근 ' + (Number(WINDOW) / 30) + '개월') : ('최근 ' + WINDOW + '일'));
    const out = {
      period: kst.toISOString().slice(0, 7),
      updated: kst.toISOString().slice(0, 19).replace('T', ' ') + ' KST',
      cadence: 'daily',
      windowLabel,
      basis: windowLabel + ' 누적 댓글 ' + comments.length.toLocaleString() + '건 집계 · '
           + '댓글 ' + PT_COMMENT + '점(하루 ' + DAILY_CAP + '건까지) + 좋아요 ' + PT_LIKE + '점 + 참여한 날 ' + PT_ACTIVEDAY + '점',
      note: '매일 자동 집계 · ' + windowLabel + ' 누적 기준. 꾸준히 참여하고 공감받은 분이 상위에 오릅니다.',
      members: top
    };

    fs.writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n', 'utf8');
    console.log('저장 완료:', OUT);
    console.log('1~5위:', top.slice(0, 5).map(m => m.rank + '.' + m.handle + '(' + m.score + '점'
      + (m.isNew ? ' NEW' : m.delta > 0 ? ' ▲' + m.delta : m.delta < 0 ? ' ▼' + (-m.delta) : ' -') + ')').join('  '));
  })();
}

main().catch(e => { console.error('실패:', e.message); process.exit(1); });
