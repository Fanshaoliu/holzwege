"""Story-graph solver: plays the game at the logic level (reachable maps, triggers, NPC pages)
until an ending, to catch soft-locks and broken flag chains in every chapter."""
import json, sys
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8792/index.html'

SOLVER = r"""
async (target) => {
  window.AUTO = true; window.AUTO_BATTLE = true;
  window.AUTO_CHOICE = (opts) => { const i = opts.findIndex(o => o.goto === target); return i >= 0 ? i : 0; };
  const idle = async () => { while (Script.running) await sleep(0); };
  const sig = () => JSON.stringify([G.flags, G.items, G.party, G.opened]);
  const warpsOf = {};
  const scan = (cmds, acc) => { for (const c of cmds || []) { if (c.t === 'warp') acc.add(c.map); if (c.t === 'if') { scan(c.then, acc); scan(c.else, acc); } } return acc; };
  const sceneWarps = (sid) => { if (!warpsOf[sid]) { const acc = new Set(); const seen = new Set(); let q = [sid];
      while (q.length) { const id = q.pop(); if (!id || seen.has(id)) continue; seen.add(id); const sc = window.STORY[id]; if (!sc) continue; scan(sc.cmds, acc);
        const walk = (cmds) => { for (const c of cmds || []) { if (c.t === 'goto' || c.t === 'call') q.push(c.id); if (c.t === 'if') { walk(c.then); walk(c.else); } } }; walk(sc.cmds); }
      warpsOf[sid] = [...acc]; } return warpsOf[sid]; };
  const vis = (mid, n) => { const f = G.flags[`show_${mid}_${n.id}`]; if (f === 1) return true; if (f === -1) return false; return evalCond(n.show); };
  const inRect = (e) => [e.x, e.y];
  function reachable() {
    const seen = [G.mapId], q = [G.mapId];
    const add = (to) => { if (window.MAPS[to] && !seen.includes(to)) { seen.push(to); q.push(to); } };
    while (q.length) {
      const mid = q.shift(), m = window.MAPS[mid];
      for (const w of m.warps || []) if (evalCond(w.cond)) add(w.to);
      for (const e of m.events || []) if (e.trigger === 'talk' && evalCond(e.cond)) { const sc = e.pages ? pickPage(e.pages) : e.scene; if (sc) sceneWarps(sc).forEach(add); }
    }
    return seen;
  }
  function collect() {
    const out = [];
    const maps = reachable();
    for (const pri of [0, 1, 2, 3]) for (const mid of maps) {
      const m = window.MAPS[mid];
      (m.events || []).forEach((e, i) => {
        const p = e.trigger === 'auto' ? 0 : e.trigger === 'step' ? 1 : 2;
        if (p !== pri || !evalCond(e.cond)) return;
        const sc = e.pages ? pickPage(e.pages) : e.scene;
        if (sc) out.push({ mid, x: e.x, y: e.y, scene: sc, label: `${e.trigger}:${mid}:${sc}` });
      });
      if (pri === 2) (m.npcs || []).forEach(n => {
        if (!vis(mid, n)) return;
        const sc = pickPage(n.pages || []);
        if (sc) out.push({ mid, x: n.x, y: n.y + 1, scene: sc, label: `npc:${mid}:${n.id}:${sc}` });
      });
      if (pri === 3) {
        (m.chests || []).forEach(c => { if (!G.opened['chest_' + c.id]) out.push({ mid, x: c.x, y: c.y + 1, chest: c, label: `chest:${mid}:${c.id}` }); });
        (m.spots || []).forEach(s => { if (!G.opened['spot_' + s.id]) out.push({ mid, x: s.x, y: s.y + 1, spot: s, label: `spot:${mid}:${s.id}` }); });
      }
    }
    if (G.party.length) { const sc = pickPage(PARTY_TALK); if (sc) out.push({ mid: G.mapId, x: World.player.x, y: World.player.y, scene: sc, label: `party:${sc}` }); }
    return out;
  }

  UI.hideTitle();
  Main.newGame();
  await sleep(50); await idle();
  const log = [], tried = new Set();
  for (let iter = 0; iter < 4000; iter++) {
    if (G.flags.ending) return { ok: true, ending: G.flags.ending, steps: log.length, log, codex: Object.keys(G.codex).length, flags: Object.keys(G.flags).length, missing: window.CODEX.filter(c => !G.codex[c.id]).map(c => c.id + "(" + c.title + ")") };
    const cands = collect();
    let moved = false;
    for (const c of cands) {
      const key = sig() + '|' + c.label;
      if (tried.has(key)) continue;
      tried.add(key);
      const before = sig();
      if (G.mapId !== c.mid) { await World.load(c.mid, c.x, c.y, 'down'); }
      G.mode = 'map';
      if (c.chest) { G.opened['chest_' + c.chest.id] = 1; Script.give(c.chest.item, c.chest.count || 1); }
      else if (c.spot) { G.opened['spot_' + c.spot.id] = 1; Script.give(c.spot.item, c.spot.count || 1); }
      else { Script.run(c.scene); await sleep(0); await idle(); }
      if (G.flags.ending) { log.push(c.label); break; }
      if (sig() !== before) { log.push(c.label); moved = true; break; }
    }
    if (G.flags.ending) continue;
    if (!moved) return { ok: false, stuck: true, steps: log.length, log, at: G.mapId, ch: G.flags.ch, cands: cands.map(c => c.label), flags: G.flags, items: G.items, party: G.party };
  }
  return { ok: false, reason: 'iter limit', log };
}
"""


def main():
    targets = sys.argv[1:] or ['e1_start', 'e2_start', 'e3_start']
    with sync_playwright() as p:
        b = p.chromium.launch()
        for tgt in targets:
            pg = b.new_page(viewport={'width': 960, 'height': 640})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') and 'AudioContext' not in m.text else None)
            pg.goto(URL); pg.wait_for_timeout(1500)
            pg.evaluate("localStorage.clear()")
            r = pg.evaluate(SOLVER, tgt)
            print(f'== {tgt}: ok={r.get("ok")} ending={r.get("ending")} steps={r.get("steps")} codex={r.get("codex")} flags={r.get("flags")}')
            if not r.get('ok'):
                print('  stuck at', r.get('at'), 'ch', r.get('ch'))
                print('  last steps:', r['log'][-15:])
                print('  candidates:', r.get('cands'))
                print('  party:', r.get('party'), 'items:', r.get('items'))
                print('  flags:', json.dumps(r.get('flags'), ensure_ascii=False))
            else:
                chap = [s for s in r['log'] if not s.startswith('party:') and not s.startswith('chest') and not s.startswith('spot')]
                if tgt == targets[0]:
                    print('  route:', ' | '.join(x.split(':', 2)[-1] if x.startswith(('auto', 'step', 'talk')) else x.split(':', 1)[-1] for x in chap))
            print('  codex missing:', r.get('missing'))
            print('  errors:', errs[:8])
            pg.close()
        b.close()


main()
