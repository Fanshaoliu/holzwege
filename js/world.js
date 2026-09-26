'use strict';
/* Map, entities, movement, collision and rendering. */
const World = (() => {
  const FW = 26, FH = 38;
  const ROW = { down: 0, left: 1, right: 2, up: 3 };
  const SPEED = 6.2;          // tiles per second
  const W = {
    canvas: null, ctx: null, buf: null, b: null, scale: 3, bw: 320, bh: 240, cam: { x: 0, y: 0 },
    player: { id: 'hero', x: 0, y: 0, px: 0, py: 0, dir: 'down', moving: false, t: 0, fx: 0, fy: 0, foot: 0, frame: 1 },
    followers: [], npcs: [], solid: null, time: 0, autoPath: null, autoGoal: null, autoWait: 0, pendingInteract: null, held: null, autoRan: {},
    busy: false, lightCanvas: null,
  };

  function init() {
    W.canvas = $('game');
    W.ctx = W.canvas.getContext('2d');
    W.buf = document.createElement('canvas');
    W.b = W.buf.getContext('2d');
    W.lightCanvas = document.createElement('canvas');
    resize();
    window.addEventListener('resize', resize);
  }

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const cw = W.canvas.clientWidth || window.innerWidth, ch = W.canvas.clientHeight || window.innerHeight;
    W.canvas.width = Math.round(cw * dpr); W.canvas.height = Math.round(ch * dpr);
    const land = cw >= ch;
    const tw = land ? 19 : 11.5, th = land ? 11.5 : 12;
    W.scale = Math.max(1, Math.floor(Math.min(W.canvas.width / (tw * T), W.canvas.height / (th * T))));
    W.bw = Math.ceil(W.canvas.width / W.scale); W.bh = Math.ceil(W.canvas.height / W.scale);
    W.buf.width = W.bw; W.buf.height = W.bh;
    W.lightCanvas.width = W.bw; W.lightCanvas.height = W.bh;
    W.ctx.imageSmoothingEnabled = false; W.b.imageSmoothingEnabled = false;
  }

  /* ---------------- map loading ---------------- */
  function sheetOf(id) { return `assets/chars/${id}.png`; }
  async function preloadMap(m) {
    const core = [m.img, sheetOf('hero')];
    if (m.fg) core.push(m.fg);
    const rest = [];
    (m.decals || []).forEach(d => rest.push(d.img));
    (m.npcs || []).forEach(n => rest.push(sheetOf(n.sprite)));
    G.party.forEach(p => rest.push(sheetOf(p)));
    rest.push('assets/maps/chest.png', 'assets/maps/chest_open.png');
    if ((m.anims || []).some(a => a.kind === 'wheel')) rest.push('assets/maps/wheel.png');
    if ((m.anims || []).some(a => a.kind === 'core')) rest.push('assets/maps/core_anim.png');
    // sprites that are still downloading pop in when they arrive; never keep the player on a black screen for long
    const restDone = Promise.all(rest.map(loadImage));
    await Promise.race([Promise.all(core.map(loadImage)), sleep(12000)]);
    await Promise.race([restDone, sleep(1500)]);
  }

  async function load(id, x, y, dir) {
    const m = window.MAPS[id];
    if (!m) { console.error('no map', id); return; }
    await preloadMap(m);
    G.mapId = id; G.map = m;
    W.solid = m.solid.map(r => r.split('').map(c => c === '1'));
    const p = W.player;
    p.x = x; p.y = y; p.px = x * T; p.py = y * T; p.dir = dir || p.dir; p.moving = false; p.frame = 1;
    W.followers = G.party.map(id2 => ({ id: id2, x, y, px: x * T, py: y * T, dir: p.dir, moving: false, t: 0, fx: x, fy: y, foot: 0, frame: 1 }));
    W.npcs = (m.npcs || []).map(n => Object.assign({}, n, { px: n.x * T, py: n.y * T, hx: n.x, hy: n.y, moving: false, t: 0, fx: n.x, fy: n.y,
      foot: 0, frame: 1, wait: 1 + Math.random() * 3 }));
    W.autoPath = null; W.autoGoal = null; W.pendingInteract = null; W.autoRan = {};
    Audio.play(m.music);
    UI.mapName(m.name);
    updateCamera(true);
  }

  async function warp(id, x, y, dir, fromScript) {
    W.busy = true;
    Input.clearTap();
    try {
      Audio.sfx('door');
      await UI.fade('out', 260);
      UI.loading(true);
      await load(id, x, y, dir);
      if (!fromScript) writeSave(AUTO_KEY);
      render();
    } catch (e) {
      console.error(e);
    } finally {
      UI.loading(false);
      await UI.fade('in', 260);
      W.busy = false;
    }
    if (!fromScript) runAuto();
  }

  function runAuto() {
    const m = G.map;
    if (!m || Script.running) return false;
    for (let i = 0; i < (m.events || []).length; i++) {
      const e = m.events[i];
      if (e.trigger !== 'auto' || W.autoRan[i]) continue;
      if (evalCond(e.cond)) { W.autoRan[i] = true; Script.run(e.scene); return true; }
    }
    return false;
  }

  /* ---------------- queries ---------------- */
  function npcVisible(n) {
    const k = `show_${G.mapId}_${n.id}`;
    const f = G.flags[k];
    if (f === 1) return true;
    if (f === -1) return false;
    return evalCond(n.show);
  }
  function decalVisible(d) { return evalCond(d.cond); }
  function inCells(list, x, y) { return list && list.some(c => c[0] === x && c[1] === y); }
  function chestAt(x, y) { return (G.map.chests || []).find(c => c.x === x && c.y === y); }
  function spotAt(x, y) { return (G.map.spots || []).find(c => c.x === x && c.y === y); }
  function npcAt(x, y) {
    return W.npcs.find(n => npcVisible(n) && ((n.x === x && n.y === y) || (n.moving && n.fx === x && n.fy === y)));
  }
  function blocked(x, y) {
    const m = G.map;
    if (x < 0 || y < 0 || x >= m.w || y >= m.h) return true;
    let s = W.solid[y][x];
    for (const d of m.decals || []) {
      if (!decalVisible(d)) continue;
      if (inCells(d.walk, x, y)) s = false;
      if (inCells(d.solid, x, y)) s = true;
    }
    if (chestAt(x, y)) s = true;
    return s;
  }
  function free(x, y, forNpc) {
    if (blocked(x, y)) return false;
    if (npcAt(x, y)) return false;
    if (forNpc) {
      const p = W.player;
      if ((p.x === x && p.y === y)) return false;
      if (W.followers.some(f => f.x === x && f.y === y)) return false;
      if ((G.map.warps || []).some(w => x >= w.x && x < w.x + (w.w || 1) && y >= w.y && y < w.y + (w.h || 1))) return false;
    }
    return true;
  }

  /* ---------------- movement ---------------- */
  function startStep(e, dir, speed) {
    const [dx, dy] = DIRS[dir];
    e.dir = dir; e.fx = e.x; e.fy = e.y; e.x += dx; e.y += dy; e.moving = true; e.t = 0; e.speed = speed || SPEED;
  }
  function tryMove(dir) {
    const p = W.player;
    if (p.moving || W.busy) return;
    p.dir = dir;
    const [dx, dy] = DIRS[dir];
    const nx = p.x + dx, ny = p.y + dy;
    if (!free(nx, ny)) {
      const n = npcAt(nx, ny);
      if (n && n.move === 'bob') { W.autoPath = null; talkTo(n); }
      else if (!p.bumped) { Audio.sfx('bump'); p.bumped = true; }
      return;
    }
    p.bumped = false;
    // followers take the place of whoever walks ahead of them
    let prev = { x: p.x, y: p.y };
    W.followers.forEach(f => {
      const cur = { x: f.x, y: f.y };
      if (cur.x !== prev.x || cur.y !== prev.y) {
        const ddx = prev.x - f.x, ddy = prev.y - f.y;
        const d = ddx > 0 ? 'right' : ddx < 0 ? 'left' : ddy > 0 ? 'down' : 'up';
        if (Math.abs(ddx) + Math.abs(ddy) === 1) startStep(f, d);
        else { f.x = prev.x; f.y = prev.y; f.px = f.x * T; f.py = f.y * T; }
      }
      prev = cur;
    });
    startStep(p, dir);
  }
  function advance(e, dt) {
    if (!e.moving) { e.frame = 1; return false; }
    e.t += dt * e.speed;
    if (e.t >= 1) {
      e.t = 1; e.moving = false; e.foot ^= 1;
      e.px = e.x * T; e.py = e.y * T; e.frame = 1;
      return true;
    }
    e.px = (e.fx + (e.x - e.fx) * e.t) * T;
    e.py = (e.fy + (e.y - e.fy) * e.t) * T;
    e.frame = e.t < 0.5 ? (e.foot ? 0 : 2) : 1;
    return false;
  }

  function update(dt) {
    W.time += dt;
    const p = W.player;
    W.followers.forEach(f => advance(f, dt));
    updateNpcs(dt);
    if (!G.map) return;
    const arrived = advance(p, dt);
    if (arrived) {
      if (onArrive()) return;
    }
    if (!p.moving && G.mode === 'map' && !W.busy) {
      const dir = Input.dir();
      if (dir) { W.autoPath = null; W.pendingInteract = null; tryMove(dir); }
      else if (W.autoPath && W.autoPath.length) {
        const nxt = W.autoPath[0];
        if (!free(nxt[0], nxt[1])) {
          const alt = W.autoGoal && bfs([p.x, p.y], W.autoGoal);
          if (alt && alt.length && (alt[0][0] !== nxt[0] || alt[0][1] !== nxt[1])) W.autoPath = alt;
          else if ((W.autoWait += dt) > 1.6) { W.autoPath = null; W.pendingInteract = null; }
        } else {
          W.autoPath.shift(); W.autoWait = 0;
          tryMove(dirTo(nxt[0], nxt[1]));
          if (!p.moving) W.autoPath = null;
        }
      } else if (W.pendingInteract) {
        const t = W.pendingInteract;
        const tx = t.npc ? t.npc.x : t.x, ty = t.npc ? t.npc.y : t.y;
        if (Math.abs(tx - p.x) + Math.abs(ty - p.y) === 1) { W.pendingInteract = null; p.dir = dirTo(tx, ty); interact(); }
        else if (t.npc && (t.tries = (t.tries || 0) + 1) < 4) goTo(tx, ty, t);
        else W.pendingInteract = null;
      }
    }
    updateCamera();
  }

  function updateNpcs(dt) {
    W.npcs.forEach(n => {
      advance(n, dt);
      if (n.move !== 'wander' || n.moving || G.mode !== 'map' || !npcVisible(n)) return;
      if (W.pendingInteract && W.pendingInteract.npc === n) return;
      n.wait -= dt;
      if (n.wait > 0) return;
      n.wait = 1.5 + Math.random() * 3;
      const dirs = ['up', 'down', 'left', 'right'];
      const d = dirs[Math.floor(Math.random() * 4)];
      const [dx, dy] = DIRS[d];
      const nx = n.x + dx, ny = n.y + dy;
      const r = n.radius || 2;
      if (Math.abs(nx - n.hx) > r || Math.abs(ny - n.hy) > r) { n.dir = d; return; }
      if (free(nx, ny, true)) startStep(n, d, 2.6); else n.dir = d;
    });
  }

  function onArrive() {
    const p = W.player, m = G.map;
    for (const w of m.warps || []) {
      if (p.x >= w.x && p.x < w.x + (w.w || 1) && p.y >= w.y && p.y < w.y + (w.h || 1)) {
        W.autoPath = null;
        if (evalCond(w.cond)) { warp(w.to, w.tx, w.ty, w.dir); return true; }
        if (w.deny) { Script.run(w.deny, () => pushBack()); return true; }
      }
    }
    for (const e of m.events || []) {
      if (e.trigger !== 'step') continue;
      const w = e.w || 1, h = e.h || 1;
      if (p.x >= e.x && p.x < e.x + w && p.y >= e.y && p.y < e.y + h && evalCond(e.cond)) {
        W.autoPath = null;
        const sc = e.pages ? pickPage(e.pages) : e.scene;
        if (sc) { Script.run(sc, e.push ? () => pushBack() : null); return true; }
      }
    }
    return false;
  }
  function pushBack() {
    const p = W.player;
    const back = OPP[p.dir];
    const [dx, dy] = DIRS[back];
    if (!blocked(p.x + dx, p.y + dy)) { startStep(p, back, 7); p.dir = OPP[back]; }
  }

  /* ---------------- interaction ---------------- */
  function facing() {
    const p = W.player; const [dx, dy] = DIRS[p.dir];
    return [p.x + dx, p.y + dy];
  }
  function talkTo(n) {
    if (n.move !== 'bob' && n.sprite.indexOf('m_') !== 0) n.dir = OPP[W.player.dir];
    const sc = pickPage(n.pages);
    if (sc) Script.run(sc);
  }
  function interact() {
    if (W.player.moving || W.busy || Script.running) return;
    let [tx, ty] = facing();
    const m = G.map;
    const [dx, dy] = DIRS[W.player.dir];
    let n = npcAt(tx, ty);
    if (!n && inCells(m.talkover, tx, ty)) n = npcAt(tx + dx, ty + dy);
    if (n) { talkTo(n); return; }
    const c = chestAt(tx, ty);
    if (c) { openChest(c); return; }
    const s = spotAt(tx, ty);
    if (s) { search(s); return; }
    for (const e of m.events || []) {
      if (e.trigger !== 'talk') continue;
      const w = e.w || 1, h = e.h || 1;
      if (tx >= e.x && tx < e.x + w && ty >= e.y && ty < e.y + h && evalCond(e.cond)) {
        const sc = e.pages ? pickPage(e.pages) : e.scene;
        if (sc) { Script.run(sc); return; }
      }
    }
    if (G.party.length) Script.run(pickPage(PARTY_TALK));
  }
  function openChest(c) {
    const key = 'chest_' + c.id;
    if (G.opened[key]) { Script.runInline([{ t: 'narr', text: '宝箱是空的。' }]); return; }
    G.opened[key] = 1; Audio.sfx('chest');
    Script.runInline([{ t: 'narr', text: '打开了宝箱。' }, { t: 'give', item: c.item, n: c.count || 1 }]);
  }
  function search(s) {
    const key = 'spot_' + s.id;
    if (G.opened[key]) { Script.runInline([{ t: 'narr', text: `${s.label}里什么也没有。` }]); return; }
    G.opened[key] = 1;
    Script.runInline([{ t: 'narr', text: `你往${s.label}里摸了摸……` }, { t: 'give', item: s.item, n: s.count || 1 }]);
  }

  /* ---------------- tap to move ---------------- */
  function tapAt(cssX, cssY) {
    if (G.mode !== 'map' || W.busy || Script.running) return;
    const rect = W.canvas.getBoundingClientRect();
    const sx = (cssX - rect.left) * (W.canvas.width / rect.width) / W.scale;
    const sy = (cssY - rect.top) * (W.canvas.height / rect.height) / W.scale;
    const tx = Math.floor((sx + W.cam.x) / T), ty = Math.floor((sy + W.cam.y) / T);
    const p = W.player;
    if (tx === p.x && ty === p.y) { interact(); return; }
    const n = npcAt(tx, ty);
    const interactive = n || chestAt(tx, ty) || spotAt(tx, ty) ||
      (G.map.events || []).some(e => e.trigger === 'talk' && tx >= e.x && tx < e.x + (e.w || 1) && ty >= e.y && ty < e.y + (e.h || 1));
    if (!blocked(tx, ty) && !n) goTo(tx, ty, null);
    else if (interactive) {
      if (Math.abs(tx - p.x) + Math.abs(ty - p.y) === 1) { p.dir = dirTo(tx, ty); interact(); return; }
      goTo(tx, ty, { x: tx, y: ty, npc: n || null });
    }
  }
  function dirTo(tx, ty) {
    const p = W.player;
    return tx > p.x ? 'right' : tx < p.x ? 'left' : ty > p.y ? 'down' : 'up';
  }
  function goTo(tx, ty, pending) {
    const p = W.player;
    W.autoGoal = pending ? (x, y) => Math.abs(x - tx) + Math.abs(y - ty) === 1 : (x, y) => x === tx && y === ty;
    W.autoPath = bfs([p.x, p.y], W.autoGoal) || null;
    W.autoWait = 0;
    W.pendingInteract = W.autoPath || (pending && Math.abs(tx - p.x) + Math.abs(ty - p.y) === 1) ? pending : null;
    return W.autoPath ? W.autoPath.length : -1;
  }
  function bfs(start, goal) {
    const m = G.map, key = (x, y) => y * m.w + x;
    const prev = new Map([[key(start[0], start[1]), null]]);
    const q = [start];
    let found = null, steps = 0;
    while (q.length && steps < 6000) {
      steps++;
      const [x, y] = q.shift();
      if ((x !== start[0] || y !== start[1]) && goal(x, y)) { found = [x, y]; break; }
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx, ny = y + dy, k = key(nx, ny);
        if (prev.has(k) || blocked(nx, ny) || npcAt(nx, ny)) continue;
        prev.set(k, [x, y]); q.push([nx, ny]);
      }
    }
    if (!found) return null;
    const path = [];
    let cur = found;
    while (cur && (cur[0] !== start[0] || cur[1] !== start[1])) { path.unshift(cur); cur = prev.get(key(cur[0], cur[1])); }
    return path;
  }

  /* ---------------- rendering ---------------- */
  function updateCamera() {
    const m = G.map; if (!m) return;
    const p = W.player, mw = m.w * T, mh = m.h * T;
    let cx = p.px + 8 - W.bw / 2, cy = p.py + 8 - W.bh / 2;
    cx = mw <= W.bw ? -(W.bw - mw) / 2 : Math.max(0, Math.min(mw - W.bw, cx));
    cy = mh <= W.bh ? -(W.bh - mh) / 2 : Math.max(0, Math.min(mh - W.bh, cy));
    W.cam.x = Math.round(cx); W.cam.y = Math.round(cy);
  }
  function blitLayer(im) {
    if (!im) return;
    const b = W.b, cx = W.cam.x, cy = W.cam.y;
    const sx = Math.max(0, cx), sy = Math.max(0, cy);
    const dx = sx - cx, dy = sy - cy;
    const w = Math.min(im.width - sx, W.bw - dx), h = Math.min(im.height - sy, W.bh - dy);
    if (w > 0 && h > 0) b.drawImage(im, sx, sy, w, h, dx, dy, w, h);
  }
  function drawEntity(e, sheet) {
    const im = img(sheetOf(sheet));
    if (!im) return;
    const b = W.b;
    const x = Math.round(e.px) - W.cam.x, y = Math.round(e.py) - W.cam.y;
    b.fillStyle = 'rgba(0,0,0,0.28)';
    b.beginPath(); b.ellipse(x + 8, y + 14, 6, 2.5, 0, 0, Math.PI * 2); b.fill();
    if (im.width < FW * 3) {
      const bob = Math.round(Math.sin(W.time * 3.2 + e.x) * 1.5);
      b.drawImage(im, x + 8 - Math.floor(im.width / 2), y + 16 - im.height + bob);
      return;
    }
    b.drawImage(im, e.frame * FW, ROW[e.dir] * FH, FW, FH, x + 8 - 13, y - 22, FW, FH);
  }
  function render() {
    const b = W.b, m = G.map;
    b.fillStyle = '#000'; b.fillRect(0, 0, W.bw, W.bh);
    if (!m) { flush(); return; }
    blitLayer(img(m.img));
    drawWater();
    const sortables = [];
    for (const d of m.decals || []) {
      if (!decalVisible(d)) continue;
      const im = img(d.img); if (!im) continue;
      const dx = d.x * T + (d.ox || 0) - W.cam.x, dy = d.y * T + (d.oy || 0) - W.cam.y;
      if (d.layer === 'sort') sortables.push({ y: d.y * T + 15, draw: () => b.drawImage(im, dx, dy) });
      else b.drawImage(im, dx, dy);
    }
    for (const c of m.chests || []) {
      const im = img(G.opened['chest_' + c.id] ? 'assets/maps/chest_open.png' : 'assets/maps/chest.png');
      if (im) sortables.push({ y: c.y * T + 15, draw: () => b.drawImage(im, c.x * T - W.cam.x, c.y * T - W.cam.y) });
    }
    for (const a of m.anims || []) {
      if (a.kind === 'wheel') {
        const im = img('assets/maps/wheel.png'); if (!im) continue;
        const f = evalCond(a.spin) ? Math.floor(W.time * 7) % 4 : 0;
        sortables.push({ y: (a.y + 1) * T + 15, draw: () => b.drawImage(im, f * 28, 0, 28, 32, a.x * T - 6 - W.cam.x, a.y * T - W.cam.y, 28, 32) });
      } else if (a.kind === 'core' && evalCond(a.lit)) {
        const im = img('assets/maps/core_anim.png'); if (!im) continue;
        const f = 3 + Math.floor(W.time * 5) % 3;
        sortables.push({ y: a.y * T + 15, draw: () => b.drawImage(im, f * 32, 0, 32, 64, a.x * T - 8 - W.cam.x, a.y * T - 48 - W.cam.y, 32, 64) });
      }
    }
    W.npcs.forEach(n => { if (npcVisible(n)) sortables.push({ y: n.py + 15, draw: () => drawEntity(n, n.sprite) }); });
    W.followers.slice().reverse().forEach(f => sortables.push({ y: f.py + 14.5, draw: () => drawEntity(f, f.id) }));
    const p = W.player;
    sortables.push({ y: p.py + 15.2, draw: () => drawEntity(p, 'hero') });
    sortables.sort((a, c) => a.y - c.y).forEach(s => s.draw());
    if (m.fg) blitLayer(img(m.fg));
    drawLight();
    flush();
  }
  function drawWater() {
    const m = G.map; if (!m.water || !m.water.length) return;
    const b = W.b, t = W.time;
    b.fillStyle = 'rgba(220,240,255,0.85)';
    const x0 = Math.floor(W.cam.x / T) - 1, y0 = Math.floor(W.cam.y / T) - 1, x1 = x0 + W.bw / T + 2, y1 = y0 + W.bh / T + 2;
    for (const [x, y] of m.water) {
      if (x < x0 || x > x1 || y < y0 || y > y1) continue;
      for (let k = 0; k < 2; k++) {
        const ph = hash(x, y, k) * 6.28, s = Math.sin(t * 1.6 + ph);
        if (s > 0.82) {
          const px = x * T + Math.floor(hash(x, y, k + 7) * 12) + 2 - W.cam.x, py = y * T + Math.floor(hash(x, y, k + 9) * 12) + 2 - W.cam.y;
          b.fillRect(px, py, s > 0.93 ? 3 : 2, 1);
        }
      }
    }
  }
  function drawLight() {
    const m = G.map, b = W.b;
    const night = G.flags.night || m.night;
    if (night) {
      b.globalCompositeOperation = 'multiply';
      b.fillStyle = 'rgb(92,104,170)'; b.fillRect(0, 0, W.bw, W.bh);
      b.globalCompositeOperation = 'source-over';
    }
    const dark = m.dark || 0;
    if (dark > 0) {
      const lc = W.lightCanvas.getContext('2d');
      lc.globalCompositeOperation = 'source-over';
      lc.clearRect(0, 0, W.bw, W.bh);
      lc.fillStyle = `rgba(4,4,12,${Math.min(0.97, dark + (dark >= 1 ? 0 : 0.15))})`;
      lc.fillRect(0, 0, W.bw, W.bh);
      const p = W.player;
      const cx = p.px + 8 - W.cam.x, cy = p.py + 4 - W.cam.y;
      const hasLamp = (G.items.lantern || 0) > 0;
      const r = dark >= 1 ? (hasLamp ? 46 : 30) : (hasLamp ? 92 : 62);
      const flick = 1 + Math.sin(W.time * 9) * 0.02;
      const g = lc.createRadialGradient(cx, cy, r * 0.25, cx, cy, r * flick);
      g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(0.7, 'rgba(0,0,0,0.75)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      lc.globalCompositeOperation = 'destination-out';
      lc.fillStyle = g; lc.beginPath(); lc.arc(cx, cy, r * flick, 0, Math.PI * 2); lc.fill();
      lc.globalCompositeOperation = 'source-over';
      b.drawImage(W.lightCanvas, 0, 0);
      if (hasLamp) {
        b.globalCompositeOperation = 'lighter';
        const g2 = b.createRadialGradient(cx, cy, 2, cx, cy, r * 0.8);
        g2.addColorStop(0, 'rgba(90,60,10,0.25)'); g2.addColorStop(1, 'rgba(0,0,0,0)');
        b.fillStyle = g2; b.fillRect(cx - r, cy - r, r * 2, r * 2);
        b.globalCompositeOperation = 'source-over';
      }
    }
  }
  function flush() {
    const c = W.ctx;
    c.imageSmoothingEnabled = false;
    c.drawImage(W.buf, 0, 0, W.bw, W.bh, 0, 0, W.bw * W.scale, W.bh * W.scale);
  }

  function pathTo(tx, ty, face) {
    const n = npcAt(tx, ty);
    if (!blocked(tx, ty) && !n) return goTo(tx, ty, null);
    return goTo(tx, ty, face ? { x: tx, y: ty, npc: n || null } : null);
  }
  return Object.assign(W, { init, resize, load, warp, update, render, interact, tapAt, runAuto, npcVisible, facing, pushBack, pathTo });
})();

