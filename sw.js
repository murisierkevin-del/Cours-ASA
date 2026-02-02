const CACHE_NAME = "cours-asa-shell-v3";
const RUNTIME_CACHE = "cours-asa-runtime-v1";

// On précache seulement le "shell" (le cœur de l'app)
const SHELL_ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./themes/index.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== RUNTIME_CACHE)
          .map((k) => caches.delete(k))
      );
      await self.clients.claim();
    })()
  );
});

// Helper: cache-first (offline d'abord)
async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  const cache = await caches.open(RUNTIME_CACHE);
  cache.put(req, res.clone());
  return res;
}

// Helper: network-first (à jour si possible)
async function networkFirst(req) {
  try {
    const res = await fetch(req);
    const cache = await caches.open(RUNTIME_CACHE);
    cache.put(req, res.clone());
    return res;
  } catch (e) {
    const cached = await caches.match(req);
    if (cached) return cached;
    throw e;
  }
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // On gère seulement les requêtes du même site (ton github.io)
  if (url.origin !== self.location.origin) return;

  // Toujours à jour pour la liste des thèmes
  if (url.pathname.endsWith("/themes/index.json")) {
    event.respondWith(networkFirst(req));
    return;
  }

  // Thèmes JSON + images: cache dynamique (cache-first)
  if (url.pathname.includes("/themes/") || url.pathname.includes("/images/")) {
    event.respondWith(cacheFirst(req));
    return;
  }

  // Le reste (shell / fichiers de base)
  event.respondWith(cacheFirst(req));
});
