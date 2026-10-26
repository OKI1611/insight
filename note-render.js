/* note-render.js — 강의 노트(content/notes/<id>.json) 공용 렌더러 「교재형 읽기」
   watch.html(요약 노트 탭·PDF) · booklet.html(과목 교재·인쇄) 두 곳이 같은 HTML을 쓴다.
   스타일은 note.css(.nt-*). 데이터(JSON)는 손대지 않고 보여주는 방식만 바꾼다.

   BiblyNote.render(note, opts)  → HTML 문자열
     opts.idPrefix  절 앵커 접두어(여러 강의를 한 페이지에 둘 때 'l3-' 등)
     opts.title/meta/header/footer/tags  머리·꼬리 조각
   BiblyNote.toc(note, idPrefix, opts) → [{label, items:[{id,no,label}]}]
   BiblyNote.tocHTML(groups, opts)     → 사이드 목차 HTML (.nt-toc)
   BiblyNote.mobileTocHTML(groups)     → 접이식 목차(본문 위, PDF 제외)
   BiblyNote.track(tocEl, opts)        → 스크롤 따라 현재 절 강조(.on); 해제 함수 반환
*/
(function(){
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function pad(n){ return (n<10?'0':'')+n; }
  function paras(t, cls){
    return String(t||'').split(/\n+/).filter(function(x){ return x.trim(); })
      .map(function(p){ return '<p class="'+(cls||'nt-p')+'">'+esc(p.trim())+'</p>'; }).join('');
  }
  // 도입 한 문장 분리: 첫 문장(12~160자, 마침표·물음표·느낌표로 끝남)만 굵게. 데이터는 그대로.
  function splitLead(t){
    var s = String(t||'').trim();
    var m = s.match(/^([\s\S]{12,160}?[.?!。]['"’”)]?)\s+([\s\S]+)$/);
    return m ? [m[1], m[2]] : [s, ''];
  }
  var PB = 'page-break-inside:avoid;break-inside:avoid';
  var LABEL = { scr:'핵심 성구', terms:'핵심 용어', mis:'흔히 이렇게 오해합니다', sum:'한눈에 정리', app:'삶으로 가져가기', q:'묵상·토론 질문', more:'더 깊이 공부하려면' };

  function render(n, o){
    o = o || {}; n = n || {};
    var p = o.idPrefix || '', secs = n.sections || [], h = '';
    h += '<div class="nt'+(o.compact?' nt-compact':'')+'">';
    if(o.header) h += o.header;
    if(o.title) h += '<div class="nt-head"><h2 class="nt-title">'+esc(o.title)+'</h2>'+(o.meta?'<p class="nt-meta">'+esc(o.meta)+'</p>':'')+'</div>';
    if(n.thesis) h += '<div class="nt-key" id="'+p+'key" style="'+PB+'"><span class="nt-label">핵심 한 문장</span><p>'+esc(n.thesis)+'</p></div>';
    if(n.overview){ var ov = splitLead(n.overview); h += '<div class="nt-intro" id="'+p+'intro"><p class="nt-lead">'+esc(ov[0])+'</p>'+(ov[1]?paras(ov[1]):'')+'</div>'; }
    if(secs.length > 1){
      h += '<div class="nt-flow" id="'+p+'flow" style="'+PB+'"><p class="nt-flow-h">이 강의의 흐름 <span>'+secs.length+'단계 · 카드를 누르면 해당 절로 이동</span></p><div class="nt-flow-grid">';
      secs.forEach(function(s, i){
        var last = i === secs.length-1;
        h += '<a class="nt-step" href="#'+p+'s'+(i+1)+'" data-nt-go="'+p+'s'+(i+1)+'"><span class="nt-step-no">'+pad(i+1)+'</span><span class="nt-step-t">'+esc(s.heading||'')+'</span>'
           + (last ? '<span class="nt-step-next nt-step-end">마무리</span>' : '<span class="nt-step-next">다음 '+pad(i+2)+' →</span>') + '</a>';
      });
      h += '</div></div>';
    }
    if(n.background) h += '<div class="nt-box" id="'+p+'bg" style="'+PB+'"><p class="nt-box-h">배경 — 역사적·신학적 맥락</p>'+paras(n.background)+'</div>';
    secs.forEach(function(s, i){
      var b = splitLead(s.body), pts = (s.points||[]).map(function(x){ return '<li>'+esc(x)+'</li>'; }).join('');
      h += '<section class="nt-sec" id="'+p+'s'+(i+1)+'"><div class="nt-sec-head" style="'+PB+'"><span class="nt-badge">'+pad(i+1)+'</span><h3>'+(s.t?'<span class="nt-t">'+esc(s.t)+'</span>':'')+esc(s.heading||'')+'</h3></div>'
         + (b[0] ? '<p class="nt-lead">'+esc(b[0])+'</p>' : '') + (b[1] ? paras(b[1]) : '')
         + (pts ? '<ul class="nt-pts">'+pts+'</ul>' : '') + '</section>';
    });
    if((n.scriptures||[]).length){
      h += '<div class="nt-box nt-scr" id="'+p+'scr" style="'+PB+'"><p class="nt-box-h">'+LABEL.scr+'</p>'
         + n.scriptures.map(function(s){ return '<p><b>'+esc(s.ref||'')+'</b>'+(s.note?' — '+esc(s.note):'')+'</p>'; }).join('') + '</div>';
    }
    if((n.terms||[]).length){
      h += '<div class="nt-terms" id="'+p+'terms"><p class="nt-box-h">'+LABEL.terms+'</p>'
         + n.terms.map(function(t){ return '<p style="'+PB+'"><b>'+esc(t.term||'')+'</b> · '+esc(t.def||'')+'</p>'; }).join('') + '</div>';
    }
    if((n.misconceptions||[]).length){
      h += '<div class="nt-caveat" id="'+p+'mis"><p class="nt-box-h">'+LABEL.mis+'</p>'
         + n.misconceptions.map(function(m){ return '<div class="nt-mis" style="'+PB+'"><p class="w"><b>오해</b>'+esc(m.wrong||'')+'</p><p class="r"><b>바른 이해</b>'+esc(m.right||'')+'</p></div>'; }).join('') + '</div>';
    }
    if((n.takeaways||[]).length){
      h += '<div class="nt-box nt-sum" id="'+p+'sum" style="'+PB+'"><p class="nt-box-h">'+LABEL.sum+'</p><ol>'
         + n.takeaways.map(function(t){ return '<li>'+esc(t)+'</li>'; }).join('') + '</ol></div>';
    }
    var ap = n.application; if(ap && !Array.isArray(ap)) ap = String(ap).split(/\n+/).filter(function(x){ return x.trim(); });
    if(ap && ap.length){
      h += '<div class="nt-part" id="'+p+'app" style="'+PB+'"><p class="nt-box-h">'+LABEL.app+'</p><ul class="nt-list">'
         + ap.map(function(a){ return '<li>'+esc(a)+'</li>'; }).join('') + '</ul></div>';
    }
    if((n.questions||[]).length){
      h += '<div class="nt-part" id="'+p+'q" style="'+PB+'"><p class="nt-box-h">'+LABEL.q+'</p><ol class="nt-list">'
         + n.questions.map(function(q){ return '<li>'+esc(q)+'</li>'; }).join('') + '</ol></div>';
    }
    var fs = n.furtherStudy; if(fs && !Array.isArray(fs)) fs = String(fs).split(/\n+/).filter(function(x){ return x.trim(); });
    if(fs && fs.length){
      h += '<div class="nt-box" id="'+p+'more" style="'+PB+'"><p class="nt-box-h">'+LABEL.more+'</p><ul class="nt-list">'
         + fs.map(function(f){ return '<li>'+esc(f)+'</li>'; }).join('') + '</ul></div>';
    }
    if(o.tags && o.tags.length){
      h += '<div class="nt-tags" style="'+PB+'"><p class="nt-box-h">키워드</p>'+o.tags.map(function(t){ return '<span class="nt-tag">#'+esc(t)+'</span>'; }).join('')+'</div>';
    }
    if(o.footer) h += o.footer;
    return h + '</div>';
  }

  // 목차 데이터: ① 강의 흐름(핵심 한 문장 + 번호 절) ② 정리(성구·용어·오해·정리·적용·질문)
  function toc(n, p, o){
    p = p || ''; o = o || {}; n = n || {};
    var flow = [], wrap = [];
    if(n.thesis) flow.push({ id:p+'key', no:'★', label:'핵심 한 문장' });
    (n.sections||[]).forEach(function(s, i){ flow.push({ id:p+'s'+(i+1), no:pad(i+1), label:s.heading||('절 '+(i+1)) }); });
    if((n.scriptures||[]).length) wrap.push({ id:p+'scr', label:LABEL.scr });
    if((n.terms||[]).length) wrap.push({ id:p+'terms', label:LABEL.terms });
    if((n.misconceptions||[]).length) wrap.push({ id:p+'mis', label:'흔한 오해' });
    if((n.takeaways||[]).length) wrap.push({ id:p+'sum', label:LABEL.sum });
    if(n.application && n.application.length) wrap.push({ id:p+'app', label:LABEL.app });
    if((n.questions||[]).length) wrap.push({ id:p+'q', label:LABEL.q });
    var g = [];
    if(flow.length) g.push({ label:o.flowLabel||'강의 흐름', items:flow, id:o.groupId });
    if(wrap.length) g.push({ label:o.wrapLabel||'정리', items:wrap });
    return g;
  }
  function tocHTML(groups, o){
    o = o || {};
    var h = '<nav class="nt-toc'+(o.cls?' '+o.cls:'')+'">';
    if(o.title) h += '<p class="nt-toc-title">'+esc(o.title)+'</p>';
    (groups||[]).forEach(function(g, gi){
      h += '<div class="nt-toc-g'+(o.collapsible?' nt-toc-col':'')+(gi===0?' open':'')+'">'
         + (g.label ? '<p class="nt-toc-gh"'+(g.id?' data-nt-go="'+esc(g.id)+'"':'')+'>'+esc(g.label)+'</p>' : '');
      g.items.forEach(function(it){
        h += '<a class="nt-toc-i" href="#'+esc(it.id)+'" data-nt-go="'+esc(it.id)+'">'+(it.no?'<span class="nt-toc-no">'+esc(it.no)+'</span>':'<span class="nt-toc-no">·</span>')+'<span>'+esc(it.label)+'</span></a>';
      });
      h += '</div>';
    });
    return h + '</nav>';
  }
  function mobileTocHTML(groups){
    var h = '<details class="nt-toc-m" data-html2canvas-ignore="true"><summary>목차 — 바로 가기</summary><div class="nt-toc-m-body">';
    (groups||[]).forEach(function(g){
      g.items.forEach(function(it){ h += '<a class="nt-chip" href="#'+esc(it.id)+'" data-nt-go="'+esc(it.id)+'">'+(it.no&&it.no!=='★'?'<b>'+esc(it.no)+'</b> ':'')+esc(it.label)+'</a>'; });
    });
    return h + '</div></details>';
  }

  // 앵커 이동(고정 헤더만큼 띄움). data-nt-go 를 가진 요소 클릭을 문서 전체에서 받는다.
  var OFFSET = 92;
  function goTo(id){
    var el = document.getElementById(id); if(!el) return false;
    var top = el.getBoundingClientRect().top + window.pageYOffset - OFFSET;
    window.scrollTo({ top: top, behavior: 'smooth' });
    return true;
  }
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('[data-nt-go]'); if(!a) return;
    if(goTo(a.getAttribute('data-nt-go'))){ e.preventDefault(); var d = a.closest('details.nt-toc-m'); if(d) d.open = false; }
  });

  // 스크롤 추적: 목차 항목이 가리키는 요소 중 기준선(OFFSET+24px) 위에 있는 마지막 것을 .on 으로
  function track(tocEl, o){
    o = o || {}; var off = (o.offset || OFFSET) + 24, raf = 0;
    if(!tocEl) return function(){};
    function items(){ return Array.prototype.slice.call(tocEl.querySelectorAll('.nt-toc-i')); }
    function update(){
      raf = 0;
      var list = items(), cur = null, curGroup = null;
      for(var i=0;i<list.length;i++){
        var el = document.getElementById(list[i].getAttribute('data-nt-go')); if(!el) continue;
        if(el.getBoundingClientRect().top <= off) cur = list[i]; else break;
      }
      if(!cur && list.length) cur = list[0];
      list.forEach(function(a){ a.classList.toggle('on', a === cur); });
      if(cur){
        curGroup = cur.closest('.nt-toc-g');
        if(curGroup && curGroup.classList.contains('nt-toc-col')){
          tocEl.querySelectorAll('.nt-toc-g').forEach(function(g){ g.classList.toggle('open', g === curGroup); });
        }
        // 목차가 스크롤될 만큼 길면 현재 항목을 보이게
        if(tocEl.scrollHeight > tocEl.clientHeight + 4){
          var r = cur.getBoundingClientRect(), tr = tocEl.getBoundingClientRect();
          if(r.top < tr.top || r.bottom > tr.bottom) cur.scrollIntoView({ block:'nearest' });
        }
      }
    }
    function onScroll(){ if(!raf) raf = requestAnimationFrame(update); }
    window.addEventListener('scroll', onScroll, { passive:true });
    window.addEventListener('resize', onScroll);
    update();
    return function(){ window.removeEventListener('scroll', onScroll); window.removeEventListener('resize', onScroll); };
  }

  window.BiblyNote = { render:render, toc:toc, tocHTML:tocHTML, mobileTocHTML:mobileTocHTML, track:track, goTo:goTo, esc:esc, pad:pad, setOffset:function(v){ OFFSET = v; } };
})();
