const CACHE_NAME='pic-202605191729';
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
  if(url.origin!==self.location.origin){
    e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
    return;
  }
  const isHTML=e.request.mode==='navigate'||url.pathname.endsWith('.html')||url.pathname==='/Pinellasiceco/'||url.pathname==='/Pinellasiceco';
  if(isHTML){
    e.respondWith(
      fetch(e.request).then(res=>{
        if(res&&res.status===200){const copy=res.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,copy));}
        return res;
      }).catch(()=>caches.match(e.request))
    );
  } else {
    e.respondWith(caches.match(e.request).then(cached=>{
      const fresh=fetch(e.request).then(res=>{
        if(res&&res.status===200){const copy=res.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,copy));}
        return res;
      }).catch(()=>cached);
      return cached||fresh;
    }));
  }
});
