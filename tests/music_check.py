"""Check every music track: equal loop length per channel, sane pitch ranges, readable note names, and that it plays."""
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8792/index.html'
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(1500)
    lengths = pg.evaluate("Audio.check()")
    bad = 0
    for name, ch in lengths.items():
        vals = set(ch.values())
        ok = len(vals) == 1
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {name:11s} beats={ch}")
    info = pg.evaluate("""() => {
        const out = {};
        for (const [name, tr] of Object.entries(MUSIC.TRACKS)) {
            out[name] = {};
            for (const [k, src] of Object.entries(tr.ch)) {
                const ev = Audio.parseMML(src).filter(e => e.midi >= 0);
                if (!ev.length) continue;
                out[name][k] = { lo: Math.min(...ev.map(e => e.midi)), hi: Math.max(...ev.map(e => e.midi)), head: ev.slice(0, 14).map(e => e.midi) };
            }
        }
        return out;
    }""")
    nm = lambda m: f"{NAMES[m % 12]}{m // 12 - 1}"
    for name, ch in info.items():
        for k, v in ch.items():
            flag = '  <-- range?' if v['lo'] < 28 or v['hi'] > 96 else ''
            print(f"   {name:11s} {k:5s} {nm(v['lo'])}..{nm(v['hi'])}  {' '.join(nm(m) for m in v['head'])}{flag}")
    pg.keyboard.press('z')
    for name in lengths:
        n0 = len(errs)
        pg.evaluate(f"Audio.unlock(); Audio.play('{name}')")
        pg.wait_for_timeout(700)
        if len(errs) > n0:
            print('   play error', name, errs[n0:])
    pg.evaluate("Audio.play('none')")
    print('tracks with mismatched channel lengths:', bad, '| page errors:', errs[:5])
    b.close()
