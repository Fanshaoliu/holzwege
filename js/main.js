'use strict';
/* Input routing, game loop, lifecycle. */
const Input = (() => {
  const held = [];
  const KEYS = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', w: 'up', s: 'down', a: 'left', d: 'right',
    W: 'up', S: 'down', A: 'left', D: 'right' };
  const OK = new Set(['z', 'Z', 'Enter', ' ', 'j', 'J', 'e', 'E']);
  const NO = new Set(['x', 'X', 'Escape', 'Backspace', 'k', 'K', 'q', 'Q']);
  // physical keys, for when an input method turns e.key into 'Process'
  const CODES = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', KeyW: 'up', KeyS: 'down', KeyA: 'left', KeyD: 'right' };
  const OK_CODES = new Set(['KeyZ', 'Enter', 'NumpadEnter', 'Space', 'KeyJ', 'KeyE']);
  const NO_CODES = new Set(['KeyX', 'Escape', 'Backspace', 'KeyK', 'KeyQ']);
  const dirOf = e => KEYS[e.key] || CODES[e.code];
  // a tap that is released before the next frame still counts as one step (or a turn)
  let tap = null;
  function press(d) { if (!held.includes(d)) held.push(d); if (G.mode === 'map') tap = d; onDir(d); }
  function release(d) { const i = held.indexOf(d); if (i >= 0) held.splice(i, 1); }
  function dir() {
    if (G.mode !== 'map') { tap = null; return null; }
    const d = held[held.length - 1] || tap;
    tap = null;
    return d || null;
  }
  function clearTap() { tap = null; }
  function clear() { held.length = 0; tap = null; }

  function onDir(d) {
    Audio.unlock();
    if (G.mode === 'map') return;
    if (G.mode === 'battle') { Battle.poke(); UI.navMove(d); return; }
    if (UI.nav) {
      if (UI.nav.buttons.length === 1 && UI.scrollEl && (d === 'up' || d === 'down')) { UI.scrollEl.scrollTop += d === 'up' ? -60 : 60; return; }
      UI.navMove(d);
    }
  }
  function ok() {
    Audio.unlock();
    if (UI.creditsSkip) { UI.creditsSkip(); return; }
    switch (G.mode) {
      case 'map': World.interact(); break;
      case 'scene': if (UI.nav && !UI.dialogActive()) UI.navOk(); else UI.advance(); break;
      case 'battle': if (!Battle.confirm()) UI.navOk(); break;
      case 'menu': case 'title': UI.navOk(); break;
      default: break;
    }
  }
  function cancel() {
    Audio.unlock();
    if (UI.creditsSkip) { UI.creditsSkip(); return; }
    switch (G.mode) {
      case 'map': if (!World.player.moving) { clear(); UI.openMenu(); } break;
      case 'scene': if (!UI.nav) UI.advance(); break;
      case 'battle': if (!Battle.confirm()) UI.navBack(); break;
      case 'menu': case 'title': UI.navBack(); break;
      default: break;
    }
  }

  function init() {
    window.addEventListener('keydown', e => {
      if (G.mode === 'name' || e.ctrlKey || e.metaKey || e.altKey) return;
      const d = dirOf(e);
      if (d) {
        e.preventDefault();
        if (!e.repeat) { release(d); press(d); }
        else if (!held.includes(d)) press(d);
        else if (G.mode !== 'map') onDir(d);
        return;
      }
      if (e.repeat) return;
      if (OK.has(e.key) || OK_CODES.has(e.code)) { e.preventDefault(); ok(); }
      else if (NO.has(e.key) || NO_CODES.has(e.code)) { e.preventDefault(); cancel(); }
      else if (e.key === 'm' || e.key === 'M' || e.code === 'KeyM') { if (G.mode === 'map') UI.openMenu(); }
    });
    window.addEventListener('keyup', e => { const d = dirOf(e); if (d) release(d); });
    window.addEventListener('blur', clear);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) return;
      clear();
      if (G.map && G.mode === 'map' && !Script.running && !World.busy) writeSave(AUTO_KEY);
    });
    // on-screen d-pad with finger sliding
    const dpad = $('dpad');
    let active = null;
    // direction from the thumb's angle around the pad centre, so corners and the middle never go dead
    const pick = (x, y) => {
      const r = dpad.getBoundingClientRect();
      const dx = x - (r.left + r.width / 2), dy = y - (r.top + r.height / 2);
      if (Math.hypot(dx, dy) < r.width * 0.1) return null;
      return Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    };
    const setDir = (d) => {
      if (d === active) return;
      if (active) { release(active); dpad.querySelector(`[data-d="${active}"]`).classList.remove('on'); }
      active = d;
      if (d) { press(d); dpad.querySelector(`[data-d="${d}"]`).classList.add('on'); }
    };
    dpad.addEventListener('pointerdown', e => { e.preventDefault(); dpad.setPointerCapture(e.pointerId); setDir(pick(e.clientX, e.clientY)); });
    dpad.addEventListener('pointermove', e => { if (active !== null || e.buttons) setDir(pick(e.clientX, e.clientY)); });
    const up = () => setDir(null);
    dpad.addEventListener('pointerup', up); dpad.addEventListener('pointercancel', up); dpad.addEventListener('lostpointercapture', up);
    const btn = (id, fn) => {
      const b = $(id);
      b.addEventListener('pointerdown', e => { e.preventDefault(); b.classList.add('on'); fn(); });
      const off = () => b.classList.remove('on');
      b.addEventListener('pointerup', off); b.addEventListener('pointercancel', off); b.addEventListener('pointerleave', off);
    };
    btn('btn-a', ok); btn('btn-b', cancel);
    // taps
    $('game').addEventListener('pointerdown', e => {
      Audio.unlock();
      if (G.mode === 'map') World.tapAt(e.clientX, e.clientY);
      else if (G.mode === 'scene' && !UI.nav) UI.advance();
    });
    $('dlg').addEventListener('pointerdown', e => { e.stopPropagation(); Audio.unlock(); if (!UI.nav) UI.advance(); });
    $('cg').addEventListener('pointerdown', () => { if (G.mode === 'scene' && !UI.nav) UI.advance(); });
    $('battle').addEventListener('pointerdown', () => Battle.confirm());
    $('menu-btn').addEventListener('click', e => { e.stopPropagation(); Audio.unlock(); if (G.mode === 'map') UI.openMenu(); });
    document.addEventListener('contextmenu', e => e.preventDefault());
  }
  return { init, dir, clear, clearTap, ok, cancel };
})();

