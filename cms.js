/* cms.js — 관리자 인플레이스 콘텐츠 편집
   · 모든 방문자: Supabase site_content['cms']에 저장된 문구를 [data-cms] 요소에 적용
   · 관리자(josephoh1611@gmail.com): 페이지에서 '글 편집' 모드로 직접 고치고 저장 → 즉시 반영
   ※ supabase_site_content.sql 실행 필요(site_content 테이블) */
(function(){
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var ADMIN = 'josephoh1611@gmail.com';
  var overrides = {}, editing = false;

  function session(){ try{ for(var i=0;i<localStorage.length;i++){ var k=localStorage.key(i); if(!/auth-token/.test(k)) continue; var v=JSON.parse(localStorage.getItem(k)); var s=(v&&v.user)?v:(v&&v.currentSession)?v.currentSession:null; if(s&&s.user){ if(s.expires_at&&s.expires_at*1000<Date.now()) return null; return s; } } }catch(e){} return null; }
  function isAdmin(){ var s=session(); return !!(s&&s.user&&s.user.email===ADMIN); }
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded',fn); }
  function toast(m){ var t=document.getElementById('cmsToast'); if(!t){ t=document.createElement('div'); t.id='cmsToast'; t.style.cssText='position:fixed;bottom:84px;left:50%;transform:translateX(-50%);z-index:120;background:#15203a;color:#fff;padding:10px 18px;border-radius:999px;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.2)'; document.body.appendChild(t);} t.textContent=m; t.style.display=''; clearTimeout(t._t); t._t=setTimeout(function(){t.style.display='none';},2400); }
  function apply(){ document.querySelectorAll('[data-cms]').forEach(function(el){ var k=el.getAttribute('data-cms'); if(overrides[k]!=null && overrides[k]!=='') el.innerHTML=overrides[k]; }); }

  // 저장본 로드 + 적용
  fetch(SB+'/rest/v1/site_content?select=data&key=eq.cms',{headers:{apikey:AK,Authorization:'Bearer '+AK}})
    .then(function(r){ return r.ok?r.json():[]; })
    .then(function(rows){ overrides=(rows[0]&&rows[0].data)||{}; ready(apply); })
    .catch(function(){});

  // 관리자 편집 바 — 관리자이면서 '편집 모드'(주소에 ?edit=1)일 때만 노출
  // 일반 열람 시에는(관리자로 로그인돼 있어도) 보이지 않음
  function editMode(){ return /[?&]edit=1\b/.test(location.search); }
  ready(function(){
    if(!isAdmin() || !editMode()) return;
    var bar=document.createElement('div');
    bar.style.cssText='position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:120;display:flex;gap:8px;align-items:center;background:#15203a;color:#fff;padding:7px 12px;border-radius:999px;box-shadow:0 8px 24px rgba(0,0,0,.25);font-size:13px';
    bar.innerHTML='<span style="opacity:.65">관리자 ·</span>'
      +'<button id="cmsToggle" style="background:#b8923f;color:#fff;border:0;padding:6px 13px;border-radius:999px;font-weight:700;cursor:pointer">✏️ 글 편집</button>'
      +'<button id="cmsSave" style="display:none;background:#fff;color:#15203a;border:0;padding:6px 13px;border-radius:999px;font-weight:700;cursor:pointer">💾 저장</button>'
      +'<button id="cmsCancel" style="display:none;background:transparent;color:#fff;border:0;padding:6px 8px;cursor:pointer;opacity:.8">취소</button>'
      +'<span id="cmsHint" style="opacity:.55"></span>';
    document.body.appendChild(bar);
    var n=document.querySelectorAll('[data-cms]').length;
    document.getElementById('cmsHint').textContent='이 페이지 '+n+'곳 편집 가능';
    document.getElementById('cmsToggle').onclick=function(){ setEdit(!editing); };
    document.getElementById('cmsSave').onclick=save;
    document.getElementById('cmsCancel').onclick=function(){ location.reload(); };
  });

  function setEdit(on){
    editing=on;
    document.querySelectorAll('[data-cms]').forEach(function(el){
      el.contentEditable=on?'true':'false';
      el.style.outline=on?'2px dashed #b8923f':'';
      el.style.outlineOffset=on?'3px':'';
      el.style.cursor=on?'text':'';
      el.title=on?('편집: '+el.getAttribute('data-cms')):'';
    });
    var sv=document.getElementById('cmsSave'), cn=document.getElementById('cmsCancel'), tg=document.getElementById('cmsToggle'), hn=document.getElementById('cmsHint');
    if(sv) sv.style.display=on?'':'none';
    if(cn) cn.style.display=on?'':'none';
    if(tg) tg.textContent=on?'편집 중':'✏️ 글 편집';
    if(hn) hn.textContent=on?'노란 점선 글자를 눌러 수정하세요':'';
  }
  function save(){
    var data={}; document.querySelectorAll('[data-cms]').forEach(function(el){ data[el.getAttribute('data-cms')]=el.innerHTML.trim(); });
    var s=session(); if(!s){ alert('로그인이 필요합니다'); return; }
    fetch(SB+'/rest/v1/site_content',{method:'POST',headers:{apikey:AK,Authorization:'Bearer '+(s.access_token||AK),'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify({key:'cms',data:data,updated_at:new Date().toISOString()})})
      .then(function(r){ if(r.ok){ overrides=data; setEdit(false); toast('✅ 저장 완료 — 모든 방문자에게 즉시 반영됩니다'); } else { return r.text().then(function(t){ alert('저장 오류: '+t+'\n\nsite_content 테이블/관리자 권한을 확인하세요.'); }); } })
      .catch(function(e){ alert('저장 오류: '+e); });
  }
})();
