/* share.js — 공통 공유 시트 (강의·모든 글 공용)
   window.biblyShare(title, url) 호출 시 바텀시트로 공유 메뉴를 띄운다.
   영상 공유와 동일한 플랫폼 + 텔레그램. */
(function(){
  if(window.biblyShare) return;
  function open(t){ window.open(t, '_blank', 'noopener,noreferrer,width=640,height=660'); }
  function toast(m){
    var t=document.createElement('div'); t.textContent=m;
    t.style.cssText='position:fixed;left:50%;bottom:96px;transform:translateX(-50%);background:#213a6b;color:#ffffff;padding:10px 18px;border-radius:9999px;font-size:14px;z-index:2147483647;font-family:Pretendard,system-ui,sans-serif;box-shadow:0 8px 28px rgba(0,0,0,.3)';
    document.body.appendChild(t); setTimeout(function(){ t.remove(); }, 1800);
  }
  function copy(url){
    function done(){ toast('링크가 복사됐어요'); }
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(url).then(done, fallback); }
    else fallback();
    function fallback(){ try{ var ta=document.createElement('textarea'); ta.value=url; ta.style.cssText='position:fixed;left:-9999px'; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); done(); }catch(e){ prompt('아래 링크를 복사하세요', url); } }
  }
  window.biblyShare = function(title, url){
    title = String(title || document.title || 'BIBLY 바이블 인사이트').trim();
    url = url || location.href;
    var eu=encodeURIComponent(url), et=encodeURIComponent(title), etxt=encodeURIComponent(title+' '+url);
    var rows = [
      ['','네이버 블로그', function(){ open('https://blog.naver.com/openapi/share?url='+eu+'&title='+et); }],
      ['','네이버 밴드',   function(){ open('https://www.band.us/plugin/share?body='+etxt+'&route='+eu); }],
      ['','네이버 카페',   function(){ copy(url); }],
      ['','카카오톡',      function(){ copy(url); }],
      ['','텔레그램',      function(){ open('https://t.me/share/url?url='+eu+'&text='+et); }],
      ['','쓰레드(Threads)', function(){ open('https://www.threads.net/intent/post?text='+etxt); }],
      ['','인스타그램',    function(){ copy(url); }],
      ['𝕏','X(트위터)',     function(){ open('https://twitter.com/intent/tweet?text='+et+'&url='+eu); }],
      ['','페이스북',      function(){ open('https://www.facebook.com/sharer/sharer.php?u='+eu); }],
      ['SEP'],
      ['','링크 복사',     function(){ copy(url); }],
      ['⋯','기타(앱으로 공유)', function(){ if(navigator.share){ navigator.share({ title:title, url:url }).catch(function(){}); } else copy(url); }]
    ];
    var ov=document.createElement('div');
    ov.style.cssText='position:fixed;inset:0;z-index:2147483646;background:rgba(0,0,0,.5);display:flex;align-items:flex-end;justify-content:center;font-family:Pretendard,system-ui,sans-serif';
    ov.onclick=function(e){ if(e.target===ov) ov.remove(); };
    var sheet=document.createElement('div');
    sheet.style.cssText='background:#fff;width:100%;max-width:420px;border-radius:20px 20px 0 0;padding:14px 10px 24px;max-height:82vh;overflow:auto;box-shadow:0 -8px 40px rgba(0,0,0,.25)';
    var h='<div style="text-align:center;font-weight:700;color:#171717;padding:6px 0 4px;font-size:15px">공유하기</div>';
    h+='<p style="text-align:center;color:#9aa0ab;font-size:12px;margin:2px 0 10px;padding:0 18px;line-height:1.5;word-break:break-all">'+title.replace(/</g,'&lt;').slice(0,64)+'</p>';
    rows.forEach(function(r,i){
      if(r[0]==='SEP'){ h+='<div style="height:1px;background:rgba(21,32,58,.08);margin:6px 12px"></div>'; return; }
      h+='<button data-i="'+i+'" style="width:100%;text-align:left;display:flex;align-items:center;gap:13px;padding:12px 18px;border:0;background:none;font-size:15px;color:#171717;cursor:pointer;border-radius:10px"><span style="width:22px;text-align:center">'+r[0]+'</span>'+r[1]+'</button>';
    });
    sheet.innerHTML=h;
    sheet.querySelectorAll('button[data-i]').forEach(function(b){
      b.onmouseenter=function(){ b.style.background='rgba(21,32,58,.05)'; };
      b.onmouseleave=function(){ b.style.background='none'; };
      b.onclick=function(){ var fn=rows[+b.dataset.i][2]; ov.remove(); try{ fn&&fn(); }catch(e){} };
    });
    ov.appendChild(sheet); document.body.appendChild(ov);
  };
})();