const Main = (() => {
  let last = 0;
  const handlers = {
    newGame: () => newGame(),
    cont: () => { const s = readSave(AUTO_KEY); if (s) loadFrom(s); },
    load: () => { UI.hideTitle(); G.mode = 'title'; titleLoad(); },
  };
  function titleLoad() {
    // reuse the in-game save panel in load mode
    const back = () => { $('panel').classList.add('hidden'); UI.showTitle(handlers); };
    $('title').classList.remove('hidden');
    const keys = [AUTO_KEY].concat(SAVE_KEYS);
    const wrap = document.createElement('div');
    const btns = keys.map((k, i) => {
      const s = readSave(k);
      const b = UI.mkOpt((k === AUTO_KEY ? '自动记录' : `记录 ${i}`) + '　' + describeSave(s), () => { if (s) { $('panel').classList.add('hidden'); loadFrom(s); } }, s ? '' : 'dis');
      wrap.appendChild(b); return b;
    });
    const p = $('panel'); p.innerHTML = '<h2>读取存档</h2>'; p.classList.remove('hidden');
    const body = document.createElement('div'); body.className = 'panel-body'; body.appendChild(wrap); p.appendChild(body);
    const bk = UI.mkOpt('返回', back); bk.className = 'btn'; const row = document.createElement('div'); row.className = 'btnrow'; row.appendChild(bk); p.appendChild(row);
    btns.push(bk);
    UI.setNav(btns, { back });
  }

  function resetState() {
    G.name = '林恩'; G.flags = { ch: 1 }; G.items = {}; G.codex = {}; G.party = []; G.opened = {};
    G.map = null; G.mapId = null;
    World.npcs = []; World.followers = [];
  }
  function showPlayUI() { $('menu-btn').classList.remove('hidden'); }

  async function newGame() {
    resetState();
    UI.hideTitle();
    Audio.play('none');
    showPlayUI();
    G.mode = 'scene';
    await Script.run('c0_intro');
  }
  async function loadFrom(s) {
    resetState();
    G.name = s.name; G.flags = s.flags || {}; G.items = s.items || {}; G.codex = s.codex || {}; G.party = s.party || []; G.opened = s.opened || {};
    UI.hideTitle(); UI.cg('off'); UI.hideDialog();
    UI.loading(true);
    await World.load(s.map, s.x, s.y, s.dir);
    UI.loading(false);
    showPlayUI();
    G.mode = 'map';
    await UI.fade('in', 300);
  }
  function toTitle() {
    Audio.stop(); UI.hideDialog(); UI.cg('off');
    UI.showTitle(handlers);
  }
  async function ending(n) {
    G.flags.ending = n;
    G.global.endings[n] = 1; saveGlobal();
    writeSave('holzwege.clear' + n);
    await UI.fade('out', 1500);
    UI.cg('off');
    await UI.credits(n);
    await UI.fade('in', 10);
    toTitle();
  }

  let frameErr = 0;
  function frame(ts) {
    const dt = Math.min(0.05, ((ts - last) / 1000) || 0.016); last = ts;
    try {
      if (document.body.dataset.mode !== G.mode) { document.body.dataset.mode = G.mode; Input.clearTap(); }
      if (G.mode === 'map' || G.mode === 'scene' || G.mode === 'menu') World.update(dt);
      World.render();
    } catch (e) {
      if (frameErr++ < 3) console.error(e);
    }
    requestAnimationFrame(frame);
  }

  async function boot() {
    loadGlobal();
    World.init();
    Input.init();
    await Promise.all(['assets/items.png', 'assets/cg/cover.png', 'assets/maps/chest.png', 'assets/maps/chest_open.png', 'assets/chars/hero.png'].map(loadImage));
    try { await document.fonts.load(`24px FusionPixel`, '林中路'); } catch (e) { /* ignore */ }
    $('loading').classList.add('hidden');
    UI.showTitle(handlers);
    requestAnimationFrame(frame);
    // start after the page's own load event so the browser does not show the page as still loading
    if (document.readyState === 'complete') Prefetch.start();
    else window.addEventListener('load', () => Prefetch.start(), { once: true });
  }

  return { boot, toTitle, ending, loadFrom, newGame };
})();

window.addEventListener('DOMContentLoaded', () => Main.boot());
