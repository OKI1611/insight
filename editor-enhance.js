/* editor-enhance.js — BIBLY 글쓰기 에디터 공통 개선
   ① 한글 폰트 다양화  ② 툴바 스크롤 고정  ③ 이미지 클릭 크기조절  ④ 모든 기기 반응형
   사용: 각 페이지에서 quill.js 로드 뒤에 <script src="/editor-enhance.js"></script>.
   - 폰트 whitelist를 등록하므로, 각 페이지 툴바의 font 배열에 아래 값들을 넣으면 노출됨. */
(function(){
  // [value(=실제 font-family), 한글 라벨]
  var FONTS = [
    ['sans-serif','고딕'], ['serif','명조'],
    ['Nanum Gothic','나눔고딕'], ['Nanum Myeongjo','나눔명조'],
    ['Nanum Pen Script','손글씨'], ['Gaegu','동글손글씨'],
    ['monospace','고정폭']
  ];
  window.BIBLY_EDITOR_FONTS = FONTS.map(function(f){ return f[0]; });

  // 1) 폰트 whitelist 등록 (Quill 인스턴스 생성 전에 실행되도록 head에서 로드)
  function registerFonts(){
    if(!window.Quill) return;
    try{
      var F = Quill.import('attributors/style/font');
      F.whitelist = window.BIBLY_EDITOR_FONTS.slice();
      Quill.register(F, true);
    }catch(e){}
  }
  registerFonts();

  // 2) 웹폰트 + CSS 주입 (1회)
  if(!document.getElementById('biblyEditorCSS')){
    var lk = document.createElement('link'); lk.rel = 'stylesheet';
    lk.href = 'https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&family=Nanum+Myeongjo:wght@400;700&family=Nanum+Pen+Script&family=Gaegu&display=swap';
    document.head.appendChild(lk);

    var rules = [
      // ② 툴바 고정 — 길게 써도 툴바가 위에 붙어 따라옴
      '.ql-toolbar.ql-snow{position:sticky;top:0;z-index:30;background:#fff;box-shadow:0 4px 12px -6px rgba(21,32,58,.35)}',
      // ④ 반응형 이미지 (작성/표시 공통)
      '.ql-editor img,.post-body img,.article img,.col-read img,.res-body img,.req-body img,.community-content img{max-width:100%;height:auto;border-radius:8px}',
      // ③ 이미지 선택 표시
      '.ql-editor img{cursor:pointer}',
      '.ql-editor img.bibly-sel{outline:3px solid #b8923f;outline-offset:2px}',
      // ③ 크기조절 바
      '#biblyImgBar{position:absolute;z-index:99999;background:#15203a;border-radius:9999px;box-shadow:0 8px 22px rgba(0,0,0,.35);display:flex;gap:2px;padding:4px}',
      '#biblyImgBar button{color:#fcfaf6;font-size:12px;font-weight:700;padding:6px 12px;border-radius:9999px;border:0;background:transparent;cursor:pointer;white-space:nowrap}',
      '#biblyImgBar button:active{background:rgba(255,255,255,.22)}',
      // 폰트 픽커
      '.ql-snow .ql-picker.ql-font{width:108px}',
      ".ql-snow .ql-picker.ql-font .ql-picker-label::before,.ql-snow .ql-picker.ql-font .ql-picker-item::before{content:'기본'}"
    ];
    FONTS.forEach(function(f){
      var v = f[0], label = f[1];
      rules.push(".ql-snow .ql-picker.ql-font .ql-picker-label[data-value=\"" + v + "\"]::before,"
               + ".ql-snow .ql-picker.ql-font .ql-picker-item[data-value=\"" + v + "\"]::before{content:'" + label + "';font-family:" + v + "}");
    });
    var st = document.createElement('style'); st.id = 'biblyEditorCSS'; st.textContent = rules.join('\n');
    document.head.appendChild(st);
  }

  // 3) 이미지 클릭 → 크기조절 바 (PC 마우스·모바일 터치 모두)
  var bar = null, selImg = null;
  function removeBar(){ if(bar){ bar.remove(); bar = null; } if(selImg){ selImg.classList.remove('bibly-sel'); selImg = null; } }
  function positionBar(img){
    if(!bar) return;
    var r = img.getBoundingClientRect();
    bar.style.top = (window.scrollY + r.top - 46) + 'px';
    bar.style.left = (window.scrollX + r.left) + 'px';
  }
  function showBar(img){
    removeBar(); selImg = img; img.classList.add('bibly-sel');
    bar = document.createElement('div'); bar.id = 'biblyImgBar';
    [['작게','30%'],['보통','55%'],['크게','80%'],['꽉참','100%']].forEach(function(o){
      var b = document.createElement('button'); b.textContent = o[0];
      b.addEventListener('mousedown', function(e){ e.preventDefault(); });
      b.addEventListener('click', function(e){
        e.preventDefault(); e.stopPropagation();
        img.setAttribute('style', 'width:' + o[1] + ';height:auto');
        setTimeout(function(){ positionBar(img); }, 0);
      });
      bar.appendChild(b);
    });
    document.body.appendChild(bar);
    positionBar(img);
  }
  function onTap(e){
    var t = e.target;
    if(t && t.tagName === 'IMG' && t.closest && t.closest('.ql-editor')){
      e.preventDefault(); showBar(t);
    } else if(!(t.closest && t.closest('#biblyImgBar'))){
      removeBar();
    }
  }
  document.addEventListener('click', onTap, true);
  window.addEventListener('scroll', function(){ if(selImg) positionBar(selImg); }, true);
  window.addEventListener('resize', function(){ if(selImg) positionBar(selImg); });
})();
