/**
 * 사이트 규모 집계 — content/stats.json 갱신
 *
 * guide.html '한눈에 보는 바이블 인사이트' 숫자판이 이 파일을 읽는다.
 * 원본 자료(사전 12.9MB · 권별 Q&A 4.1MB)는 너무 커서 브라우저에서 직접 셀 수 없으므로
 * 여기서 미리 세어 작은 JSON 하나로 만들어 둔다.
 *
 * 실행: node tools/build_stats.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// 저장소 경로에 한글이 있어도 안전하도록 fileURLToPath 사용
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'content', 'stats.json');

const read = (rel) => {
  try { return JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8')); }
  catch (e) { console.warn('건너뜀 ' + rel + ' — ' + e.message.slice(0, 80)); return null; }
};
const len = (v) => (Array.isArray(v) ? v.length : 0);

// ── 무료 강의 수 (course.json 의 각 레벨 lessons 합계) ──
const course = read('content/course.json');
let lectures = 0;
if (course) for (const lv of (course.levels || [])) lectures += len(lv.lessons);

// ── 원어 대조 새 번역 권수 ──
const books = read('bible/books.json');
const bibleBooks = Array.isArray(books) ? books.length : (books ? Object.keys(books).length : 0);

// ── 성경사전 항목 수 ──
const dictEntries = len(read('dictionary/entries.json'));

// ── 성경 Q&A 문항 수 (권별 + 주제별) ──
const qaBook = len(read('dictionary/qa-book.json'));
const qaTopic = len(read('dictionary/qa-topic.json'));
const qaItems = qaBook + qaTopic;

// ── 바이블 잉글리시 유닛 수 (참고용) ──
const beUnits = len(read('content/be-units.json'));

/** 화면에는 '이상'을 뜻하는 + 를 붙이므로 실제보다 작은 쪽으로 내림한다(과장 방지). */
const floorTo = (n, step) => Math.floor(n / step) * step;
const withComma = (n) => n.toLocaleString('ko-KR');

const stats = {
  updated: new Date().toISOString().slice(0, 10),
  note: '자동 집계 파일 — 직접 고치지 마세요. tools/build_stats.mjs 를 실행하면 갱신됩니다.',
  exact: { lectures, bibleBooks, dictEntries, qaItems, qaBook, qaTopic, beUnits },
  display: {
    lectures:    withComma(floorTo(lectures, 10)) + '+',
    bibleBooks:  String(bibleBooks) + '권',
    dictEntries: withComma(floorTo(dictEntries, 100)) + '+',
    qaItems:     withComma(floorTo(qaItems, 100)) + '+'
  }
};

const prev = (() => { try { return JSON.parse(fs.readFileSync(OUT, 'utf8')); } catch (e) { return null; } })();
fs.writeFileSync(OUT, JSON.stringify(stats, null, 2) + '\n', 'utf8');

console.log('저장 완료:', OUT);
console.log('  무료 강의      ' + lectures + ' → ' + stats.display.lectures);
console.log('  새 번역 권수   ' + bibleBooks + ' → ' + stats.display.bibleBooks);
console.log('  성경사전 항목  ' + dictEntries + ' → ' + stats.display.dictEntries);
console.log('  성경 Q&A 문항  ' + qaItems + ' (권별 ' + qaBook + ' + 주제별 ' + qaTopic + ') → ' + stats.display.qaItems);
console.log('  바이블잉글리시 ' + beUnits + '유닛');
if (prev && JSON.stringify(prev.exact) === JSON.stringify(stats.exact)) console.log('\n(수치 변동 없음)');
