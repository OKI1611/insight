/* content-loader.js — 관리자 편집 즉시 반영
   content/course.json · content/site.json 요청을 가로채,
   Supabase site_content에 저장된 최신본이 있으면 그것을, 없으면 정적 파일을 돌려준다.
   반드시 페이지의 다른 스크립트보다 먼저(<head>) 로드되어야 함. */
(function(){
  if(window.__biblyLoaderReady) return; window.__biblyLoaderReady = true;
  var SB = 'https://bmxkndkwefdgsomlznoo.supabase.co';
  var AK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJteGtuZGt3ZWZkZ3NvbWx6bm9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzAwODIsImV4cCI6MjA5NjE0NjA4Mn0.l1yHhMVYwMqYSL8ub9PtrJPOl7CYr7yqstG2AER1EaU';
  var orig = window.fetch ? window.fetch.bind(window) : null;
  if(!orig) return;
  var cache = {};
  function live(key){
    if(cache[key] !== undefined) return Promise.resolve(cache[key]);
    return orig(SB + '/rest/v1/site_content?select=data&key=eq.' + key, { headers:{ apikey:AK, Authorization:'Bearer ' + AK } })
      .then(function(r){ return r.ok ? r.json() : []; })
      .then(function(rows){ var d = (rows && rows[0]) ? rows[0].data : null; cache[key] = d; return d; })
      .catch(function(){ cache[key] = null; return null; });
  }
  window.fetch = function(url, opts){
    try{
      var u = String((url && url.url) ? url.url : url);
      var m = u.match(/content\/(course|site)\.json/);
      var method = (opts && opts.method) ? String(opts.method).toUpperCase() : 'GET';
      if(m && method === 'GET'){
        var key = m[1];
        return live(key).then(function(d){
          if(d) return new Response(JSON.stringify(d), { status:200, headers:{ 'Content-Type':'application/json' } });
          return orig(url, opts);
        });
      }
    }catch(e){}
    return orig(url, opts);
  };
})();
