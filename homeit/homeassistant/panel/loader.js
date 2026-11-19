// Entry point registered in panel_custom (module_url). This file never changes, so browsers may cache
// it freely. It reads version.txt (written by `homeit ha deploy-panel`) without caching and imports that
// build of home-panel.js, so a redeploy shows up on the next page load without restarting Home Assistant.
const base = new URL('./', import.meta.url);
let v = '';
try {
  v = (await (await fetch(new URL('version.txt', base), { cache: 'no-store' })).text()).trim();
} catch (e) {
  v = String(Date.now());
}
await import(new URL('home-panel.js?v=' + encodeURIComponent(v), base).href);
