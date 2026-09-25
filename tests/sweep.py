"""Run every scene in auto mode and load every map; report runtime errors; screenshot maps."""
import json, sys
from playwright.sync_api import sync_playwright
URL = 'http://127.0.0.1:8792/index.html'
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 960, 'height': 640})
    errs = []
    pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
    pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type == 'error' or 'missing' in m.text or 'cond error' in m.text else None)
    pg.goto(URL); pg.wait_for_timeout(2000)
    pg.evaluate("window.AUTO=true; window.AUTO_BATTLE=true;")
    ids = pg.evaluate("Object.keys(window.STORY)")
    bad = []
    for sid in ids:
        n0 = len(errs)
        r = pg.evaluate("""async (sid) => {
            try {
              if (!G.map) await World.load('village', 20, 20, 'down');
              G.mode = 'map';
              await Script.exec(sid);
              return 'ok';
            } catch (e) { return 'ERR ' + (e && e.message || JSON.stringify(e)); }
        }""", sid)
        if r != 'ok' or len(errs) > n0:
            bad.append((sid, r, errs[n0:]))
    print('scenes run:', len(ids), 'problems:', len(bad))
    for x in bad[:30]: print('  ', x)
    maps = pg.evaluate("Object.keys(window.MAPS)")
    import os; os.makedirs('/tmp/maps', exist_ok=True)
    pg.evaluate("window.AUTO=false")
    for mid in maps:
        n0 = len(errs)
        pos = pg.evaluate("""async (mid) => {
            const m = window.MAPS[mid];
            let x = Math.floor(m.w/2), y = Math.floor(m.h/2);
            const w = (m.warps||[])[0];
            if (w) { x = w.x; y = w.y; }
            await World.load(mid, x, y, 'down'); G.mode = 'map';
            World.render();
            return [x, y, m.npcs.length];
        }""", mid)
        pg.wait_for_timeout(250)
        pg.screenshot(path=f'/tmp/maps/{mid}.png')
        if len(errs) > n0: print('map err', mid, errs[n0:])
    print('maps loaded:', len(maps))
    print('\n'.join(errs[:20]))
    b.close()
