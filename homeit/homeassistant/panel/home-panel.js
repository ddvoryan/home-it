// home-panel: a Home Assistant custom panel (panel_custom) for a wall tablet and a phone.
//
// Generic code: every entity id comes from the panel's `config:` block in configuration.yaml
// (only sent to logged-in users). Nothing site-specific belongs in this file, because
// /config/www (/local/) is served without authentication.
//
// Layout: 3 columns, no scroll on a tablet in landscape; one scrolling column with full-screen
// sheets when the panel is narrower than 700px. Dark after sunset, light after sunrise.

const FONT_HREF = 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Unbounded:wght@500;600&display=swap';

const ICON = {
  bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
  lantern: '<path d="M9 3h6M10 3v2M14 3v2"/><path d="M8 5h8l-1 11H9z"/><path d="M12 16v5M9 21h6"/>',
  string: '<path d="M3 5c6 4 12 4 18 0"/><path d="M7 7.6v1.9M12 8.5v1.9M17 7.6v1.9"/><circle cx="7" cy="11.7" r="1.7"/><circle cx="12" cy="12.6" r="1.7"/><circle cx="17" cy="11.7" r="1.7"/>',
  drop: '<path d="M12 3c3.2 4.2 5.5 7 5.5 10a5.5 5.5 0 0 1-11 0c0-3 2.3-5.8 5.5-10z"/>',
  umbrella: '<path d="M3 12a9 9 0 0 1 18 0z"/><path d="M12 12v6.5a2 2 0 0 0 4 0"/>',
  bolt: '<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>',
  bell: '<path d="M6 9a6 6 0 0 1 12 0c0 6.5 2.5 8 2.5 8h-17S6 15.5 6 9"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
  belloff: '<path d="M6 9a6 6 0 0 1 12 0c0 6.5 2.5 8 2.5 8h-17S6 15.5 6 9"/><path d="M10 20.5a2 2 0 0 0 4 0"/><path d="M3 3l18 18"/>',
  leaf: '<path d="M5 20c0-9 6-15 15-15 0 9-6 15-14 15"/><path d="M5 20l9-9"/>',
  sprinkler: '<path d="M12 21v-6M8 21h8"/><path d="M12 15c0-4-3-6-7-7M12 15c0-4 3-6 7-7M12 15V6"/>',
  sofa: '<path d="M4 11V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3"/><path d="M2 13a2 2 0 0 1 4 0v2h12v-2a2 2 0 0 1 4 0v5H2z"/>',
  dish: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 8h16M8 5.5h.01"/><circle cx="12" cy="14.5" r="3.5"/>',
  garage: '<path d="M3 21V9l9-6 9 6v12"/><path d="M7 21v-8h10v8M7 17h10"/>',
  tree: '<path d="M12 22v-5"/><path d="M12 2l6 8h-3l4 7H5l4-7H6z"/>',
  home: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
  tower: '<path d="M12 2L7 22M12 2l5 20M9 9h6M8 14h8M7 19h10"/>',
  car: '<path d="M4 16v-4l2.2-5.2A2 2 0 0 1 8 5.5h8a2 2 0 0 1 1.8 1.3L20 12v4"/><path d="M3 16h18v2.5H3zM4 12h16"/>',
  door: '<path d="M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17"/><path d="M4 21h16"/><path d="M14.5 12h.01"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  server: '<rect x="4" y="4" width="16" height="7" rx="1.5"/><rect x="4" y="13" width="16" height="7" rx="1.5"/><path d="M8 7.5h.01M8 16.5h.01"/>',
  camera: '<rect x="3" y="7" width="12" height="10" rx="2"/><path d="M15 10.5l6-3.5v10l-6-3.5"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  theme: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17a8.5 8.5 0 0 0 0-17z" fill="currentColor"/>',
  fan: '<circle cx="12" cy="12" r="1.8"/><path d="M12 10.2C11 6 12 3 14.5 3c2.6 0 2.2 4.6-2.5 7.2M13.8 12c4.2-1 7.2 0 7.2 2.5 0 2.6-4.6 2.2-7.2-2.5M12 13.8c1 4.2 0 7.2-2.5 7.2-2.6 0-2.2-4.6 2.5-7.2M10.2 12C6 13 3 12 3 9.5 3 6.9 7.6 7.3 10.2 12"/>',
  laser: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 8v4M8 20h8M12 16v4"/>',
  air: '<path d="M3 8h11a3 3 0 1 0-3-3M3 12h15a3 3 0 1 1-3 3M3 16h7"/>',
  plug: '<path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0zM12 18v4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', minus: '<path d="M5 12h14"/>',
  chev: '<path d="M9 6l6 6-6 6"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  play: '<path d="M8.5 5.5v13l10-6.5z" fill="currentColor"/>',
  cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
};
const ic = (n, c = '') => `<svg class="ic ${c}" viewBox="0 0 24 24" aria-hidden="true">${ICON[n] || ICON.plug}</svg>`;

