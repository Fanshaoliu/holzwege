'use strict';
/* Input routing, game loop, lifecycle. */
const Input = (() => {
  const held = [];
  const KEYS = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', w: 'up', s: 'down', a: 'left', d: 'right',
    W: 'up', S: 'down', A: 'left', D: 'right' };
  const OK = new Set(['z', 'Z', 'Enter', ' ', 'j', 'J', 'e', 'E']);
  const NO = new Set(['x', 'X', 'Escape', 'Backspace', 'k', 'K', 'q', 'Q']);
  function press(d) { if (!held.includes(d)) held.push(d); onDir(d); }
  function release(d) { const i = held.indexOf(d); if (i >= 0) held.splice(i, 1); }
  function dir() { return G.mode === 'map' ? (held[held.length - 1] || null) : null; }
  function clear() { held.length = 0; }

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
      if (G.mode === 'name') return;
      const d = KEYS[e.key];
      if (d) { e.preventDefault(); if (!e.repeat) press(d); else if (G.mode !== 'map') onDir(d); return; }
      if (e.repeat) return;
      if (OK.has(e.key)) { e.preventDefault(); ok(); }
      else if (NO.has(e.key)) { e.preventDefault(); cancel(); }
      else if (e.key === 'm' || e.key === 'M') { if (G.mode === 'map') UI.openMenu(); }
    });
    window.addEventListener('keyup', e => { const d = KEYS[e.key]; if (d) release(d); });
    window.addEventListener('blur', clear);
    // on-screen d-pad with finger sliding
    const dpad = $('dpad');
    let active = null;
    const pick = (x, y) => { const el = document.elementFromPoint(x, y); return el && el.dataset && el.dataset.d ? el.dataset.d : null; };
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
  return { init, dir, clear, ok, cancel };
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
    await World.load(s.map, s.x, s.y, s.dir);
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

  function frame(ts) {
    const dt = Math.min(0.05, ((ts - last) / 1000) || 0.016); last = ts;
    if (document.body.dataset.mode !== G.mode) document.body.dataset.mode = G.mode;
    if (G.mode === 'map' || G.mode === 'scene' || G.mode === 'menu') World.update(dt);
    World.render();
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
  }

  return { boot, toTitle, ending, loadFrom, newGame };
})();

window.addEventListener('DOMContentLoaded', () => Main.boot());
