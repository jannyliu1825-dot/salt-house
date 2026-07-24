/*
 * sw.js - 台南鹽行溫馨套房 PWA Service Worker
 * -------------------------------------------------
 * 快取策略：
 * 1. 核心檔案 (App Shell)：安裝時預先快取，採「Cache First」。
 * 2. 頁面導覽 (HTML)：採「Network First，失敗才用快取」，確保內容盡量最新，
 *    離線時仍可顯示上次快取的頁面。
 * 3. 外部資源 (Tailwind CDN、Font Awesome、Google Fonts、Unsplash 圖片等)：
 *    採「Stale While Revalidate」，先回應快取加速顯示，同時背景更新快取。
 */

const CACHE_VERSION = "v1.0.0";
const APP_SHELL_CACHE = `salt-house-app-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `salt-house-runtime-${CACHE_VERSION}`;

// 需要在安裝階段預先快取的核心檔案 (App Shell)
const APP_SHELL_FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-72.png",
  "./icons/icon-96.png",
  "./icons/icon-128.png",
  "./icons/icon-144.png",
  "./icons/icon-152.png",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-384.png",
  "./icons/icon-512.png",
  "./icons/icon-192-maskable.png",
  "./icons/icon-512-maskable.png",
];

// ------------------------------------------------------------
// install：預先快取 App Shell
// ------------------------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(APP_SHELL_CACHE)
      .then((cache) => cache.addAll(APP_SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

// ------------------------------------------------------------
// activate：清除舊版本快取
// ------------------------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter(
              (key) =>
                key !== APP_SHELL_CACHE && key !== RUNTIME_CACHE
            )
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ------------------------------------------------------------
// fetch：依請求類型套用不同快取策略
// ------------------------------------------------------------
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // 只處理 GET 請求，其餘 (POST 等) 直接放行
  if (request.method !== "GET") {
    return;
  }

  const requestUrl = new URL(request.url);

  // 1) 頁面導覽請求 (HTML) -> Network First
  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
    return;
  }

  // 2) 同源的靜態資源 (manifest / icons) -> Cache First
  if (requestUrl.origin === self.location.origin) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // 3) 外部 CDN 資源 (Tailwind、Font Awesome、Google Fonts、圖片) -> Stale While Revalidate
  event.respondWith(staleWhileRevalidate(request));
});

// ------------------------------------------------------------
// 快取策略實作
// ------------------------------------------------------------

// Cache First：先查快取，沒有才發網路請求並存入快取
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const cache = await caches.open(APP_SHELL_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return cached || Response.error();
  }
}

// Network First：先嘗試網路，失敗（離線）才回退到快取
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const cache = await caches.open(APP_SHELL_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    // 離線且無快取時，回退到首頁 (App Shell)
    const fallback = await caches.match("./index.html");
    return fallback || Response.error();
  }
}

// Stale While Revalidate：先回快取(若有)，同時背景更新
async function staleWhileRevalidate(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);

  const networkFetch = fetch(request)
    .then((response) => {
      // 允許 opaque (跨網域無 CORS header) 回應也一併快取，確保離線可用
      if (response && (response.status === 200 || response.type === "opaque")) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);

  return cached || networkFetch;
}

// ------------------------------------------------------------
// 監聽來自頁面的訊息 (例如：手動觸發更新)
// ------------------------------------------------------------
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
