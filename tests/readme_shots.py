"""Capture the screenshots used in README.md into docs/screens/."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image

URL = 'http://127.0.0.1:8792/index.html'
OUT = 'docs/screens'
os.makedirs(OUT, exist_ok=True)


def save(pg, name, quant=True):
    path = f'{OUT}/{name}.png'
    pg.screenshot(path=path)
    if quant:
        im = Image.open(path).convert('RGB').quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(path, optimize=True)


def setup(pg, mid, x, y, d='down', party=('chloe', 'tin'), flags=None, extra=''):
    pg.evaluate("""async ([mid, x, y, d, party, flags]) => {
        UI.hideTitle(); G.party = party; Object.assign(G.flags, flags || {});
        Object.assign(G.items, {hammer:1, lantern:1, jug:1, poem:1, photo:1, forest_map:1, watch:1, bridge_nail:1});
        await World.load(mid, x, y, d); G.mode = 'map'; $('menu-btn').classList.remove('hidden');
        World.followers.forEach((f, i) => { f.y = y - 1 - i; f.py = f.y * 16; f.fy = f.y; f.dir = d; });
    }""", [mid, x, y, d, list(party), flags or {}])
    if extra: pg.evaluate(extra)
    pg.wait_for_timeout(900)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 960, 'height': 540})
    pg.goto(URL); pg.wait_for_timeout(2000)
    save(pg, 'title')

    setup(pg, 'village', 20, 15, 'down', flags={'ch': 2, 'c1_done': 1, 'c1_chloe_arrived': 1, 'c1_tin_joined': 1, 'show_village_chloe': -1, 'show_village_tin': -1})
    save(pg, 'village')

    setup(pg, 'village', 20, 15, 'down', flags={})
    pg.evaluate("Script.runInline([{t:'say', name:'克洛伊', who:'chloe', text:'这是什么地方的以太浓度？零点三？这种浓度也敢住人？坐标偏了足足三尺！'}]); 0")
    pg.wait_for_timeout(2600); save(pg, 'dialog')
    pg.keyboard.press('z'); pg.wait_for_timeout(400)

    setup(pg, 'harbor', 24, 16, 'up', flags={'ch': 3})
    pg.evaluate("window.__r = null; Battle.start('mask').then(r => window.__r = r); 0")
    pg.wait_for_timeout(1400); pg.keyboard.press('z'); pg.wait_for_timeout(700); pg.keyboard.press('z'); pg.wait_for_timeout(900)
    save(pg, 'battle')
    pg.evaluate("window.AUTO = true"); pg.wait_for_timeout(200)
    b.close()

    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 960, 'height': 540})
    pg.goto(URL); pg.wait_for_timeout(2000)
    setup(pg, 'forest', 26, 17, 'up', flags={'ch': 2, 'c2_gate_done': 1, 'c2_met_ister': 1})
    save(pg, 'forest')
    setup(pg, 'backup', 8, 6, 'up', flags={'ch': 4})
    save(pg, 'backup')
    pg.evaluate("Object.assign(G.codex, {dasein:1, zuhanden:1, dasman:1, angst:1, gestell:1})")
    pg.evaluate("UI.openMenu()"); pg.wait_for_timeout(200)
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('z'); pg.wait_for_timeout(300)
    for _ in range(3):
        pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(60)
    pg.keyboard.press('z'); pg.wait_for_timeout(500)
    save(pg, 'codex')
    b.close()

    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_timeout(2000)
    setup(pg, 'capital', 36, 18, 'up', flags={'ch': 4, 'c4_arrived': 1, 'c4_gest_met': 1})
    pg.evaluate("Script.runInline([{t:'say', name:'赛拉', who:'sera', text:'嗯。大家都挺好的。'}]); 0")
    pg.wait_for_timeout(2400)
    pg.screenshot(path=f'{OUT}/phone.png')
    im = Image.open(f'{OUT}/phone.png').convert('RGB')
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(f'{OUT}/phone.png', optimize=True)
    b.close()
print('saved', sorted(os.listdir(OUT)))
