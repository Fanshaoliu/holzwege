'use strict';
/* global state + small helpers */
const G = {
  name: '林恩', flags: {}, items: {}, codex: {}, party: [], opened: {},
  mapId: null, map: null, mode: 'boot', settings: { speed: 2, bgm: 0.55, sfx: 0.7 },
  global: { endings: {}, codex: {} },
};
const DIRS = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
const OPP = { up: 'down', down: 'up', left: 'right', right: 'left' };
const T = 16;

function $(id) { return document.getElementById(id); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function hash(x, y, s) {
  let n = (x * 374761393 + y * 668265263 + (s || 0) * 2147483647) >>> 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177) >>> 0;
  return ((n ^ (n >>> 16)) & 0xffffff) / 0x1000000;
}
function fmt(text) { return (text || '').replace(/\{林恩\}/g, G.name); }

/* ---------- condition language:  a & !b | (item:x & ch>=3) ---------- */
function flagVal(name) {
  if (name === 'true') return 1;
  if (name === 'false') return 0;
  if (name === 'coins') return G.items.coin || 0;
  if (name.startsWith('item:')) return (G.items[name.slice(5)] || 0) > 0 ? 1 : 0;
  if (name.startsWith('party:')) return G.party.includes(name.slice(6)) ? 1 : 0;
  const v = G.flags[name];
  return v === undefined ? 0 : v;
}
function evalCond(src) {
  if (src === null || src === undefined || src === '') return true;
  const toks = String(src).match(/!|&|\||\(|\)|[A-Za-z0-9_:]+\s*(>=|<=|==|!=|>|<)\s*-?\d+|[A-Za-z0-9_:]+/g) || [];
  let i = 0;
  function peek() { return toks[i]; }
  function next() { return toks[i++]; }
  function or() { let v = and(); while (peek() === '|') { next(); const r = and(); v = v || r; } return v; }
  function and() { let v = un(); while (peek() === '&') { next(); const r = un(); v = v && r; } return v; }
  function un() { if (peek() === '!') { next(); return !un(); } return prim(); }
  function prim() {
    const t = next();
    if (t === '(') { const v = or(); next(); return v; }
    if (!t) return true;
    const m = t.match(/^([A-Za-z0-9_:]+)\s*(>=|<=|==|!=|>|<)\s*(-?\d+)$/);
    if (m) {
      const a = flagVal(m[1]), b = parseInt(m[3], 10);
      switch (m[2]) { case '>=': return a >= b; case '<=': return a <= b; case '==': return a === b; case '!=': return a !== b; case '>': return a > b; default: return a < b; }
    }
    return !!flagVal(t);
  }
  try { return !!or(); } catch (e) { console.warn('cond error', src, e); return false; }
}
function pickPage(pages) {
  if (!pages) return null;
  for (const [cond, scene] of pages) { if (evalCond(cond)) return scene; }
  return null;
}

/* ---------- assets ---------- */
const IMG = {};
function loadImage(src) {
  if (IMG[src]) return IMG[src].p;
  const img = new Image();
  const p = new Promise(res => { img.onload = () => res(img); img.onerror = () => { console.warn('img fail', src); res(null); }; });
  img.src = src;
  IMG[src] = { img, p };
  return p;
}
function img(src) { const e = IMG[src]; return e && e.img.complete && e.img.naturalWidth ? e.img : null; }

/* ---------- persistence ---------- */
const SAVE_KEYS = ['holzwege.slot1', 'holzwege.slot2', 'holzwege.slot3'];
const AUTO_KEY = 'holzwege.auto';
function snapshot() {
  const p = World.player;
  return { v: 1, name: G.name, flags: G.flags, items: G.items, codex: G.codex, party: G.party, opened: G.opened,
    map: G.mapId, x: p.x, y: p.y, dir: p.dir, time: Date.now() };
}
function writeSave(key) { try { localStorage.setItem(key, JSON.stringify(snapshot())); return true; } catch (e) { return false; } }
function readSave(key) { try { const s = localStorage.getItem(key); return s ? JSON.parse(s) : null; } catch (e) { return null; } }
function saveGlobal() { try { localStorage.setItem('holzwege.global', JSON.stringify({ g: G.global, s: G.settings })); } catch (e) { /* ignore */ } }
function loadGlobal() {
  try { const s = JSON.parse(localStorage.getItem('holzwege.global') || 'null'); if (s) { G.global = Object.assign(G.global, s.g || {}); G.settings = Object.assign(G.settings, s.s || {}); } } catch (e) { /* ignore */ }
}
function describeSave(s) {
  if (!s) return '（空）';
  const m = window.MAPS[s.map];
  const d = new Date(s.time);
  const pad = n => String(n).padStart(2, '0');
  return `${s.name} · ${m ? m.name : s.map} · ${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