const PARTY_TALK = [
  ['c5_trapdoor_open & !c5_boss_won', 'p_c5_under'],
  ['c5_home & !c5_grave_done', 'p_c5_home'],
  ['c5_home & !c5_ister_done', 'p_c5_forest'],
  ['c4_letter_opened & !c4_pebble_known', 'p_c4_deca'],
  ['c4_backup_deleted & !c4_sera_restored', 'p_c4_sera2'],
  ['c4_wall_done & !c4_backup_deleted', 'p_c4_backup'],
  ['c4_chloe_ran & !c4_wall_done', 'p_c4_find'],
  ['c4_deca_met & !c4_sentinel_won', 'p_c4_archive'],
  ['c4_sera_met & !c4_deca_met', 'p_c4_sera'],
  ['c4_arrived & !c4_sera_met', 'p_c4_arrive'],
  ['c3_otto_watch & c3_marta_jug & c3_poem_got & !c3_night_done', 'p_c3_night'],
  ['c3_clock_restarted & !c3_night_done', 'p_c3_after'],
  ['c3_tower_open & !c3_clock_restarted', 'p_c3_tower'],
  ['c3_otto_done & !item:pendulum & !c3_tower_open', 'p_c3_bob'],
  ['c3_arrived & !c3_otto_done', 'p_c3_otto'],
  ['c2_done & !c3_arrived', 'p_c3_road'],
  ['c2_bridge_started & !c2_bridge_done', 'p_c2_bridge'],
  ['c2_hof_ill & !c2_bridge_started', 'p_c2_hof'],
  ['c2_ister_done & !c2_hof_ill', 'p_c2_ister'],
  ['c2_gate_done & !c2_met_ister', 'p_c2_forest'],
  ['c1_tin_joined & !c1_night_done', 'p_c1_night'],
  ['c1_quest_tin & !c1_tin_joined', 'p_c1_tin'],
  [null, 'p_default'],
];