const WX_KIND = {
  'clear-night': 'night', cloudy: 'cloud', fog: 'cloud', hail: 'rain', lightning: 'storm', 'lightning-rainy': 'storm',
  partlycloudy: 'pcloudy', pouring: 'rain', rainy: 'rain', snowy: 'rain', 'snowy-rainy': 'rain', sunny: 'sun',
  windy: 'cloud', 'windy-variant': 'cloud', exceptional: 'cloud',
};
const WX_LABEL = {
  'clear-night': 'Clear', cloudy: 'Cloudy', fog: 'Fog', hail: 'Hail', lightning: 'Thunderstorms', 'lightning-rainy': 'Thunderstorms',
  partlycloudy: 'Partly cloudy', pouring: 'Heavy rain', rainy: 'Rain', snowy: 'Snow', 'snowy-rainy': 'Sleet', sunny: 'Sunny',
  windy: 'Windy', 'windy-variant': 'Windy', exceptional: 'Unusual weather',
};
function wx(k, size = 24) {
  const S = 'var(--solar)', G = 'var(--grid)', H = 'var(--home)', D = 'var(--d)';
  const cloud = (y = 0) => `<path stroke="${G}" d="M7 ${17 + y}a4 4 0 0 1-.5-8A6 6 0 0 1 18 ${8 + y}a4.5 4.5 0 0 1-.5 9z"/>`;
  const sun = '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>';
  const g = {
    sun: `<g stroke="${S}">${sun}</g>`,
    cloud: cloud(0),
    rain: `${cloud(-3)}<path stroke="${H}" d="M8 17.5l-1 3M12 17.5l-1 3M16 17.5l-1 3"/>`,
    storm: `${cloud(-3)}<path stroke="${S}" d="M12.5 15l-2.5 4h3.5l-2 4"/><path stroke="${H}" d="M7.5 17.5l-1 2.5M17 17.5l-1 2.5"/>`,
    pcloudy: `<g stroke="${S}"><path d="M8 2.5v1.5M3 7.5h1.5M4.6 4.1l1 1"/><path d="M5.2 10.4A3.5 3.5 0 0 1 11.3 6"/></g><path stroke="${G}" d="M8.5 20a3.5 3.5 0 0 1-.4-7A5 5 0 0 1 17.5 12.5a3.8 3.8 0 0 1-.5 7.5z"/>`,
    night: `<path stroke="${D}" d="M19.5 13.5A7.5 7.5 0 1 1 10 4a6 6 0 0 0 9.5 9.5z"/>`,
    ncloudy: `<path stroke="${D}" d="M11.5 8.5A4.5 4.5 0 0 1 6 3.2 4.5 4.5 0 1 0 11.5 8.5z"/><path stroke="${G}" d="M9 20.5a3.5 3.5 0 0 1-.4-7A5 5 0 0 1 18 13a3.8 3.8 0 0 1-.5 7.5z"/>`,
  };
  return `<svg class="wx" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true">${g[k] || g.cloud}</svg>`;
}

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmtTime = (d) => d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
const fmtHour = (h) => (h % 12 || 12) + (h < 12 || h === 24 ? ' AM' : ' PM');
const sameDay = (a, b) => a.toDateString() === b.toDateString();
function relTime(d, now = new Date()) {
  if (!d || isNaN(d)) return '—';
  if (sameDay(d, now)) return fmtTime(d);
  const y = new Date(now); y.setDate(y.getDate() - 1);
  if (sameDay(d, y)) return 'Yesterday ' + fmtTime(d);
  if (now - d < 6 * 864e5) return d.toLocaleDateString([], { weekday: 'short' }) + ' ' + fmtTime(d);
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// ---- time-of-use: peak hours on weekdays that are not holidays (US federal holidays most utilities use) ----
function holidays(y) {
  const d = (m, day) => new Date(y, m, day);
  const nth = (m, wd, n) => { const f = new Date(y, m, 1); return new Date(y, m, 1 + ((wd - f.getDay() + 7) % 7) + 7 * (n - 1)); };
  const last = (m, wd) => { const l = new Date(y, m + 1, 0); return new Date(y, m, l.getDate() - ((l.getDay() - wd + 7) % 7)); };
  const fixed = [d(0, 1), d(6, 4), d(10, 11), d(11, 25)].map((x) => (x.getDay() === 0 ? new Date(y, x.getMonth(), x.getDate() + 1) : x));
  return [...fixed, nth(1, 1, 3), last(4, 1), nth(8, 1, 1), nth(10, 4, 4)].map((x) => x.toDateString());
}
function isOffDay(day) {
  return day.getDay() === 0 || day.getDay() === 6 || holidays(day.getFullYear()).includes(day.toDateString());
}
function tou(now, c = {}) {
  const ps = c.peak_start ?? 17, pe = c.peak_end ?? 20;
  const off = isOffDay(now), h = now.getHours() + now.getMinutes() / 60;
  const peak = !off && h >= ps && h < pe;
  let next = '';
  if (peak) next = `until ${fmtHour(pe)}`;
  else if (!off && h < ps) next = `peak ${fmtHour(ps).replace(' PM', '')}–${fmtHour(pe)}`;
  else {
    const d = new Date(now);
    for (let i = 1; i <= 7; i++) {
      d.setDate(d.getDate() + 1);
      if (!isOffDay(d)) { next = i === 1 ? `until ${fmtHour(ps)} tomorrow` : `until ${d.toLocaleDateString([], { weekday: 'long' })} ${fmtHour(ps)}`; break; }
    }
  }
  return { peak, off, ps, pe, h, next };
}

const CSS = `
:host{display:block;height:100vh;height:100dvh;
  --f-num:"Unbounded",ui-sans-serif,system-ui,sans-serif;
  --f-ui:"Plus Jakarta Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
*{box-sizing:border-box}
button{font:inherit;color:inherit}
.root{
  --ground:#080b11; --t:#eef2f7; --d:#8d96a8;
  --solar:#fbbf24; --ok:#34d399; --home:#38bdf8; --grid:#94a3b8; --ev:#2dd4bf; --acc:#8d7bff; --heat:#ff8c1a; --alert:#ff5d7a;
  --card:rgba(255,255,255,.045); --brd:rgba(255,255,255,.08); --tile:rgba(255,255,255,.055); --tile-brd:rgba(255,255,255,.06);
  --shadow:none; --scrim:rgba(3,5,9,.62); --sheet:#10141d; --saver:#000000; --saver-t:rgba(238,242,247,.5); --mood:transparent;
  color-scheme:dark;position:relative;height:100%;overflow:hidden;container:scr/inline-size;
  font-family:var(--f-ui);color:var(--t);background:var(--ground);-webkit-tap-highlight-color:transparent;user-select:none}
.root[data-mode="light"]{
  --ground:#eef3f8; --t:#152633; --d:#4f6170;
  --solar:#b7770c; --ok:#0f8a5f; --home:#1683c7; --grid:#64748b; --ev:#0d8f86; --acc:#6354b9; --heat:#c2571a; --alert:#c53757;
  --card:#ffffff; --brd:rgba(21,38,51,.06); --tile:#f2f5f9; --tile-brd:rgba(21,38,51,.05);
  --shadow:0 1px 2px rgba(21,38,51,.05),0 12px 28px -14px rgba(21,38,51,.2); --scrim:rgba(21,38,51,.38); --sheet:#ffffff;
  color-scheme:light}
.screen{position:absolute;inset:0;overflow:hidden;
  background:
    radial-gradient(900px 620px at 12% -12%,color-mix(in srgb,var(--mood) 24%,transparent),transparent 62%),
    radial-gradient(760px 520px at 105% 112%,color-mix(in srgb,var(--mood) 13%,transparent),transparent 62%),
    var(--ground)}
.wrap{height:100%;display:flex;flex-direction:column;gap:12px;
  padding:max(14px,env(safe-area-inset-top,0px)) max(16px,env(safe-area-inset-right,0px)) max(16px,env(safe-area-inset-bottom,0px)) max(16px,env(safe-area-inset-left,0px))}
.ic{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}
.wx{fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}
.lbl{font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--d)}
.sub{font-size:13px;font-weight:600;color:var(--d)}
.num{font-family:var(--f-num);font-weight:500;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 10px;font-weight:800;font-size:11px;
  letter-spacing:.08em;text-transform:uppercase;background:color-mix(in srgb,var(--c) 16%,transparent);color:var(--c);white-space:nowrap}
.dot{width:8px;height:8px;border-radius:50%;background:var(--c);flex:none}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}

.top{display:grid;grid-template-columns:auto auto 1fr auto auto auto;grid-template-areas:"greet people status wx theme clock";
  align-items:center;gap:20px;min-height:58px;flex:none;padding:0 4px}
.greet{grid-area:greet;display:flex;align-items:center;gap:12px}
.hi{font-family:var(--f-num);font-weight:600;font-size:21px;letter-spacing:-.02em}
.date{font-size:13px;font-weight:600;color:var(--d);margin-top:2px}
.people{grid-area:people;display:flex;gap:6px}
.pp{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;font-family:var(--f-num);font-weight:600;font-size:14px;
  color:var(--c);background:color-mix(in srgb,var(--c) 18%,transparent);border:1.5px solid color-mix(in srgb,var(--c) 55%,transparent)}
.pp.away{opacity:.35;border-style:dashed}
.status{all:unset;grid-area:status;justify-self:start;cursor:pointer;display:inline-flex;align-items:center;gap:10px;
  min-height:44px;padding:0 16px;border-radius:999px;font-weight:700;font-size:14px;
  background:color-mix(in srgb,var(--c) 12%,transparent);color:var(--t)}
.status.calm{background:transparent;color:var(--d)}
.wxmini{grid-area:wx;display:flex;align-items:center;gap:8px;font-family:var(--f-num);font-weight:500;font-size:20px;letter-spacing:-.03em}
.iconbtn{all:unset;cursor:pointer;width:44px;height:44px;border-radius:14px;display:grid;place-items:center;
  background:var(--tile);border:1px solid var(--tile-brd);color:var(--d);flex:none}
.themebtn{grid-area:theme}
.clock{grid-area:clock;font-family:var(--f-num);font-weight:500;font-size:42px;letter-spacing:-.05em;line-height:1;font-variant-numeric:tabular-nums}
.clock small{font-size:13px;letter-spacing:0;margin-left:4px;color:var(--d);font-weight:600}

.body{flex:1;min-height:0;display:grid;grid-template-columns:1.14fr 1fr 1fr;gap:12px}
.col{display:flex;flex-direction:column;gap:12px;min-height:0;min-width:0}
.card{background:var(--card);border:1px solid var(--brd);border-radius:26px;padding:15px 16px 16px;box-shadow:var(--shadow);
  -webkit-backdrop-filter:blur(22px) saturate(140%);backdrop-filter:blur(22px) saturate(140%);
  display:flex;flex-direction:column;gap:12px;min-height:0;overflow:hidden;cursor:pointer;position:relative;flex:none}
.card.grow{flex:1 1 auto}
.card-h{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.ct{font-family:var(--f-num);font-weight:600;font-size:15px;margin:0;letter-spacing:-.01em;white-space:nowrap}
.st{font-size:13px;font-weight:600;color:var(--d);text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.tou-bar{position:relative;display:flex;height:14px;border-radius:999px;overflow:hidden;gap:2px}
.tou-bar span{height:100%;background:color-mix(in srgb,var(--grid) 28%,transparent)}
.tou-bar span.pk{background:var(--solar)}
.tou-wrap{position:relative;padding-top:6px}
.now{position:absolute;top:2px;width:3px;height:22px;border-radius:2px;background:var(--t);transform:translateX(-50%);box-shadow:0 0 0 2px var(--ground)}
.ticks{position:relative;height:16px;margin-top:6px;font-size:11px;font-weight:700;color:var(--d)}
.ticks span{position:absolute;transform:translateX(-50%);white-space:nowrap}
.ticks span:first-child{transform:none}.ticks span:last-child{transform:translateX(-100%)}
.flow{width:100%;height:auto;display:block;max-width:460px;margin:0 auto}
.flow text{font-family:var(--f-ui);font-size:12px;font-weight:700;fill:var(--d);text-anchor:middle}
.flow text.v{font-size:13px;fill:var(--t)}
.flow .base{stroke:color-mix(in srgb,var(--grid) 35%,transparent);stroke-width:2;stroke-linecap:round}
.flow .dots{stroke-width:5;stroke-linecap:round;stroke-dasharray:0 14;animation:run 1.1s linear infinite}
@keyframes run{to{stroke-dashoffset:-14}}
.bill{display:grid;grid-template-columns:auto 1fr;gap:4px 18px;align-items:end}
.hero{font-family:var(--f-num);font-weight:500;font-size:44px;letter-spacing:-.05em;line-height:1;font-variant-numeric:tabular-nums}
.hero small{font-size:15px;letter-spacing:0;color:var(--d);font-weight:600;margin-left:3px}
.bbar{position:relative;height:12px;border-radius:999px;background:color-mix(in srgb,var(--grid) 22%,transparent);margin-bottom:8px}
.bbar .fill{position:absolute;inset:0 auto 0 0;border-radius:999px;background:var(--grid)}
.bbar .mk{position:absolute;top:-5px;width:2px;height:22px;background:var(--t);border-radius:2px}
.bbar .mk.typ{background:var(--d);opacity:.7}
.blegend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;font-weight:700;color:var(--d);margin-top:6px}
.eline{display:flex;align-items:baseline;gap:10px}
.eline .ic{margin-left:auto;color:var(--d);align-self:center}

.qa{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.tile{all:unset;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;gap:11px;min-height:62px;padding:10px 12px;
  border-radius:18px;background:var(--tile);border:1px solid var(--tile-brd);transition:background .3s,box-shadow .3s,border-color .3s;min-width:0}
.tile .bub{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;color:var(--d);background:color-mix(in srgb,var(--d) 10%,transparent);flex:none}
.tile .tx{min-width:0}
.tile .nm{font-size:14.5px;font-weight:700;line-height:1.2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tile .sv{font-size:12.5px;font-weight:600;color:var(--d);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tile.na{opacity:.45}
.on{background:color-mix(in srgb,var(--c) 13%,var(--tile));border-color:color-mix(in srgb,var(--c) 38%,transparent);
  box-shadow:0 0 26px -8px color-mix(in srgb,var(--c) 70%,transparent)}
.on .bub{color:var(--c);background:color-mix(in srgb,var(--c) 18%,transparent)}
.on .sv{color:var(--c)}
.armed{border-color:var(--alert)!important;box-shadow:0 0 0 1px var(--alert)!important}
.armed .sv{color:var(--alert)!important}
.rooms{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr;gap:8px;flex:1;min-height:0}
.room{all:unset;box-sizing:border-box;cursor:pointer;display:block;container:room/size;overflow:hidden;
  border-radius:20px;background:var(--tile);border:1px solid var(--tile-brd);min-width:0;min-height:0;transition:background .3s,box-shadow .3s}
.room .ri{box-sizing:border-box;height:100%;display:flex;flex-direction:column;justify-content:space-between;gap:4px;padding:10px 12px}
.room .rb{display:block;min-width:0}
.room .rb>span{display:block}
.room .rt{display:flex;justify-content:space-between;align-items:center;color:var(--d)}
.room .rn{font-size:14px;font-weight:700;color:var(--t)}
.room .rv{font-family:var(--f-num);font-weight:500;font-size:17px;letter-spacing:-.04em;line-height:1.1}
.room .rs{font-size:12px;font-weight:600;color:var(--d);line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.room.on .rt{color:var(--c)}

.wnow{display:flex;align-items:center;gap:14px}
.wnow .hero{font-size:46px}
.wdet{font-size:13px;font-weight:600;color:var(--d);line-height:1.5;min-width:0}
.wdet b{color:var(--t);font-weight:700}
.fc{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.fc div{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 4px;border-radius:16px;background:var(--tile);min-width:0}
.fc .n{font-size:12px;font-weight:700;color:var(--d);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.fc .t{font-family:var(--f-num);font-weight:500;font-size:16px;letter-spacing:-.03em}
.fc .p{font-size:11.5px;font-weight:700;color:var(--home)}
.yard{all:unset;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:16px;
  background:var(--tile);border:1px solid var(--tile-brd);min-height:52px}
.yard .yt{flex:1;min-width:0}
.yard .nm{font-size:14px;font-weight:700}
.yard .bub{color:var(--home)}

.rows{display:flex;flex-direction:column;gap:2px}
.row{display:flex;align-items:center;gap:12px;min-height:44px;padding:4px 2px}
.row .ic{color:var(--d)}
.row .rx{flex:1;min-width:0}
.row .nm{font-size:14.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row .sv{font-size:12.5px;font-weight:600;color:var(--d)}
.row.act{margin:0 -6px;padding:6px 8px;border-radius:16px;background:color-mix(in srgb,var(--alert) 14%,transparent)}
.row.act .ic,.row.act .sv{color:var(--alert)}
.row.act .nm{white-space:normal}
.row.warn .ic,.row.warn .sv{color:var(--solar)}
.badge{width:44px;height:44px;border-radius:13px;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:none;
  background:var(--tile);line-height:1}
.badge b{font-family:var(--f-num);font-weight:500;font-size:16px;letter-spacing:-.03em}
.badge span{font-size:9.5px;font-weight:800;letter-spacing:.08em;color:var(--d);margin-top:3px}
.badge.today{background:color-mix(in srgb,var(--solar) 20%,transparent);color:var(--solar)}
.empty{display:flex;align-items:center;gap:12px;color:var(--d);font-size:13.5px;font-weight:600;line-height:1.4;padding:6px 2px}

.evm{display:flex;align-items:flex-end;justify-content:space-between;gap:14px}
.evs{display:flex;gap:18px}
.evs div{display:flex;flex-direction:column;gap:3px}
.evs b{font-family:var(--f-num);font-weight:500;font-size:16px;letter-spacing:-.03em}
.seg{display:flex;gap:4px;padding:4px;border-radius:16px;background:var(--tile)}
.seg button{all:unset;cursor:pointer;flex:1;text-align:center;min-height:40px;display:grid;place-items:center;border-radius:12px;
  font-weight:700;font-size:14px;color:var(--d);padding:0 6px}
.seg button[aria-pressed="true"]{background:var(--acc);color:var(--ground)}

.thumb{position:relative;aspect-ratio:16/9;border-radius:20px;overflow:hidden;flex:none;max-width:100%;background:#1b1f1c;cursor:pointer}
.thumb img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.thumb .tl{position:absolute;top:10px;left:10px;background:rgba(0,0,0,.55);color:#ffffff}
.thumb.ring{box-shadow:0 0 0 2px var(--alert),0 0 30px -6px var(--alert)}
.thumb.ring .tl{background:var(--alert);color:#ffffff}
.thumb .play{position:absolute;left:50%;top:50%;width:54px;height:54px;margin:-27px 0 0 -27px;border-radius:50%;display:grid;place-items:center;background:rgba(0,0,0,.45);color:#ffffff}
.thumb .cap{position:absolute;left:12px;right:12px;bottom:10px;display:flex;justify-content:space-between;font-size:12.5px;font-weight:700;color:#ffffff;text-shadow:0 1px 4px rgba(0,0,0,.7)}
.thumb .none{position:absolute;inset:0;display:grid;place-items:center;padding-top:10px;color:#8d96a8;font-size:13px;font-weight:700}

.layer{position:absolute;inset:0;z-index:5;background:var(--scrim);display:grid;place-items:center}
.layer.anim{animation:fade .2s ease-out}
.layer.anim .sheet{animation:rise .25s ease-out}
.sheet{width:min(800px,90%);max-height:88%;overflow:auto;background:var(--sheet);border:1px solid var(--brd);border-radius:26px;
  padding:22px 24px 24px;box-shadow:0 30px 80px -20px rgba(0,0,0,.5);display:flex;flex-direction:column;gap:18px;user-select:text}
.sh{display:flex;align-items:flex-start;gap:14px}
.sh .ttl{font-family:var(--f-num);font-weight:600;font-size:21px;letter-spacing:-.02em}
.sh .sts{font-size:14px;font-weight:600;color:var(--d);margin-top:4px}
.close{all:unset;cursor:pointer;margin-left:auto;width:44px;height:44px;border-radius:14px;display:grid;place-items:center;background:var(--tile);flex:none}
.sec{display:flex;flex-direction:column;gap:10px}
.sgrid{display:grid;grid-template-columns:1fr 1fr;gap:18px 24px}
.sw{all:unset;cursor:pointer;width:54px;height:32px;border-radius:999px;background:color-mix(in srgb,var(--d) 25%,transparent);position:relative;flex:none;transition:background .2s}
.sw::after{content:"";position:absolute;top:3px;left:3px;width:26px;height:26px;border-radius:50%;background:var(--t);transition:transform .2s}
.sw[aria-pressed="true"]{background:var(--c,var(--acc))}
.sw[aria-pressed="true"]::after{transform:translateX(22px);background:var(--ground)}
.btn{all:unset;cursor:pointer;box-sizing:border-box;min-height:48px;padding:0 18px;border-radius:15px;display:inline-flex;align-items:center;justify-content:center;gap:8px;
  font-weight:700;font-size:15px;background:var(--tile);border:1px solid var(--tile-brd);white-space:nowrap}
.btn.pri{background:var(--c,var(--acc));color:var(--ground);border-color:transparent}
.btn.armed{background:var(--alert);color:var(--ground)}
.btn[disabled]{opacity:.4;cursor:default}
.btns{display:flex;gap:10px;flex-wrap:wrap}
.kv{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.kv div{padding:12px;border-radius:16px;background:var(--tile);min-width:0}
.kv b{display:block;font-family:var(--f-num);font-weight:500;font-size:19px;letter-spacing:-.03em;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.week{display:grid;grid-template-columns:40px 1fr;gap:6px 10px;align-items:center;font-size:12px;font-weight:700;color:var(--d)}
.week .wb{position:relative;height:12px;border-radius:999px;background:color-mix(in srgb,var(--grid) 18%,transparent);overflow:hidden}
.week .wb i{position:absolute;top:0;bottom:0;background:color-mix(in srgb,var(--ev) 60%,transparent)}
.fcl .row{border-bottom:1px solid var(--brd)}
.fcl .row .nm{white-space:normal}
.hrs{display:flex;align-items:flex-end;gap:3px;height:110px}
.hrs i{flex:1;border-radius:4px 4px 1px 1px;background:color-mix(in srgb,var(--grid) 45%,transparent);min-height:2px}
.hrs i.pk{background:var(--solar)}
.hrsx{display:flex;justify-content:space-between;font-size:11px;font-weight:700;color:var(--d)}
.saver{position:absolute;inset:0;z-index:8;background:var(--saver);cursor:pointer;display:grid;place-items:center}
.saver .inner{display:flex;flex-direction:column;align-items:center;gap:10px;color:var(--saver-t);animation:drift 50s ease-in-out infinite alternate}
.saver .big{font-family:var(--f-num);font-weight:500;font-size:150px;letter-spacing:-.06em;line-height:1}
.saver .sm{font-size:16px;font-weight:700}
@keyframes drift{0%{transform:translate(-30px,-18px)}100%{transform:translate(30px,22px)}}
@keyframes fade{from{opacity:0}}
@keyframes rise{from{transform:translateY(16px);opacity:0}}
@media (prefers-reduced-motion:reduce){.flow .dots,.saver .inner,.layer.anim,.layer.anim .sheet{animation:none}}

@container scr (min-width: 701px) and (max-width: 1100px){
  .wrap{padding-left:max(12px,env(safe-area-inset-left,0px));padding-right:max(12px,env(safe-area-inset-right,0px))}
  .body,.col{gap:10px}
  .body{grid-template-columns:1.05fr 1fr 1fr}
  .card{padding:13px 12px 14px;gap:10px}
  .top{gap:14px}
  .tile{gap:8px;padding:8px 9px;min-height:58px}
  .tile .bub{width:30px;height:30px;border-radius:10px}
  .tile .bub .ic{width:19px;height:19px}
  .tile .nm{font-size:13.5px}
  .tile .sv{font-size:12px}
  .room .ri{padding:9px 10px}
  .room .rn{font-size:13px}
  .room .rv{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .room .ic{width:19px;height:19px}
  .hero{font-size:38px}
  .wnow .hero{font-size:40px}
  .clock{font-size:36px}
}
/* Room tiles share whatever height the screen leaves (the Android app's system bars take ~90px), so each
   tile tightens itself: value and status on one line when short, a single name + value line when very short. */
@container room (max-height: 74px){
  .room .ri{padding:6px 10px;gap:2px}
  .room .rt .ic{width:16px;height:16px}
  .room .rb{display:flex;align-items:baseline;gap:6px}
  .room .rv{flex:0 1 auto;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .room .rs{flex:1 1 0;min-width:0}
}
@container room (max-height: 48px){
  .room .ri{flex-direction:row;align-items:center;justify-content:flex-start;gap:8px}
  .room .rt{flex:1;min-width:0}
  .room .rt .ic,.room .rb .rs{display:none}
  .room .rn{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
}
@container scr (max-width: 700px){
  .screen{overflow-y:auto;overscroll-behavior:contain}
  .wrap{height:auto;min-height:100%;padding:max(14px,env(safe-area-inset-top,0px)) max(12px,env(safe-area-inset-right,0px)) 28px max(12px,env(safe-area-inset-left,0px))}
  .top{grid-template-columns:1fr auto auto;grid-template-areas:"greet greet clock" "people wx theme" "status status status";gap:12px;padding:0 4px 4px}
  .people{justify-self:start}
  .status{justify-self:stretch}
  .clock{font-size:36px}
  .body{display:flex;flex-direction:column}
  .col{display:contents}
  .c-safety{order:1}.c-actions{order:2}.c-weather{order:3}.c-energy{order:4}.c-rooms{order:5}.c-ev{order:6}.c-cal{order:7}
  .card.grow{flex:none}
  .rooms{grid-auto-rows:auto}
  .room{min-height:104px}
  .tile{gap:9px;padding:10px}
  .tile .bub{width:34px;height:34px}
  .layer{place-items:stretch}
  .sheet{width:auto;max-height:none;border-radius:0;border:0;padding:max(52px,env(safe-area-inset-top,0px)) 18px 30px}
  .sgrid,.kv{grid-template-columns:1fr 1fr}
  .sgrid.one{grid-template-columns:1fr}
  .saver .big{font-size:86px}
}`;

class HomePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.ui = { sheet: null, shown: null, armed: null, lastTouch: Date.now(), wakeUntil: 0, fc: null, cal: [], calAt: 0, hours: null, hoursAt: 0, pend: {} };
    this._sig = '';
    this._holding = false;
    this._pending = false;
    try { this.ui.theme = JSON.parse(localStorage.getItem('home-panel-theme') || 'null'); } catch (e) { this.ui.theme = null; }
    try { this.ui.fanUntil = +localStorage.getItem('home-panel-fan-until') || 0; } catch (e) { this.ui.fanUntil = 0; }
    this._upgradeProps();
  }

  // HA can set hass/panel/narrow on the element before this module defines it. Those become own
  // properties that hide the class setters, so re-apply them through the setters.
  _upgradeProps() {
    for (const k of ['panel', 'narrow', 'route', 'hass']) {
      if (Object.prototype.hasOwnProperty.call(this, k)) { const v = this[k]; delete this[k]; this[k] = v; }
    }
  }

  set hass(h) { const first = !this._hass; this._hass = h; if (first) this._start(); this._schedule(); }
  get hass() { return this._hass; }
  set panel(p) { this._panel = p; this.cfg = (p && p.config) || {}; this._ids = null; this._schedule(true); }
  set narrow(n) { this._narrow = n; this._schedule(true); }
  get narrow() { return this._narrow; }
  get panel() { return this._panel; }
  set route(r) { this._route = r; }
  get route() { return this._route; }

  connectedCallback() {
    this._upgradeProps();
    if (!document.querySelector(`link[href="${FONT_HREF}"]`)) {
      const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = FONT_HREF; document.head.appendChild(l);
    }
    const r = this.shadowRoot;
    if (!r.querySelector('style')) {
      r.innerHTML = `<style>${CSS}</style><div class="root" id="root"><div class="screen" id="screen"></div><div id="layer"></div></div>`;
      r.addEventListener('click', (e) => this._click(e));
      r.addEventListener('pointerdown', () => { this._holding = true; this.ui.lastTouch = Date.now(); });
      const up = () => { this._holding = false; if (this._pending) { this._pending = false; this._schedule(true); } };
      r.addEventListener('pointerup', up); r.addEventListener('pointercancel', up);
    }
    this._tick = setInterval(() => this._schedule(true), 20000);
    if (this._hass) this._start();
    this._schedule(true);
  }
  disconnectedCallback() {
    clearInterval(this._tick);
    if (this._fcUnsub) { this._fcUnsub.then((u) => u && u()).catch(() => {}); this._fcUnsub = null; }
    this._started = false;
  }

  // ---------- data helpers ----------
  s(id) { return id && this._hass ? this._hass.states[id] : undefined; }
  v(id) { const x = this.s(id); return x ? x.state : undefined; }
  n(id) { const x = parseFloat(this.v(id)); return isNaN(x) ? null : x; }
  on(id) { return this.v(id) === 'on'; }
  t(id) { const x = this.v(id); const d = x ? new Date(x) : null; return d && !isNaN(d) ? d : null; }
  ok(id) { const x = this.v(id); return x !== undefined && x !== 'unavailable'; }
  call(domain, service, data) { return this._hass.callService(domain, service, data).catch((e) => console.warn('home-panel', domain, service, e)); }

  _start() {
    if (this._started || !this._hass || !this.isConnected) return;
    this._started = true;
    const w = (this.cfg.weather || {}).forecast;
    if (w && this._hass.connection) {
      this._fcUnsub = this._hass.connection.subscribeMessage((m) => { this.ui.fc = m.forecast || []; this._schedule(true); },
        { type: 'weather/subscribe_forecast', forecast_type: (this.cfg.weather || {}).forecast_type || 'twice_daily', entity_id: w });
      this._fcUnsub.catch((e) => console.warn('home-panel forecast', e));
    }
  }

  _allIds() {
    if (this._ids) return this._ids;
    const out = new Set();
    const walk = (x) => {
      if (typeof x === 'string') { if (/^[a-z_]+\.[a-z0-9_]+$/.test(x)) out.add(x); }
      else if (Array.isArray(x)) x.forEach(walk);
      else if (x && typeof x === 'object') Object.values(x).forEach(walk);
    };
    walk(this.cfg);
    this._ids = [...out];
    return this._ids;
  }

  _schedule(force) {
    if (force) this._force = true;
    if (this._raf) return;
    // requestAnimationFrame can stall in a hidden or throttled WebView, so a timer backs it up.
    const run = () => {
      if (!this._raf) return;
      cancelAnimationFrame(this._raf); clearTimeout(this._rafT); this._raf = 0;
      this._render();
    };
    this._raf = requestAnimationFrame(run);
    this._rafT = setTimeout(run, 300);
  }

  // ---------- derived state ----------
  mode() {
    const sunUp = this.v(this.cfg.sun || 'sun.sun') === 'above_horizon';
    const auto = sunUp ? 'light' : 'dark';
    const o = this.ui.theme;
    if (o && o.sunUp === sunUp) return o.mode;
    if (o) { this.ui.theme = null; try { localStorage.removeItem('home-panel-theme'); } catch (e) { /* ignore */ } }
    return auto;
  }
  ev() {
    const c = this.cfg.ev || {};
    if (!c.power) return null;
    const kw = this.n(c.power) || 0;
    const state = (this.v(c.state) || '').toLowerCase();
    const cable = (this.v(c.cable) || '').toLowerCase();
    const charging = kw > 0.05 || (state.startsWith('charging'));
    const plugged = charging || (cable && !cable.startsWith('unplug'));
    return { c, kw, charging, plugged, avail: this.ok(c.power), energy: this.n(c.energy), miles: this.n(c.miles), amps: this.v(c.amps) };
  }
  workshop() {
    const room = (this.cfg.rooms || []).find((r) => r.kind === 'workshop');
    if (!room) return null;
    const out = {};
    for (const o of room.outlets || []) out[o.key] = { ...o, on: this.on(o.switch), w: this.n(o.power), avail: this.ok(o.switch) };
    const laser = out[room.laser], ex = out[room.exhaust];
    const cutting = laser && laser.on && (laser.w ?? 0) >= (room.laser_threshold_w ?? 15);
    const clearing = room.end_script && this.on(room.end_script);
    return { room, out, laser, ex, cutting, warn: !!(cutting && ex && !ex.on), clearing };
  }
  doorbell() {
    const c = this.cfg.front_door || {};
    const ding = this.t(c.ding), now = Date.now();
    return { c, ding, ringing: !!(ding && now - ding < (c.ring_alert_seconds ?? 180) * 1000), motion: this.t(c.motion), activity: this.t(c.activity) };
  }
  offline() {
    const h = this.cfg.health || {};
    const bad = [];
    for (const id of h.connectivity || []) if (this.v(id) !== 'on') bad.push(id);
    for (const id of h.available || []) if (!this.ok(id)) bad.push(id);
    return { bad, total: (h.connectivity || []).length + (h.available || []).length };
  }
  nas() {
    const h = this.cfg.health || {};
    const okStates = h.nas_ok_states || ['normal', 'background_scrubbing'];
    const bad = (h.nas || []).filter((id) => !okStates.includes(this.v(id)));
    return { bad, security: h.nas_security ? this.on(h.nas_security) : false, backup: this.t(h.backup) };
  }
  raining() {
    const w = this.cfg.weather || {};
    return (this.n(w.rain_rate) || 0) > 0 || ['rainy', 'pouring', 'lightning-rainy'].includes(this.v(w.forecast));
  }
  status() {
    const db = this.doorbell(), ws = this.workshop(), ev = this.ev(), T = tou(new Date(), this.cfg.tou);
    if (db.ringing) return { c: 'alert', t: `Doorbell rang at ${fmtTime(db.ding)}`, open: 'safety' };
    if (ws && ws.warn) return { c: 'alert', t: 'Laser running with the exhaust off', open: 'room:workshop' };
    if (ev && ev.charging && T.peak) return { c: 'alert', t: 'EV charging at peak price', open: 'ev' };
    const off = this.offline();
    if (off.bad.length) return { c: 'solar', t: `${off.bad.length} device${off.bad.length > 1 ? 's' : ''} offline`, open: 'safety' };
    if (T.peak) return { c: 'solar', t: `Peak price ${T.next}${ev && ev.plugged ? ' · EV waits' : ''}`, open: 'energy' };
    if (ev && ev.charging) return { c: 'ev', t: `EV charging · ${ev.kw.toFixed(1)} kW`, open: 'ev' };
    return { c: 'ok', t: 'All systems normal', calm: true, open: 'safety' };
  }
  mood(st) {
    if (st.c === 'alert') return 'var(--alert)';
    if (this.raining()) return 'var(--grid)';
    const w = this.cfg.weather || {};
    if (this.v(this.cfg.sun || 'sun.sun') === 'above_horizon' && (this.n(w.solar) ?? 0) > 250) return 'var(--solar)';
    return 'transparent';
  }
  saverOn() {
    const sv = this.cfg.saver || {};
    if (sv.enabled === false) return false;
    const root = this.shadowRoot.getElementById('root');
    if (root && root.clientWidth <= 700) return false;
    const now = new Date(), m = now.getHours() * 60 + now.getMinutes();
    const p = (s, d) => { const [h, mm] = String(s || d).split(':').map(Number); return h * 60 + (mm || 0); };
    const a = p(sv.start, '02:00'), b = p(sv.end, '06:00');
    const inWin = a < b ? m >= a && m < b : m >= a || m < b;
    const idle = Date.now() - this.ui.lastTouch > (sv.idle_seconds ?? 120) * 1000;
    return inWin && idle && !this.ui.sheet;
  }

  // ---------- render ----------
  _render() {
    if (!this._hass || !this.shadowRoot.getElementById('screen')) return;
    if (this._holding) { this._pending = true; return; }
    const sig = this._allIds().map((id) => { const x = this._hass.states[id]; return x ? x.last_updated : '-'; }).join('|')
      + JSON.stringify(this.ui.pend) + (this.ui.fc ? this.ui.fc.length : 0) + this.ui.calAt + this.ui.hoursAt;
    if (!this._force && sig === this._sig) return;
    this._force = false; this._sig = sig;
    this._maybeFetch();
    const root = this.shadowRoot.getElementById('root'), sc = this.shadowRoot.getElementById('screen'), L = this.shadowRoot.getElementById('layer');
    const st = this.status();
    root.dataset.mode = this.mode();
    root.style.setProperty('--mood', this.mood(st));
    const keep = sc.scrollTop;
    sc.innerHTML = `<div class="wrap">${this.header(st)}<div class="body">
      <div class="col">${this.safetyCard()}${this.evCard()}</div>
      <div class="col">${this.actionsCard()}${this.roomsCard()}</div>
      <div class="col">${this.weatherCard()}${this.energyCard()}${this.calendarCard()}</div></div></div>`;
    sc.scrollTop = keep;
    let html = '';
    if (this.saverOn()) {
      const T = tou(new Date(), this.cfg.tou), w = this.cfg.weather || {};
      html = `<div class="saver" data-act="wake"><div class="inner"><div class="big">${fmtTime(new Date()).replace(/\s?[AP]M$/i, '')}</div>
        <div class="sm">${this.n(w.temp) !== null ? Math.round(this.n(w.temp)) + '° · ' : ''}${T.peak ? 'peak price ' + T.next : T.next.startsWith('until') ? 'off-peak ' + T.next : 'off-peak · ' + T.next}</div></div></div>`;
    } else if (this.ui.sheet) {
      const x = this.sheet(this.ui.sheet), fresh = this.ui.sheet !== this.ui.shown;
      if (x) html = `<div class="layer ${fresh ? 'anim' : ''}" data-act="closebg"><div class="sheet" role="dialog" aria-label="${esc(x.t)}">
        <div class="sh"><div><div class="ttl">${esc(x.t)}</div><div class="sts">${x.s}</div></div><button class="close" data-act="close" aria-label="Close">${ic('x')}</button></div>${x.b}</div></div>`;
      else this.ui.sheet = null;
    }
    this.ui.shown = html.includes('class="sheet"') ? this.ui.sheet : null;
    const prev = L.querySelector('.sheet'), ss = prev ? prev.scrollTop : 0;
    L.innerHTML = html;
    const nsh = L.querySelector('.sheet'); if (nsh) nsh.scrollTop = ss;
  }

  _maybeFetch() {
    const now = Date.now();
    const cals = this.cfg.calendars || [];
    if (cals.length && now - this.ui.calAt > 15 * 60e3 && !this._calBusy) {
      this._calBusy = true;
      const start = new Date(); start.setHours(0, 0, 0, 0);
      const end = new Date(start); end.setDate(end.getDate() + 8);
      Promise.all(cals.map((c) => this._hass.callApi('GET', `calendars/${c.entity || c}?start=${encodeURIComponent(start.toISOString())}&end=${encodeURIComponent(end.toISOString())}`)
        .then((evs) => evs.map((e) => ({ ...e, cal: c.name || '' }))).catch(() => [])))
        .then((lists) => {
          const all = lists.flat().map((e) => ({ ...e, _s: new Date(e.start.dateTime || e.start.date + 'T00:00:00'), allDay: !e.start.dateTime }));
          all.sort((a, b) => a._s - b._s);
          this.ui.cal = all; this.ui.calAt = Date.now(); this._calBusy = false; this._schedule(true);
        });
    }
  }
  _fetchHours() {
    const stat = (this.cfg.energy || {}).hourly_statistic;
    if (!stat || this._hoursBusy || Date.now() - this.ui.hoursAt < 60 * 60e3) return;
    this._hoursBusy = true;
    const start = new Date(Date.now() - 4 * 864e5);
    this._hass.callWS({ type: 'recorder/statistics_during_period', start_time: start.toISOString(), statistic_ids: [stat], period: 'hour', types: ['change'] })
      .then((r) => {
        const rows = (r[stat] || []).map((x) => ({ d: new Date(x.start), v: Math.max(0, x.change || 0) }));
        const byDay = {};
        for (const x of rows) (byDay[x.d.toDateString()] ||= Array(24).fill(null))[x.d.getHours()] = x.v;
        const days = Object.keys(byDay).filter((k) => byDay[k].filter((v) => v !== null).length >= 20).sort((a, b) => new Date(a) - new Date(b));
        const k = days[days.length - 1];
        this.ui.hours = k ? { day: new Date(k), vals: byDay[k].map((v) => v || 0) } : null;
        this.ui.hoursAt = Date.now(); this._hoursBusy = false; this._schedule(true);
      }).catch(() => { this._hoursBusy = false; this.ui.hoursAt = Date.now(); });
  }

  // ---------- header ----------
  header(st) {
    const now = new Date(), h = now.getHours(), w = this.cfg.weather || {};
    const greet = h < 5 ? 'Good night' : h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : h < 22 ? 'Good evening' : 'Good night';
    const people = (this.cfg.people || []).map((p) => {
      const home = this.v(p.entity) === 'home';
      return `<div class="pp ${home ? '' : 'away'}" style="--c:var(--${p.color || 'acc'})" title="${esc(p.name || p.initials)} · ${home ? 'home' : 'away'}">${esc(p.initials || '?')}</div>`;
    }).join('');
    const showMenu = this._narrow || (this._hass && this._hass.dockedSidebar === 'always_hidden');
    const t = this.n(w.temp);
    const time = fmtTime(now), ap = (time.match(/[AP]M$/i) || [''])[0];
    return `<header class="top">
      <div class="greet">${showMenu ? `<button class="iconbtn" data-act="menu" aria-label="Open the sidebar">${ic('menu')}</button>` : ''}
        <div><div class="hi">${greet}</div><div class="date">${now.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' })}</div></div></div>
      <div class="people">${people}</div>
      <button class="status ${st.calm ? 'calm' : ''}" style="--c:var(--${st.c})" data-open="${st.open}"><span class="dot"></span>${esc(st.t)}</button>
      <div class="wxmini">${wx(WX_KIND[this.v(w.forecast)] || 'cloud', 28)}${t !== null ? Math.round(t) + '°' : ''}</div>
      <button class="iconbtn themebtn" data-act="theme" aria-label="Switch between light and dark">${ic('theme')}</button>
      <div class="clock">${time.replace(/\s?[AP]M$/i, '')}<small>${ap}</small></div>
    </header>`;
  }

  // ---------- cards ----------
  safetyCard() {
    const db = this.doorbell(), off = this.offline(), nas = this.nas();
    const last = db.activity || db.motion;
    const healthOk = !off.bad.length && !nas.bad.length;
    return `<section class="card c-safety grow" data-open="safety"><div class="card-h"><h2 class="ct">Front door</h2><span class="st">${db.ringing ? '<span class="chip" style="--c:var(--alert)">Act now</span>' : 'All quiet'}</span></div>
      ${this.thumb(db)}
      <div class="rows">
        <div class="row ${db.ringing ? 'act' : ''}">${ic('bell')}<div class="rx"><div class="nm">${db.ringing ? 'Someone is at the door' : 'Doorbell'}</div><div class="sv">${db.ding ? (db.ringing ? 'Rang at ' : 'Last ring ') + relTime(db.ding) : 'No rings yet'}</div></div>${db.ringing ? '<span class="chip" style="--c:var(--alert)">View</span>' : ''}</div>
        <div class="row">${ic('door')}<div class="rx"><div class="nm">Activity</div><div class="sv">${last ? 'Last at ' + relTime(last) : 'Nothing recorded'}</div></div></div>
        <div class="row ${healthOk ? '' : 'warn'}">${ic('shield')}<div class="rx"><div class="nm">${off.bad.length ? `${off.bad.length} of ${off.total} devices offline` : `All ${off.total} devices online`}</div>
          <div class="sv">${nas.bad.length ? 'NAS needs a look' : 'Home Assistant &amp; NAS healthy'}</div></div><span class="dot" style="--c:var(--${healthOk ? 'ok' : 'solar'})"></span></div>
      </div></section>`;
  }
  thumb(db, big) {
    const cam = this.s(db.c.camera);
    const pic = cam && cam.attributes.entity_picture;
    const when = db.activity || db.motion;
    return `<div class="thumb ${db.ringing ? 'ring' : ''}" data-act="live" ${big ? 'style="max-height:420px"' : ''}>
      ${pic ? `<img src="${esc(pic)}" alt="Front door, last recording">` : '<div class="none">No recording yet</div>'}
      <span class="chip tl">${db.ringing ? 'Ringing now' : 'Last recording'}</span>${pic ? `<span class="play">${ic('play')}</span>` : ''}
      <span class="cap"><span>${db.ringing ? 'Doorbell · ' + fmtTime(db.ding) : when ? relTime(when) : ''}</span><span>Live view</span></span></div>`;
  }
  evCard() {
    const ev = this.ev();
    if (!ev) return '';
    const T = tou(new Date(), this.cfg.tou);
    const status = !ev.avail ? 'Offline' : ev.charging ? (T.peak ? 'Charging at peak price' : `Charging · ${ev.kw.toFixed(1)} kW`)
      : ev.plugged ? (T.peak ? `Plugged in · waits ${T.next.replace('until ', 'for ')}` : 'Plugged in') : 'Unplugged';
    return `<section class="card c-ev" data-open="ev"><div class="card-h"><h2 class="ct">EV charger</h2><span class="st">${esc(status)}</span></div>
      <div class="evm"><div class="hero" style="color:${ev.charging ? 'var(--ev)' : 'var(--t)'}">${ev.kw.toFixed(1)}<small>kW</small></div>
        <div class="evs"><div><span class="lbl">${ev.charging ? 'Session' : 'Last session'}</span><b>${ev.energy !== null ? ev.energy.toFixed(1) : '—'} kWh</b></div>
        <div><span class="lbl">Range</span><b>${ev.miles !== null ? '+' + Math.round(ev.miles) : '—'} mi</b></div></div></div>
      ${this.ampSeg(ev)}</section>`;
  }
  ampSeg(ev) {
    const choices = ev.c.amp_choices || [16, 24, 32, 40];
    const cur = this.ui.pend.amps ?? ev.amps;
    return `<div class="seg" role="group" aria-label="Charging current">${choices.map((a) => `<button type="button" aria-pressed="${String(a) === String(cur)}" data-act="amps:${a}">${a} A</button>`).join('')}</div>`;
  }
  tileState(a) {
    const ids = a.entities || (a.entity ? [a.entity] : []);
    if (a.kind === 'ev') {
      const ev = this.ev();
      if (!ev) return { on: false, sv: 'Not set up', na: true };
      const T = tou(new Date(), this.cfg.tou);
      return { on: ev.charging, sv: ev.charging ? `${ev.kw.toFixed(1)} kW` : !ev.plugged ? 'Unplugged' : T.peak ? `Waits ${T.next.replace('until ', 'for ')}` : 'Plugged in', na: !ev.avail };
    }
    const avail = ids.some((id) => this.ok(id));
    const anyOn = ids.some((id) => this.on(id));
    if (a.kind === 'mute') return { on: !anyOn && avail, sv: !avail ? 'Unavailable' : anyOn ? 'On' : 'Muted', na: !avail };
    if (a.kind === 'zone') {
      // last_changed also resets when HA restarts, so it can't say when the zone last ran
      return { on: anyOn, sv: !avail ? 'Unavailable' : anyOn ? 'Running' : 'Ready', na: !avail };
    }
    const label = anyOn ? (a.on_label || 'On') : (a.off_label || 'Off');
    return { on: anyOn, sv: !avail ? 'Unavailable' : label, na: !avail };
  }
  actionsCard() {
    const acts = this.cfg.actions || [];
    const onCount = acts.filter((a) => this.tileState(a).on).length;
    return `<section class="card c-actions" data-open="none"><div class="card-h"><h2 class="ct">Quick actions</h2><span class="st">${onCount} on</span></div>
      <div class="qa">${acts.map((a, i) => {
        const s = this.tileState(a), armed = this.ui.armed === 'qa' + i;
        const msg = armed ? (a.kind === 'ev' ? (tou(new Date(), this.cfg.tou).peak ? 'Peak price · tap again' : 'Tap again to start') : 'Tap again to switch off') : s.sv;
        return `<button class="tile ${s.on ? 'on' : ''} ${armed ? 'armed' : ''} ${s.na ? 'na' : ''}" style="--c:var(--${a.color || 'acc'})" data-qa="${i}">
          <span class="bub">${ic(a.icon)}</span><span class="tx"><div class="nm">${esc(a.name)}</div><div class="sv">${esc(msg)}</div></span></button>`;
      }).join('')}</div></section>`;
  }

  roomInfo(r) {
    if (r.kind === 'climate') {
      const c = this.s(r.climate); if (!c) return { v: '—', s: 'Unavailable' };
      const a = c.attributes, act = a.hvac_action, cur = a.current_temperature;
      const eco = a.preset_mode === 'eco';
      const target = c.state === 'heat_cool' ? `${a.target_temp_low}–${a.target_temp_high}°` : a.temperature != null ? `to ${a.temperature}°` : '';
      const actTxt = c.state === 'off' ? 'Off' : act === 'heating' ? 'Heating' : act === 'cooling' ? 'Cooling' : eco ? 'Eco' : 'Idle';
      const fan = a.fan_mode === 'on' ? 'fan on' : '';
      return { v: cur != null ? `${Math.round(cur * 10) / 10}°` : '—', s: [actTxt + (target && c.state !== 'off' && !eco ? ' · ' + target : ''), fan].filter(Boolean).join(' · '),
        c: act === 'heating' ? 'heat' : act === 'cooling' ? 'home' : a.fan_mode === 'on' ? 'acc' : null };
    }
    if (r.kind === 'appliance') {
      const op = this.v(r.state), fin = this.t(r.finish);
      const map = { ready: 'Ready', inactive: 'Off', run: 'Running', pause: 'Paused', delayedstart: 'Starts later', finished: 'Done', actionrequired: 'Needs you', error: 'Error', aborting: 'Stopping' };
      return { v: map[op] || (op === 'unavailable' || op === undefined ? 'Offline' : op), s: op === 'run' && fin ? `${r.appliance || 'Program'} done ${fmtTime(fin)}` : op === 'finished' ? `${r.appliance || 'Program'} finished` : r.appliance || '',
        c: op === 'run' ? 'home' : op === 'finished' ? 'ok' : ['error', 'actionrequired'].includes(op) ? 'alert' : null };
    }
    if (r.kind === 'switches') {
      const on = (r.switches || []).filter((x) => this.on(x.entity));
      const first = (r.switches || [])[0];
      return { v: on.length ? (on.length === 1 ? on[0].name : `${on.length} on`) : 'All off', s: (r.switches || []).filter((x) => !this.on(x.entity)).map((x) => x.name + ' off').join(' · ') || 'Everything on',
        c: on.length ? (on[0].color || (first && first.color) || 'ok') : null };
    }
    if (r.kind === 'workshop') {
      const w = this.workshop(); const any = Object.values(w.out).some((o) => o.on);
      const lw = w.laser && w.laser.w;
      return { v: w.cutting ? 'Laser on' : w.clearing ? 'Clearing air' : any ? 'Powered' : 'Off',
        s: w.warn ? 'Exhaust is off' : w.cutting ? `${w.laser.name} · ${Math.round(lw)} W` : any ? Object.values(w.out).filter((o) => o.on).map((o) => o.short || o.name).join(', ') : `${w.laser ? w.laser.name : 'Laser'} & exhaust`,
        c: w.warn ? 'alert' : w.cutting || w.clearing ? 'heat' : null };
    }
    if (r.kind === 'yard') {
      const y = (this.cfg.yard || [])[r.yard ?? 0] || {};
      const watering = (y.zones || []).filter((z) => this.on(z.entity));
      const lights = (r.extra || []).filter((x) => this.on(x.entity));
      const v = watering.length ? 'Watering' : lights.length ? lights[0].name.replace(/ lights?$/i, '') + ' on' : this.on(y.rain_delay) ? 'Rain delay' : this.on(y.standby) ? 'Standby' : 'Quiet';
      const s = watering.length ? watering.map((z) => z.name).join(', ') : this.on(y.standby) ? 'Schedules paused' : this.on(y.rain_delay) ? 'Watering paused' : 'Zones idle';
      return { v, s, c: watering.length ? 'home' : lights.length ? 'solar' : null };
    }
    return { v: '', s: '' };
  }
  roomsCard() {
    const rooms = this.cfg.rooms || [];
    return `<section class="card c-rooms grow" data-open="none"><div class="card-h"><h2 class="ct">Rooms</h2><span class="st">${rooms.length} rooms</span></div>
      <div class="rooms">${rooms.map((r, i) => {
        const x = this.roomInfo(r);
        return `<button class="room ${x.c ? 'on' : ''}" style="--c:var(--${x.c || 'd'})" data-open="room:${i}">
          <span class="ri"><span class="rt"><span class="rn">${esc(r.name)}</span>${ic(r.icon)}</span><span class="rb"><span class="rv">${esc(x.v)}</span><span class="rs">${esc(x.s)}</span></span></span></button>`;
      }).join('')}</div></section>`;
  }
  fcLabel(f) {
    const d = new Date(f.datetime), now = new Date();
    const day = sameDay(d, now) ? (f.is_daytime === false ? 'Tonight' : 'Today') : d.toLocaleDateString([], { weekday: 'short' });
    return f.is_daytime === false && day !== 'Tonight' ? day + ' night' : day;
  }
  weatherCard() {
    const w = this.cfg.weather || {}, cond = this.v(w.forecast);
    const t = this.n(w.temp), feels = this.n(w.feels), wind = this.n(w.wind), rd = this.n(w.rain_today), uv = this.n(w.uv);
    const fc = (this.ui.fc || []).slice(0, 4);
    const yards = this.cfg.yard || [];
    const zonesOn = yards.flatMap((y) => (y.zones || []).filter((z) => this.on(z.entity)).map((z) => z.name));
    const delay = yards.filter((y) => this.on(y.rain_delay)).map((y) => y.name);
    const standby = yards.filter((y) => this.on(y.standby)).map((y) => y.name);
    const yt = zonesOn.length ? `Watering: ${zonesOn.join(', ')}` : delay.length ? `Rain delay: ${delay.join(' & ')}` : 'Irrigation on schedule';
    const ys = standby.length ? `${standby.join(' & ')} on standby` : this.raining() ? 'Raining now' : `${yards.length} controllers ready`;
    return `<section class="card c-weather grow" data-open="weather">
      <div class="card-h"><h2 class="ct">Weather &amp; yard</h2><span class="st">${this.raining() ? '<span class="chip" style="--c:var(--home)">Raining</span>' : 'NWS forecast'}</span></div>
      <div class="wnow">${wx(WX_KIND[cond] || 'cloud', 52)}<div class="hero">${t !== null ? Math.round(t) + '°' : '—'}</div>
        <div class="wdet"><b>${esc(WX_LABEL[cond] || '')}</b>${feels !== null ? ` · feels ${Math.round(feels)}°` : ''}<br>${wind !== null ? `Wind ${Math.round(wind)} mph · ` : ''}${rd ? `rain today ${rd.toFixed(2)} in` : uv !== null ? `UV ${uv}` : ''}</div></div>
      <div class="fc">${fc.length ? fc.map((f) => `<div><span class="n">${esc(this.fcLabel(f))}</span>${wx(f.is_daytime === false && WX_KIND[f.condition] === 'pcloudy' ? 'ncloudy' : (WX_KIND[f.condition] || 'cloud'), 26)}<span class="t">${Math.round(f.temperature)}°</span><span class="p">${f.precipitation_probability ? f.precipitation_probability + '%' : '&nbsp;'}</span></div>`).join('')
        : '<div style="grid-column:1/-1"><span class="n">Loading forecast…</span></div>'}</div>
      ${yards.length ? `<button class="yard" data-open="yard"><span class="bub">${ic('sprinkler')}</span><span class="yt"><div class="nm">${esc(yt)}</div><div class="sub">${esc(ys)}</div></span>${ic('chev')}</button>` : ''}
    </section>`;
  }
  touBar(big, mini) {
    const T = tou(new Date(), this.cfg.tou);
    const segs = T.off ? [[24, '']] : [[T.ps, ''], [T.pe - T.ps, 'pk'], [24 - T.pe, '']];
    return `<div class="tou-wrap"><div class="tou-bar" ${big ? 'style="height:22px"' : ''}>${segs.map(([w, c]) => `<span class="${c}" style="width:${w / 24 * 100}%"></span>`).join('')}</div>
      <div class="now" style="left:${T.h / 24 * 100}%;${big ? 'height:30px' : ''}"></div></div>
      ${mini ? '' : `<div class="ticks"><span style="left:0">12 AM</span><span style="left:25%">6 AM</span><span style="left:50%">12 PM</span>${T.off ? '' : `<span style="left:${T.ps / 24 * 100}%">${T.ps % 12 || 12}</span><span style="left:${T.pe / 24 * 100}%">${fmtHour(T.pe)}</span>`}<span style="left:100%">12 AM</span></div>`}`;
  }
  bill() {
    const e = this.cfg.energy || {};
    const g = (k) => this.n(e[k]);
    const el = g('elec_to_date'), gas = g('gas_to_date'), fEl = g('elec_forecast'), fGas = g('gas_forecast'), tEl = g('elec_typical'), tGas = g('gas_typical');
    const sum = (...xs) => (xs.some((x) => x === null) ? null : xs.reduce((a, b) => a + b, 0));
    return { el, gas, fEl, fGas, tot: sum(el, gas ?? 0), fc: sum(fEl, fGas ?? 0), typ: sum(tEl, tGas ?? 0) };
  }
  energyCard() {
    const T = tou(new Date(), this.cfg.tou), b = this.bill();
    return `<section class="card c-energy" data-open="energy">
      <div class="card-h"><h2 class="ct">Energy</h2>${T.peak ? `<span class="chip" style="--c:var(--solar)">Peak ${esc(T.next)}</span>` : `<span class="chip" style="--c:var(--ok)">Off-peak${T.off ? ' all day' : ''}</span>`}</div>
      ${this.touBar(false, true)}
      <div class="eline"><span class="num" style="font-size:24px">${b.tot !== null ? '$' + Math.round(b.tot) : '—'}</span><span class="sub">bill so far${b.fc !== null ? ' · forecast $' + Math.round(b.fc) : ''}</span>${ic('chev')}</div>
    </section>`;
  }
  calendarCard() {
    const cals = this.cfg.calendars || [];
    if (!cals.length) {
      return `<section class="card c-cal" data-open="none"><div class="card-h"><h2 class="ct">Calendar</h2><span class="st">Not linked</span></div>
        <div class="empty">${ic('cal')}<span>Link Google Calendar in Home Assistant, then add it to this panel's settings.</span></div></section>`;
    }
    const evs = this.ui.cal.filter((e) => (e.end && new Date(e.end.dateTime || e.end.date) > new Date()) || e._s > new Date());
    return `<section class="card c-cal" data-open="calendar"><div class="card-h"><h2 class="ct">Calendar</h2><span class="st">Next 7 days</span></div>
      <div class="rows">${evs.length ? evs.slice(0, 3).map((e) => this.calRow(e)).join('') : '<div class="empty">Nothing scheduled this week.</div>'}</div></section>`;
  }
  calRow(e) {
    const d = e._s, today = sameDay(d, new Date());
    return `<div class="row"><div class="badge ${today ? 'today' : ''}"><b>${d.getDate()}</b><span>${d.toLocaleDateString([], { month: 'short' }).toUpperCase()}</span></div>
      <div class="rx"><div class="nm">${esc(e.summary)}</div><div class="sv">${today ? 'Today' : d.toLocaleDateString([], { weekday: 'short' })}${e.allDay ? '' : ' · ' + fmtTime(d)}${e.cal ? ' · ' + esc(e.cal) : ''}</div></div></div>`;
  }

  // ---------- sheets ----------
  row(i, nm, sv, ctrl = '', cls = '') { return `<div class="row ${cls}">${ic(i)}<div class="rx"><div class="nm">${nm}</div><div class="sv">${sv}</div></div>${ctrl}</div>`; }
  sw(act, on, c, na) { return `<button class="sw" style="--c:var(--${c})" aria-pressed="${on}" data-act="${act}" aria-label="Toggle" ${na ? 'disabled' : ''}></button>`; }

  sheet(k) {
    if (k === 'energy') return this.energySheet();
    if (k === 'ev') return this.evSheet();
    if (k === 'yard') return this.yardSheet();
    if (k === 'weather') return this.weatherSheet();
    if (k === 'safety') return this.safetySheet();
    if (k === 'calendar') return { t: 'Calendar', s: 'Next 7 days', b: `<div class="rows">${this.ui.cal.map((e) => this.calRow(e)).join('') || '<div class="empty">Nothing scheduled.</div>'}</div>` };
    if (k === 'room:workshop') { const i = (this.cfg.rooms || []).findIndex((r) => r.kind === 'workshop'); return i >= 0 ? this.roomSheet(i) : null; }
    if (k.startsWith('room:')) return this.roomSheet(+k.slice(5));
    return null;
  }
  energySheet() {
    this._fetchHours();
    const T = tou(new Date(), this.cfg.tou), b = this.bill(), c = this.cfg.tou || {};
    const when = T.peak ? 'peak price ' + T.next : T.next.startsWith('until') ? 'off-peak ' + T.next : 'off-peak now · ' + T.next;
    const max = Math.max(b.fc || 0, b.typ || 0, b.tot || 0) * 1.06 || 1;
    const H = this.ui.hours;
    let hrs = '<div class="sub">Loading hourly use…</div>';
    if (H) {
      const hm = Math.max(...H.vals, 0.01), all = H.vals.reduce((a, v) => a + v, 0), pk = isOffDay(H.day) ? 0 : H.vals.slice(T.ps, T.pe).reduce((a, v) => a + v, 0);
      hrs = `<div class="hrs">${H.vals.map((v, i) => `<i class="${!isOffDay(H.day) && i >= T.ps && i < T.pe ? 'pk' : ''}" style="height:${v / hm * 100}%" title="${i}:00 · ${v.toFixed(2)} kWh"></i>`).join('')}</div>
        <div class="hrsx"><span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>11 PM</span></div>
        <div class="sub">${H.day.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })}: ${all.toFixed(1)} kWh${pk ? `, ${pk.toFixed(1)} kWh of it at peak` : ''}. Utility data arrives a day or two late, so there is no live whole-home reading.</div>`;
    } else if (this.ui.hoursAt) hrs = '<div class="sub">Hourly use is not available.</div>';
    const ev = this.ev();
    return { t: 'Energy', s: `${esc([c.utility, c.name].filter(Boolean).join(' ') || 'Time of use')} · ${when}`, b: `
      <div class="sec"><div class="lbl">Today's prices</div>${this.touBar(true)}<div class="sub">Peak is ${fmtHour(T.ps)}–${fmtHour(T.pe)} on weekdays. Weekends and holidays are off-peak all day.</div></div>
      ${ev ? `<div class="sec"><div class="lbl">Power right now</div>${this.flow(ev, T)}</div>` : ''}
      <div class="sec"><div class="bill"><div><div class="lbl">Bill so far</div><div class="hero" style="margin-top:6px">${b.tot !== null ? '$' + Math.round(b.tot) : '—'}</div></div>
        <div><div class="bbar"><div class="fill" style="width:${(b.tot || 0) / max * 100}%"></div>${b.fc ? `<div class="mk" style="left:${b.fc / max * 100}%"></div>` : ''}${b.typ ? `<div class="mk typ" style="left:${b.typ / max * 100}%"></div>` : ''}</div>
        <div class="sub">${b.fc !== null ? 'Forecast $' + Math.round(b.fc) : ''}${b.typ !== null ? ' · typical $' + Math.round(b.typ) : ''}</div></div></div></div>
      <div class="kv"><div><span class="lbl">Electric</span><b>$${b.el ?? '—'}</b><span class="sub">of ~$${b.fEl ?? '—'}</span></div><div><span class="lbl">Gas</span><b>$${b.gas ?? '—'}</b><span class="sub">of ~$${b.fGas ?? '—'}</span></div>
        <div><span class="lbl">Typical bill</span><b>$${b.typ !== null ? Math.round(b.typ) : '—'}</b><span class="sub">this time of year</span></div><div><span class="lbl">Price now</span><b style="color:var(--${T.peak ? 'solar' : 'ok'})">${T.peak ? 'Peak' : 'Off-peak'}</b><span class="sub">${esc(T.next)}</span></div></div>
      <div class="sec"><div class="lbl">Latest full day by hour</div>${hrs}</div>` };
  }
  flow(ev, T) {
    const on = ev.charging;
    const node = (x, c, i, n, v) => `<circle cx="${x}" cy="30" r="22" fill="color-mix(in srgb,var(--${c}) 14%,transparent)" stroke="var(--${c})" stroke-width="1.5"/>
      <svg x="${x - 11}" y="19" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--${c})" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICON[i]}</svg>
      <text x="${x}" y="70">${n}</text><text class="v" x="${x}" y="88">${v}</text>`;
    return `<svg class="flow" viewBox="0 0 360 94" role="img" aria-label="Power flow">
      <line class="base" x1="62" y1="30" x2="158" y2="30"/><line class="base" x1="202" y1="30" x2="298" y2="30"/>
      ${on ? '<line class="dots" stroke="var(--grid)" x1="62" y1="30" x2="158" y2="30"/><line class="dots" stroke="var(--ev)" x1="202" y1="30" x2="298" y2="30"/>' : ''}
      ${node(40, 'grid', 'tower', esc((this.cfg.tou || {}).utility || 'Grid'), T.peak ? 'Peak price' : 'Off-peak')}
      ${node(180, 'home', 'home', 'Home', 'No live meter')}
      ${node(320, 'ev', 'car', 'EV', on ? ev.kw.toFixed(1) + ' kW' : ev.plugged ? 'Waiting' : 'Unplugged')}</svg>`;
  }
  evSheet() {
    const ev = this.ev(); if (!ev) return null;
    const c = ev.c, T = tou(new Date(), this.cfg.tou), arm = this.ui.armed === 'evsheet';
    const tm = (id) => { const x = this.v(id); return x && x !== 'unknown' ? x.slice(0, 5) : null; };
    const toH = (s) => { const [h, m] = s.split(':').map(Number); return h + m / 60; };
    const wdS = tm(c.weekday_start), wdE = tm(c.weekday_end), weS = tm(c.weekend_start), weE = tm(c.weekend_end);
    const sched = this.on(c.schedule);
    const bars = (s, e) => {
      if (!sched || !s || !e) return '<i style="left:0;width:100%"></i>';
      const a = toH(s), b = toH(e);
      if (a === b) return '<i style="left:0;width:100%"></i>';
      return a < b ? `<i style="left:${a / 24 * 100}%;width:${(b - a) / 24 * 100}%"></i>` : `<i style="left:0;width:${b / 24 * 100}%"></i><i style="left:${a / 24 * 100}%;width:${(24 - a) / 24 * 100}%"></i>`;
    };
    const t12 = (s) => { const [h, m] = s.split(':').map(Number); return (h % 12 || 12) + (m ? ':' + String(m).padStart(2, '0') : '') + (h < 12 ? ' AM' : ' PM'); };
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const status = ev.charging ? `Charging · ${ev.kw.toFixed(1)} kW` : ev.plugged ? 'Plugged in' : 'Unplugged';
    return { t: 'EV charger', s: `${esc(c.location || 'Driveway')} · ${status} · ${esc(ev.amps || '—')} A`, b: `
      <div class="kv"><div><span class="lbl">Power</span><b style="color:${ev.charging ? 'var(--ev)' : 'inherit'}">${ev.kw.toFixed(1)} kW</b></div><div><span class="lbl">${ev.charging ? 'Session' : 'Last session'}</span><b>${ev.energy !== null ? ev.energy.toFixed(1) : '—'} kWh</b></div>
        <div><span class="lbl">Range added</span><b>${ev.miles !== null ? '+' + Math.round(ev.miles) : '—'} mi</b></div><div><span class="lbl">Cable</span><b>${ev.plugged ? 'Plugged in' : 'Unplugged'}</b></div></div>
      <div class="sec"><div class="lbl">Charging current</div>${this.ampSeg(ev)}</div>
      <div class="sec"><div class="lbl">Schedule</div><div class="week">${days.map((d, i) => `<span>${d}</span><div class="wb">${i < 5 ? bars(wdS, wdE) : bars(weS, weE)}</div>`).join('')}</div>
        <div class="rows">${this.row('cal', 'Charging schedule', sched ? `Weekdays ${wdS ? t12(wdS) + '–' + t12(wdE) : '—'}${weS && weS === weE ? ', weekends any time' : weS ? `, weekends ${t12(weS)}–${t12(weE)}` : ''}` : 'Off · charges whenever plugged in', this.sw('toggle:' + c.schedule, sched, 'ev'))}</div>
        <div class="sub">Change the schedule times in the ChargePoint app.</div></div>
      <div class="btns" style="--c:var(--ev)">${ev.charging ? (c.stop ? '<button class="btn" data-act="evstop">Stop charging</button>' : '')
        : c.start ? `<button class="btn ${arm ? 'armed' : 'pri'}" data-act="evsheet" ${ev.plugged ? '' : 'disabled'}>${arm ? (T.peak ? 'Peak price now · tap again to start' : 'Tap again to start') : 'Start charging now'}</button>` : ''}</div>` };
  }
  yardSheet() {
    const yards = this.cfg.yard || [];
    return { t: 'Yard & irrigation', s: this.raining() ? 'Raining now' : 'Rachio', b: yards.map((y, yi) => this.yardBlock(y)).join('') };
  }
  yardBlock(y, extra = []) {
    const zones = (y.zones || []).map((z) => this.row(z.icon || 'sprinkler', esc(z.name), !this.ok(z.entity) ? 'Unavailable' : this.on(z.entity) ? 'Running' : 'Idle',
      `<button class="btn" data-act="${this.on(z.entity) ? 'off' : 'on'}:${z.entity}">${this.on(z.entity) ? 'Stop' : 'Run'}</button>`)).join('');
    const ex = extra.map((x) => this.row(x.icon || 'bulb', esc(x.name), this.on(x.entity) ? 'On' : 'Off', this.sw('toggle:' + x.entity, this.on(x.entity), x.color || 'solar', !this.ok(x.entity)))).join('');
    return `<div class="sec"><div class="lbl">${esc(y.name)}</div><div class="rows">${ex}
      ${y.standby ? this.row('sprinkler', 'Standby', this.on(y.standby) ? 'On · scheduled watering is paused' : 'Off · schedules run normally', this.sw('toggle:' + y.standby, this.on(y.standby), 'solar', !this.ok(y.standby))) : ''}
      ${y.rain_delay ? this.row('umbrella', 'Rain delay', this.on(y.rain_delay) ? 'On' : 'Off', this.sw('toggle:' + y.rain_delay, this.on(y.rain_delay), 'home', !this.ok(y.rain_delay))) : ''}
      ${y.rain_sensor ? this.row('drop', 'Rain sensor', this.on(y.rain_sensor) ? 'Wet · watering skipped' : 'Dry') : ''}
      ${zones}</div></div>`;
  }
  weatherSheet() {
    const w = this.cfg.weather || {}, cond = this.v(w.forecast);
    const f = (id, u, d = 0) => { const x = this.n(id); return x === null ? '—' : x.toFixed(d) + u; };
    return { t: 'Weather', s: `${esc(WX_LABEL[cond] || '')} · ${f(w.temp, '°')} outside, ${f(w.inside, '°', 1)} inside`, b: `
      <div class="kv"><div><span class="lbl">Feels like</span><b>${f(w.feels, '°')}</b></div><div><span class="lbl">Humidity</span><b>${f(w.humidity, '%')}</b></div><div><span class="lbl">Wind</span><b>${f(w.wind, ' mph')}</b></div><div><span class="lbl">UV</span><b>${f(w.uv, '')}</b></div>
        <div><span class="lbl">Rain today</span><b>${f(w.rain_today, ' in', 2)}</b></div><div><span class="lbl">Rain this week</span><b>${f(w.rain_week, ' in', 2)}</b></div><div><span class="lbl">Indoor</span><b>${f(w.inside, '°', 1)}</b></div><div><span class="lbl">Rain rate</span><b>${f(w.rain_rate, ' in/h', 2)}</b></div></div>
      <div class="sec fcl"><div class="lbl">Forecast · National Weather Service</div><div class="rows">${(this.ui.fc || []).slice(0, 8).map((x) => `<div class="row">${wx(x.is_daytime === false && WX_KIND[x.condition] === 'pcloudy' ? 'ncloudy' : (WX_KIND[x.condition] || 'cloud'), 30)}<div class="rx"><div class="nm">${esc(this.fcLabel(x))} · ${Math.round(x.temperature)}°</div><div class="sv">${esc(x.detailed_description || WX_LABEL[x.condition] || '')}</div></div>${x.precipitation_probability ? `<span class="sub" style="color:var(--home)">${x.precipitation_probability}%</span>` : ''}</div>`).join('')}</div></div>` };
  }
  safetySheet() {
    const db = this.doorbell(), c = db.c, off = this.offline(), nas = this.nas();
    const vol = this.n(c.volume), levels = c.volume_levels || [['Off', 0], ['Low', 4], ['Med', 8], ['High', 11]];
    const near = (v) => levels.reduce((b, l) => (Math.abs(l[1] - v) < Math.abs(b[1] - v) ? l : b), levels[0])[0];
    const names = off.bad.map((id) => esc((this.s(id) && this.s(id).attributes.friendly_name) || id));
    return { t: 'Front door', s: db.ringing ? 'Doorbell rang at ' + fmtTime(db.ding) : 'Last activity ' + relTime(db.activity || db.motion), b: `
      ${this.thumb(db, true)}
      <div class="btns"><button class="btn" data-act="live">${ic('camera')} Watch live</button></div>
      <div class="sec"><div class="lbl">Recent</div><div class="rows">
        ${this.row('bell', 'Doorbell rang', db.ding ? relTime(db.ding) : 'No rings recorded')}
        ${this.row('door', 'Last activity', relTime(db.activity))}
        ${this.row('door', 'Motion alert', db.motion ? relTime(db.motion) : '—')}</div></div>
      <div class="sgrid">${vol !== null ? `<div class="sec"><div class="lbl">Chime volume</div><div class="seg">${levels.map(([l, v]) => `<button type="button" aria-pressed="${near(vol) === l}" data-act="vol:${v}">${l}</button>`).join('')}</div></div>` : ''}
        <div class="sec"><div class="lbl">Doorbell</div><div class="rows">
          ${c.chime ? this.row('bell', 'In-home chime', this.on(c.chime) ? 'Rings normally' : 'Muted', this.sw('toggle:' + c.chime, this.on(c.chime), 'acc')) : ''}
          ${c.motion_detection ? this.row('door', 'Motion detection', this.on(c.motion_detection) ? 'On' : 'Off', this.sw('toggle:' + c.motion_detection, this.on(c.motion_detection), 'acc')) : ''}</div></div></div>
      <div class="sec"><div class="lbl">Home health</div><div class="rows">
        ${this.row('shield', off.bad.length ? `${off.bad.length} of ${off.total} devices offline` : `All ${off.total} devices online`, off.bad.length ? names.join(', ') : 'Plugs, irrigation, dishwasher, thermostat, doorbell, charger', '', off.bad.length ? 'warn' : '')}
        ${this.row('server', 'NAS storage', nas.bad.length ? 'Check: ' + nas.bad.map((id) => esc(this.v(id))).join(', ') : 'Drives and volume normal', '', nas.bad.length ? 'warn' : '')}
        ${(this.cfg.health || {}).nas_security ? this.row('shield', 'NAS Security Advisor', nas.security ? 'Has warnings · open DSM Security Advisor' : 'No warnings', '', nas.security ? 'warn' : '') : ''}
        ${(this.cfg.health || {}).backup ? this.row('server', 'Home Assistant backups', nas.backup ? 'Last automatic backup ' + relTime(nas.backup) : 'No automatic backups set up', '', nas.backup ? '' : 'warn') : ''}</div></div>` };
  }
  roomSheet(i) {
    const r = (this.cfg.rooms || [])[i]; if (!r) return null;
    const x = this.roomInfo(r);
    let b = '';
    if (r.kind === 'climate') b = this.climateBody(r);
    else if (r.kind === 'appliance') {
      const op = this.v(r.state), fin = this.t(r.finish), prog = this.v(r.program);
      const pretty = (p) => (p || '').replace(/^.*_program_/, '').replace(/_/g, ' ').replace(/\b(\d+)$/, '$1°').replace(/^\w/, (m) => m.toUpperCase());
      b = `<div class="rows">${this.row(r.icon || 'dish', esc(r.appliance || 'Appliance'), esc(x.v) + (op === 'run' && fin ? ' · done at ' + fmtTime(fin) : ''))}
        ${prog && prog !== 'unknown' ? this.row('dish', 'Program', esc(pretty(prog))) : ''}
        ${r.door ? this.row('door', 'Door', esc(this.v(r.door) || '—')) : ''}
        ${r.remote_start ? this.row('bolt', 'Remote start', this.on(r.remote_start) ? 'Allowed' : 'Off · press Remote Start on the dishwasher to allow it') : ''}</div>
        ${r.stop && op === 'run' ? '<div class="btns"><button class="btn" data-act="press:' + r.stop + '">Stop program</button></div>' : ''}`;
    } else if (r.kind === 'switches') {
      b = `<div class="rows">${(r.switches || []).map((s) => {
        const armed = this.ui.armed === 'sw:' + s.entity;
        return this.row(s.icon || 'plug', esc(s.name), !this.ok(s.entity) ? 'Unavailable' : armed ? 'Tap again to switch off' : this.on(s.entity) ? 'On' : 'Off',
          armed ? `<button class="btn armed" data-act="swc:${s.entity}">Tap again</button>` : this.sw((s.confirm_off ? 'swc:' : 'toggle:') + s.entity, this.on(s.entity), s.color || 'ok', !this.ok(s.entity)));
      }).join('')}</div>`;
    } else if (r.kind === 'workshop') b = this.workshopBody();
    else if (r.kind === 'yard') b = this.yardBlock((this.cfg.yard || [])[r.yard ?? 0] || { name: r.name }, r.extra || []);
    return { t: r.sheet_title || r.name, s: esc([x.v, x.s].filter(Boolean).join(' · ')), b };
  }
  climateBody(r) {
    const c = this.s(r.climate); if (!c) return '<div class="sub">The thermostat is unavailable.</div>';
    const a = c.attributes, mode = c.state, eco = a.preset_mode === 'eco', P = this.ui.pend;
    const hum = this.n(r.humidity);
    const modes = (a.hvac_modes || []).map((m) => [m, { heat: 'Heat', cool: 'Cool', heat_cool: 'Heat · Cool', off: 'Off', auto: 'Auto', fan_only: 'Fan' }[m] || m]);
    const val = (k, d) => P[k] ?? d;
    const step = (key, label, col, cur) => `<div class="sec" style="--c:var(--${col})"><div class="lbl">${label}</div><div class="btns" style="align-items:center;flex-wrap:nowrap">
      <button class="btn" data-act="sp:${key}:-1" aria-label="${label} down">${ic('minus')}</button>
      <span class="hero" style="font-size:40px;min-width:96px;text-align:center;color:var(--c)">${cur}°</span>
      <button class="btn" data-act="sp:${key}:1" aria-label="${label} up">${ic('plus')}</button></div></div>`;
    const sp = eco ? '<div class="sub">Eco is on: the Nest uses its Eco temperatures. Turn Eco off to set your own.</div>'
      : mode === 'heat' ? step('temperature', 'Heat to', 'heat', val('temperature', a.temperature))
      : mode === 'cool' ? step('temperature', 'Cool to', 'home', val('temperature', a.temperature))
      : mode === 'heat_cool' ? `<div class="sgrid one">${step('target_temp_low', 'Heat to', 'heat', val('target_temp_low', a.target_temp_low))}${step('target_temp_high', 'Cool to', 'home', val('target_temp_high', a.target_temp_high))}</div>`
      : '<div class="sub">The thermostat is off. Pick a mode to start heating or cooling.</div>';
    const fanOn = a.fan_mode === 'on', fanScript = r.fan_script && this.on(r.fan_script);
    const until = fanScript && this.ui.fanUntil > Date.now() ? new Date(this.ui.fanUntil) : this.t(r.fan_timer);
    const fanSel = !fanOn ? 'off' : fanScript ? (this.ui.fanChoice || '15') : 'on';
    const fanOpts = [['off', 'Off'], ...(r.fan_script ? [['15', '15 min'], ['60', '1 hour']] : []), ['on', r.fan_script ? 'Until off' : 'On']];
    return `<div class="kv"><div><span class="lbl">Inside</span><b>${a.current_temperature ?? '—'}°</b></div><div><span class="lbl">Humidity</span><b>${hum !== null ? Math.round(hum) + '%' : '—'}</b></div>
        <div><span class="lbl">Now</span><b style="color:${a.hvac_action === 'heating' ? 'var(--heat)' : a.hvac_action === 'cooling' ? 'var(--home)' : 'inherit'}">${esc({ heating: 'Heating', cooling: 'Cooling', idle: 'Idle', off: 'Off', fan: 'Fan' }[a.hvac_action] || a.hvac_action || '—')}</b></div>
        <div><span class="lbl">Outside</span><b>${this.n((this.cfg.weather || {}).temp) !== null ? Math.round(this.n((this.cfg.weather || {}).temp)) + '°' : '—'}</b></div></div>
      <div class="sec"><div class="lbl">Mode</div><div class="seg">${modes.map(([v, l]) => `<button type="button" aria-pressed="${mode === v}" data-act="hvac:${v}">${l}</button>`).join('')}</div></div>
      ${sp}
      ${(a.preset_modes || []).includes('eco') ? `<div class="rows">${this.row('leaf', 'Eco temperatures', eco ? 'On · saves energy while you are away' : 'Off', this.sw('eco', eco, 'ok'))}</div>` : ''}
      ${(a.fan_modes || []).length ? `<div class="sec"><div class="lbl">Fan</div><div class="seg">${fanOpts.map(([v, l]) => `<button type="button" aria-pressed="${fanSel === v}" data-act="fan:${v}">${l}</button>`).join('')}</div>
        <div class="sub">${!fanOn ? 'Runs the fan without heating or cooling.' : until ? `Fan running until ${fmtTime(until)}.` : 'Fan running.'}</div></div>` : ''}`;
  }
  workshopBody() {
    const w = this.workshop(), room = w.room, outs = Object.values(w.out);
    const anyOn = outs.some((o) => o.on);
    const wr = (o) => {
      const armed = this.ui.armed === 'ws:' + o.key;
      const sv = !o.avail ? 'Unavailable' : (o.key === room.exhaust && w.clearing ? 'Clearing fumes' : o.on ? `On${o.w !== null ? ' · ' + Math.round(o.w) + ' W' : ''}` : 'Off')
        + (armed ? ' · ' + (o.confirm_text || 'tap again to switch off') : o.note ? ' · ' + o.note : '');
      return this.row(o.icon || 'plug', esc(o.name), esc(sv), armed ? `<button class="btn armed" data-act="ws:${o.key}">Tap again</button>` : this.sw('ws:' + o.key, o.on, 'heat', !o.avail));
    };
    const laserOn = w.laser && w.laser.on;
    return `${w.warn ? `<div class="row act">${ic('fan')}<div class="rx"><div class="nm">${esc(w.laser.name)} is drawing ${Math.round(w.laser.w)} W with the exhaust off</div><div class="sv">Turn the exhaust on before cutting</div></div><button class="btn" data-act="ws:${room.exhaust}">Turn on</button></div>` : ''}
      ${room.start_script || room.end_script ? `<div class="sec"><div class="btns" style="--c:var(--heat)">${room.start_script ? '<button class="btn pri" data-act="wsstart">Start laser session</button>' : ''}${room.end_script ? `<button class="btn" data-act="wsend" ${laserOn || anyOn ? '' : 'disabled'}>End session</button>` : ''}</div>
        <div class="sub">${esc(room.session_help || 'Start powers the PC, laser, air assist and exhaust. End switches off the laser and air assist and runs the exhaust 3 more minutes to clear fumes. The PC stays on so Windows can shut down properly.')}</div></div>` : ''}
      <div class="sec"><div class="lbl">Laser cutter &amp; accessories</div><div class="rows">${outs.map(wr).join('')}</div></div>`;
  }

  // ---------- actions ----------
  arm(id) { this.ui.armed = id; clearTimeout(this._armT); this._armT = setTimeout(() => { this.ui.armed = null; this._schedule(true); }, 4000); }
  toggle(id, on) { const dom = id.split('.')[0]; return this.call(['switch', 'light', 'input_boolean', 'fan'].includes(dom) ? dom : 'homeassistant', on ? 'turn_on' : 'turn_off', { entity_id: id }); }
  quick(i) {
    const a = (this.cfg.actions || [])[i]; if (!a) return;
    const s = this.tileState(a); if (s.na) return;
    const ids = a.entities || [a.entity];
    if (a.kind === 'ev') {
      const ev = this.ev();
      if (ev.charging) { if (ev.c.stop) this.call('button', 'press', { entity_id: ev.c.stop }); return; }
      if (!ev.plugged) return;
      if (this.ui.armed !== 'qa' + i) { this.arm('qa' + i); return; }
      this.ui.armed = null; if (ev.c.start) this.call('button', 'press', { entity_id: ev.c.start }); return;
    }
    if (a.kind === 'mute') { ids.forEach((id) => this.toggle(id, !this.on(id))); return; }
    if (s.on && a.confirm_off && this.ui.armed !== 'qa' + i) { this.arm('qa' + i); return; }
    this.ui.armed = null;
    ids.forEach((id) => this.toggle(id, !s.on));
  }
  setpoint(key, delta) {
    const room = (this.cfg.rooms || []).find((r) => r.kind === 'climate'); const c = room && this.s(room.climate); if (!c) return;
    const a = c.attributes, P = this.ui.pend;
    const cur = P[key] ?? a[key]; if (cur == null) return;
    const lim = (v) => Math.max(a.min_temp ?? 50, Math.min(a.max_temp ?? 90, v));
    let nv = lim(cur + delta);
    if (key === 'target_temp_low') nv = Math.min(nv, (P.target_temp_high ?? a.target_temp_high) - 3);
    if (key === 'target_temp_high') nv = Math.max(nv, (P.target_temp_low ?? a.target_temp_low) + 3);
    P[key] = nv;
    clearTimeout(this._spT);
    this._spT = setTimeout(() => {
      const data = { entity_id: room.climate };
      if (c.state === 'heat_cool') { data.target_temp_low = P.target_temp_low ?? a.target_temp_low; data.target_temp_high = P.target_temp_high ?? a.target_temp_high; }
      else data.temperature = P.temperature ?? a.temperature;
      this.call('climate', 'set_temperature', data).finally(() => { setTimeout(() => { this.ui.pend = {}; this._schedule(true); }, 1500); });
    }, 1200);
  }
  _click(e) {
    const path = e.composedPath();
    const find = (attr) => path.find((el) => el.dataset && el.dataset[attr] !== undefined);
    const a = find('act'), q = find('qa'), o = find('open');
    this.ui.lastTouch = Date.now();
    if (a) {
      const [k, v, w] = a.dataset.act.split(':');
      if (k === 'closebg' && e.target !== a) return;
      const climateRoom = (this.cfg.rooms || []).find((r) => r.kind === 'climate');
      const ws = this.workshop();
      switch (k) {
        case 'close': case 'closebg': this.ui.sheet = null; break;
        case 'wake': this.ui.lastTouch = Date.now(); break;
        case 'menu': this.dispatchEvent(new Event('hass-toggle-menu', { bubbles: true, composed: true })); return;
        case 'theme': {
          const sunUp = this.v(this.cfg.sun || 'sun.sun') === 'above_horizon';
          const m = this.mode() === 'dark' ? 'light' : 'dark';
          this.ui.theme = m === (sunUp ? 'light' : 'dark') ? null : { mode: m, sunUp };
          try { if (this.ui.theme) localStorage.setItem('home-panel-theme', JSON.stringify(this.ui.theme)); else localStorage.removeItem('home-panel-theme'); } catch (err) { /* ignore */ }
          break;
        }
        case 'live': {
          const id = (this.cfg.front_door || {}).live || (this.cfg.front_door || {}).camera;
          if (id) this.dispatchEvent(new CustomEvent('hass-more-info', { detail: { entityId: id }, bubbles: true, composed: true }));
          return;
        }
        case 'amps': { const ev = this.ev(); if (ev) { this.ui.pend.amps = v; this.call('select', 'select_option', { entity_id: ev.c.amps, option: v }).finally(() => setTimeout(() => { delete this.ui.pend.amps; this._schedule(true); }, 4000)); } break; }
        case 'evstop': { const ev = this.ev(); if (ev && ev.c.stop) this.call('button', 'press', { entity_id: ev.c.stop }); break; }
        case 'evsheet': { const ev = this.ev(); if (this.ui.armed === 'evsheet') { this.ui.armed = null; if (ev && ev.c.start) this.call('button', 'press', { entity_id: ev.c.start }); } else this.arm('evsheet'); break; }
        case 'toggle': { const id = a.dataset.act.slice(7); this.toggle(id, !this.on(id)); break; }
        case 'swc': { const id = a.dataset.act.slice(4); if (this.on(id) && this.ui.armed !== 'sw:' + id) this.arm('sw:' + id); else { this.ui.armed = null; this.toggle(id, !this.on(id)); } break; }
        case 'on': this.toggle(a.dataset.act.slice(3), true); break;
        case 'off': this.toggle(a.dataset.act.slice(4), false); break;
        case 'press': this.call('button', 'press', { entity_id: a.dataset.act.slice(6) }); break;
        case 'vol': this.call('number', 'set_value', { entity_id: (this.cfg.front_door || {}).volume, value: +v }); break;
        case 'hvac': if (climateRoom) { this.ui.pend = {}; this.call('climate', 'set_hvac_mode', { entity_id: climateRoom.climate, hvac_mode: v }); } break;
        case 'eco': if (climateRoom) { const c = this.s(climateRoom.climate); this.call('climate', 'set_preset_mode', { entity_id: climateRoom.climate, preset_mode: c.attributes.preset_mode === 'eco' ? 'none' : 'eco' }); } break;
        case 'sp': this.setpoint(v, +w); break;
        case 'fan': if (climateRoom) {
          const r = climateRoom;
          if (r.fan_script) this.call('script', 'turn_off', { entity_id: r.fan_script });
          if (v === 'off') this.call('climate', 'set_fan_mode', { entity_id: r.climate, fan_mode: 'off' });
          else if (v === 'on') this.call('climate', 'set_fan_mode', { entity_id: r.climate, fan_mode: 'on' });
          else if (r.fan_script) {
            this.ui.fanChoice = v; this.ui.fanUntil = Date.now() + +v * 60e3;
            try { localStorage.setItem('home-panel-fan-until', String(this.ui.fanUntil)); } catch (err) { /* ignore */ }
            setTimeout(() => this.call('script', 'turn_on', { entity_id: r.fan_script, variables: { minutes: +v } }), 300);
          }
        } break;
        case 'ws': if (ws) {
          const o = ws.out[v]; if (!o) break;
          if (o.on && o.confirm_off && this.ui.armed !== 'ws:' + v) { this.arm('ws:' + v); break; }
          this.ui.armed = null; this.toggle(o.switch, !o.on);
        } break;
        case 'wsstart': if (ws && ws.room.start_script) this.call('script', 'turn_on', { entity_id: ws.room.start_script }); break;
        case 'wsend': if (ws && ws.room.end_script) this.call('script', 'turn_on', { entity_id: ws.room.end_script }); break;
        default: break;
      }
      this._schedule(true);
      return;
    }
    if (q) { this.quick(+q.dataset.qa); this._schedule(true); return; }
    if (o) { const k = o.dataset.open; if (k === 'none') return; this.ui.sheet = k; this._schedule(true); }
  }
}

if (!customElements.get('home-panel')) customElements.define('home-panel', HomePanel);
