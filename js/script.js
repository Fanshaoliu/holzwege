'use strict';
/* Scene interpreter for the compiled screenplay. */
const Script = (() => {
  const ABORT = { abort: true };
  const ENDED = { ended: true };
  const S = { running: false };

  function give(id, n) {
    G.items[id] = (G.items[id] || 0) + (n || 1);
  }
  function unlockCodex(id) {
    const e = window.CODEX.find(c => c.id === id);
    if (!e) return;
    const fresh = !G.codex[id];
    G.codex[id] = 1;
    G.global.codex[id] = 1; saveGlobal();
    if (fresh) { Audio.sfx('codex'); UI.toast(`思想手记 · ${e.title}`); }
  }

  async function run(sceneId, after) {
    if (S.running || !sceneId) return;
    S.running = true;
    const prevMode = G.mode;
    G.mode = 'scene';
    let ended = false;
    try { await exec(sceneId); }
    catch (e) { if (e === ENDED) ended = true; else if (e !== ABORT) console.error(e); }
    UI.hideDialog();
    S.running = false;
    if (ended) return;
    UI.cg('off');
    if (G.mode === 'scene') G.mode = 'map';
    if (after) after();
    if (!World.runAuto()) { /* nothing */ }
  }
  async function runInline(cmds) {
    if (S.running) return;
    S.running = true; G.mode = 'scene';
    try { await block(cmds); } catch (e) { if (e !== ABORT) console.error(e); }
    UI.hideDialog(); S.running = false; if (G.mode === 'scene') G.mode = 'map';
  }
  async function exec(id) {
    let cur = id;
    let guard = 0;
    while (cur && guard++ < 200) {
      const sc = window.STORY[cur];
      if (!sc) { console.warn('missing scene', cur); return; }
      cur = await block(sc.cmds);
    }
  }

  async function block(cmds) {
    for (const c of cmds) {
      switch (c.t) {
        case 'say': await UI.say(c); break;
        case 'narr': await UI.say({ text: c.text, narr: true }); break;
        case 'choice': {
          const opts = c.options.filter(o => evalCond(o.cond));
          const i = await UI.choose(opts);
          return opts[i].goto;
        }
        case 'goto': return c.id;
        case 'call': await exec(c.id); break;
        case 'if': {
          const r = await block(evalCond(c.cond) ? c.then : c.else);
          if (r) return r;
          break;
        }
        case 'set': G.flags[c.k] = c.v; break;
        case 'give': {
          give(c.item, c.n);
          const it = window.ITEMS[c.item] || { name: c.item };
          Audio.sfx(c.item === 'coin' ? 'item' : 'fanfare');
          const extra = c.item === 'coin' ? `（现在有 ${G.items.coin} 枚）` : '';
          await UI.say({ narr: true, text: `${G.name}得到了【${it.name}】！${extra}` });
          break;
        }
        case 'take': G.items[c.item] = Math.max(0, (G.items[c.item] || 0) - (c.n || 1)); break;
        case 'codex': unlockCodex(c.id); break;
        case 'battle': {
          UI.hideDialog();
          const res = await Battle.start(c.id);
          if (res === 'win') {
            const B = window.BATTLES[c.id];
            G.flags['won_' + c.id] = 1;
            (B.codex || []).forEach(unlockCodex);
            if (B.post) await exec(B.post);
          } else {
            await UI.say({ narr: true, text: '你们先退开了一些。等想清楚了再来。' });
            World.pushBack();
            throw ABORT;
          }
          break;
        }
        case 'warp': UI.hideDialog(); await World.warp(c.map, c.x, c.y, c.dir, true); break;
        case 'fade': await UI.fade(c.mode); break;
        case 'music': Audio.play(c.name); break;
        case 'sfx': Audio.sfx(c.name); break;
        case 'wait': if (!window.AUTO) await sleep(c.ms); break;
        case 'show': G.flags[`show_${G.mapId}_${c.id}`] = 1; break;
        case 'hide': G.flags[`show_${G.mapId}_${c.id}`] = -1; break;
        case 'party':
          if (c.op === 'add') {
            if (!G.party.includes(c.id)) G.party.push(c.id);
            G.flags[`show_${G.mapId}_${c.id}`] = -1;
            await loadImage(`assets/chars/${c.id}.png`);
            const p = World.player;
            World.followers = G.party.map(id => {
              const old = World.followers.find(f => f.id === id);
              return old || { id, x: p.x, y: p.y, px: p.x * T, py: p.y * T, dir: p.dir, moving: false, t: 0, fx: p.x, fy: p.y, foot: 0, frame: 1 };
            });
          } else {
            G.party = G.party.filter(x => x !== c.id);
            World.followers = World.followers.filter(f => f.id !== c.id);
          }
          break;
        case 'cg': UI.cg(c.name); break;
        case 'shake': UI.shake(); break;
        case 'flash': UI.flash(); break;
        case 'night': G.flags.night = c.on ? 1 : 0; break;
        case 'title': UI.hideDialog(); await UI.titleCard(c.text); break;
        case 'name': UI.hideDialog(); await UI.askName(); break;
        case 'heal': break;
        case 'end': return null;
        case 'ending':
          UI.hideDialog();
          await Main.ending(c.n);
          throw ENDED;
        case 'face': {
          const n = World.npcs.find(x => x.id === c.id); if (n) n.dir = c.dir; break;
        }
        default: break;
      }
    }
    return null;
  }

  return { run, runInline, exec, get running() { return S.running; }, unlockCodex, give };
})();
