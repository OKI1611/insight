/* protect.js — 번역·학습 자료 저작권 보호(대량 복제 억제)
   한 줄 include로 적용: <script src="/protect.js?v=1"></script>
   ※ 정적 사이트 특성상 완전 차단은 불가하나, 우클릭·드래그·대량복사·전체선택·저장/인쇄를
      억제하고 콘솔·푸터에 저작권을 고지해 무단 수집의 장벽과 법적 근거를 둔다.
   ※ 사이트의 정식 '구절 복사/공유 버튼'(출처 자동첨부)과 소량 인용은 그대로 허용. */
(function(){
  if(window.__biblyProtect) return; window.__biblyProtect = true;
  var LIMIT = 400; // 한 번에 복사 허용 글자수(이 이상이면 대량으로 간주, 차단)

  function isField(el){ return el && el.closest && el.closest('input,textarea,[contenteditable="true"]'); }
  function toast(m){
    var t = document.getElementById('cprtToast');
    if(!t){ t = document.createElement('div'); t.id='cprtToast';
      t.style.cssText='position:fixed;left:50%;bottom:84px;transform:translateX(-50%);z-index:2000;background:#213a6b;color:#fff;padding:10px 18px;border-radius:999px;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.22);max-width:90vw;text-align:center';
      document.body.appendChild(t); }
    t.textContent = m; t.style.display=''; clearTimeout(t._t); t._t=setTimeout(function(){ t.style.display='none'; }, 2400);
  }

  // 우클릭(컨텍스트 메뉴) 차단 — 입력창 제외
  document.addEventListener('contextmenu', function(e){ if(isField(e.target)) return; e.preventDefault(); toast('이 콘텐츠는 저작권 보호 대상입니다.'); });
  // 이미지·텍스트 드래그 차단
  document.addEventListener('dragstart', function(e){ if(isField(e.target)) return; e.preventDefault(); });

  // 대량 복사/잘라내기 차단(임계값 초과 시). 소량 인용은 허용(공유 기능과 호환)
  function guard(e){
    if(isField(e.target)) return;
    var s=''; try{ s=(window.getSelection&&window.getSelection().toString())||''; }catch(_){}
    if(s.length > LIMIT){ e.preventDefault(); e.stopImmediatePropagation(); toast('대량 복제는 제한됩니다 · 구절별 공유 버튼을 이용해 주세요'); }
  }
  document.addEventListener('copy', guard, true);
  document.addEventListener('cut', guard, true);

  // 단축키: 전체선택(Ctrl/⌘+A) 제한, 저장(Ctrl+S)·인쇄(Ctrl+P) 차단 — 입력창 제외
  document.addEventListener('keydown', function(e){
    if(isField(e.target)) return;
    var k=(e.key||'').toLowerCase(); var mod=e.ctrlKey||e.metaKey;
    if(!mod) return;
    if(k==='a'){ e.preventDefault(); }
    else if(k==='s'){ e.preventDefault(); toast('페이지 저장이 제한됩니다.'); }
    else if(k==='p'){ e.preventDefault(); toast('인쇄가 제한됩니다.'); }
  });

  // 콘솔 경고(개발자도구 통한 수집 억제)
  try{
    console.log('%c저작권 보호 콘텐츠','color:#00704a;font-size:18px;font-weight:bold');
    console.log('%cBIBLY 바이블 인사이트의 「KJV 새번역」·영어/신학 학습 자료는 저작권 보호 대상입니다.\n무단 복제·자동 수집(크롤링·스크래핑)·배포 시 민·형사상 책임을 질 수 있습니다.','color:#171717;font-size:13px');
  }catch(_){}

  // 푸터 저작권 고지 1줄 자동 삽입
  function addNotice(){
    if(document.getElementById('cprtNotice')) return;
    var p=document.createElement('p'); p.id='cprtNotice';
    p.style.cssText='text-align:center;font-size:11px;color:rgba(33,58,107,.4);padding:18px 16px 24px;line-height:1.6';
    p.innerHTML='© BIBLY 바이블 인사이트 · 「KJV 새번역」 및 영어·신학 학습 자료의 <b>무단 복제·자동 수집·배포를 금합니다.</b>';
    document.body.appendChild(p);
  }
  if(document.body) addNotice(); else document.addEventListener('DOMContentLoaded', addNotice);
})();
