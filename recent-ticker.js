/* recent-ticker.js — 재사용 컴포넌트: 이벤트 배너 + 회전 공지 티커
   어느 페이지든 <script src="/recent-ticker.js?v=1"></script> 한 줄로 삽입.
   #siteHeader 바로 아래(없으면 body 맨 위)에 끼워 넣고, 최근 글·자료·요청을 시간 간격으로 회전 노출.
   supabase 라이브러리가 없으면 자동으로 로드한다. */
(function(){
  if(window.__biblyTicker) return; window.__biblyTicker = true;
  var SB='https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';

  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  function ensureSb(cb){
    if(window.supabase && window.supabase.createClient){ cb(); return; }
    var s=document.createElement('script');
    s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
    s.onload=function(){ cb(); }; s.onerror=function(){};
    document.head.appendChild(s);
  }

  function buildNodes(){
    var wrap=document.createElement('div');
    wrap.innerHTML =
      '<a href="event.html" class="block bg-gradient-to-r from-gold to-[#caa24f] text-white">'
      + '<div class="max-w-6xl mx-auto px-5 py-3 flex items-center justify-center gap-2.5 text-center text-sm md:text-[15px] font-semibold flex-wrap">'
      + '<span class="text-base"></span>'
      + '<span>오픈 기념 — <b>가입하면 누구나 무료!</b> 신규 5일 · 추천 3개월 · 창립 1년</span>'
      + '<span class="inline-flex items-center gap-1 bg-white/20 hover:bg-white/30 transition px-3 py-1 rounded-full text-[13px]">혜택 보기 →</span>'
      + '</div></a>'
      + '<div id="recentTicker" class="hidden bg-white border-b" style="border-color:rgba(33,58,107,.08)">'
      + '<div class="max-w-6xl mx-auto px-5 py-2.5 flex items-center gap-3">'
      + '<span class="shrink-0 inline-flex items-center gap-1.5 text-[11px] font-bold px-3 py-1 rounded-full" style="background:#213a6b;color:#fff">새 소식</span>'
      + '<div class="flex-1 min-w-0 relative h-5 overflow-hidden">'
      + '<a id="tkItem" href="#" class="absolute inset-0 flex items-center gap-2 transition-opacity duration-500">'
      + '<span id="tkCat" class="shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded" style="color:#b8923f;background:rgba(184,146,63,.1)"></span>'
      + '<span id="tkTitle" class="flex-1 min-w-0 text-sm truncate" style="color:rgba(33,58,107,.8)"></span>'
      + '<span id="tkDate" class="shrink-0 text-xs hidden sm:inline" style="color:rgba(33,58,107,.35)"></span>'
      + '</a></div>'
      + '<div class="shrink-0 flex items-center gap-0.5" style="color:rgba(33,58,107,.4)">'
      + '<button onclick="biblyTkStep(-1)" title="이전" class="w-6 h-6 rounded-full hover:bg-ink/5 transition">‹</button>'
      + '<button id="tkPlay" onclick="biblyTkToggle()" title="멈춤/재생" class="w-6 h-6 rounded-full hover:bg-ink/5 transition text-[11px]"></button>'
      + '<button onclick="biblyTkStep(1)" title="다음" class="w-6 h-6 rounded-full hover:bg-ink/5 transition">›</button>'
      + '</div></div></div>';
    return wrap;
  }
  function insertAfter(ref, wrap){
    var n=ref.nextSibling;
    while(wrap.firstChild){ ref.parentNode.insertBefore(wrap.firstChild, n); }
  }
  // site-header.js가 #siteHeader를 <header>로 교체하므로, <header> 뒤(없으면 #siteHeader 뒤)에 삽입.
  function inject(attempt){
    if(document.getElementById('recentTicker')) return;
    var ref = document.querySelector('header') || document.getElementById('siteHeader');
    if(!ref){
      if((attempt||0) < 25){ setTimeout(function(){ inject((attempt||0)+1); }, 80); return; }
      // 최후 수단: body 최상단
      var w0=buildNodes(); while(w0.lastChild){ document.body.insertBefore(w0.lastChild, document.body.firstChild); }
      return;
    }
    insertAfter(ref, buildNodes());
  }

  function run(){
    var $=function(id){ return document.getElementById(id); };
    var strip=function(s){ return String(s||'').replace(/<[^>]*>/g,'').replace(/&[a-z]+;/g,' ').trim(); };
    function fdate(d){ if(!d) return ''; var x=new Date(d), now=new Date(); var diff=(now-x)/86400000;
      if(diff<1&&x.getDate()===now.getDate()) return '오늘'; if(diff<2) return '어제';
      return (x.getMonth()+1)+'.'+x.getDate(); }
    var tsb=window.supabase.createClient(SB,AK,{auth:{persistSession:false}});
    var TK=[], i=0, timer=null, playing=true;
    function show(){ if(!TK.length) return; var it=TK[i%TK.length], a=$('tkItem'); if(!a) return;
      a.style.opacity=0;
      setTimeout(function(){ $('tkCat').textContent=it.cat; $('tkTitle').textContent=it.title; $('tkDate').textContent=it.date; a.href=it.href; a.style.opacity=1; }, 180);
    }
    function reset(){ clearInterval(timer); if(playing) timer=setInterval(function(){ i=(i+1)%TK.length; show(); }, 4200); }
    window.biblyTkStep=function(d){ if(!TK.length) return; i=(i+d+TK.length)%TK.length; show(); reset(); };
    window.biblyTkToggle=function(){ playing=!playing; $('tkPlay').textContent=playing?'':'▶'; if(playing) reset(); else clearInterval(timer); };
    Promise.allSettled([
      tsb.from('columns').select('id,title,created_at').order('created_at',{ascending:false}).limit(4),
      tsb.from('community_posts').select('id,content,board,created_at').order('created_at',{ascending:false}).limit(4),
      tsb.from('resources').select('id,title,category,created_at').order('created_at',{ascending:false}).limit(3),
      tsb.from('lecture_requests').select('id,title,type,created_at').order('created_at',{ascending:false}).limit(2)
    ]).then(function(rs){
      var BN={free:'나눔',qna:'질문',prayer:'기도'};
      var get=function(k){ return (rs[k].status==='fulfilled'&&rs[k].value.data)||[]; };
      get(0).forEach(function(c){ TK.push({cat:'칼럼',title:strip(c.title)||'(제목 없음)',date:fdate(c.created_at),href:'column.html#col-'+c.id,t:c.created_at}); });
      get(1).forEach(function(p){ TK.push({cat:BN[p.board]||'나눔',title:strip(p.content).slice(0,46)||'(내용)',date:fdate(p.created_at),href:'community.html?board='+(p.board||'free'),t:p.created_at}); });
      get(2).forEach(function(r){ TK.push({cat:(r.category||'자료').slice(0,6),title:strip(r.title)||'(제목 없음)',date:fdate(r.created_at),href:'resources.html',t:r.created_at}); });
      get(3).forEach(function(r){ TK.push({cat:r.type==='feedback'?'건의':'요청',title:strip(r.title)||'(제목 없음)',date:fdate(r.created_at),href:'request.html',t:r.created_at}); });
      TK.sort(function(a,b){ return String(b.t||'').localeCompare(String(a.t||'')); }); TK.length=Math.min(TK.length,12);
      if(TK.length){ var band=$('recentTicker'); if(!band) return; band.classList.remove('hidden'); show(); reset();
        band.addEventListener('mouseenter',function(){ clearInterval(timer); });
        band.addEventListener('mouseleave',function(){ if(playing) reset(); });
      }
    });
  }

  ready(function(){ inject(); ensureSb(run); });
})();
