const CACHE_NAME='pic-20260429b';
const ASSETS=['./','/Pinellasiceco/index.html'];
self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(ASSETS).catch(()=>{})));
  self.skipWaiting();
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch',e=>{
  const url=new URL(e.request.url);
  if(url.origin===self.location.origin){
    e.respondWith(caches.match(e.request).then(cached=>{
      const fresh=fetch(e.request).then(res=>{
        if(res&&res.status===200){const copy=res.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,copy));}
        return res;
      }).catch(()=>cached);
      return cached||fresh;
    }));
  } else {
    e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
  }
});
