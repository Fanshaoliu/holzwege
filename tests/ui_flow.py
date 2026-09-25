"""Menus, codex, save/load, an ending with credits, and phone-sized battle/menu screenshots."""
import os
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8792/index.html'
OUT = '/tmp/ui'
os.makedirs(OUT, exist_ok=True)
SETUP = """async () => {
  UI.hideTitle();
  G.party = ['chloe','tin'];
  Object.assign(G.items, {hammer:1, lantern:1, jug:1, poem:1, photo:1, forest_map:1, coin:7});
  Object.assign(G.codex, {seinsfrage:1, dasein:1, zuhanden:1, bewandtnis:1, welt:1, mitsein:1, gerede:1, dasman:1, angst:1});
  Object.assign(G.flags, {ch:2, c1_done:1});
  await World.load('village', 20, 16, 'down'); G.mode = 'map';
}"""


def run(vp, tag):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport=vp, has_touch=tag == 'phone', is_mobile=tag == 'phone')
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto(URL); pg.wait_for_timeout(1500)
        pg.evaluate("localStorage.clear()")
        pg.evaluate(SETUP)
        key = lambda k, t=160: (pg.keyboard.press(k), pg.wait_for_timeout(t))
        shot = lambda n: pg.screenshot(path=f'{OUT}/{tag}_{n}.png')

        key('m'); shot('menu')
        key('z'); shot('items'); key('x')
        key('ArrowDown'); key('z'); shot('codex'); key('z'); shot('codex_view'); key('x'); key('x')
        pg.evaluate("UI.openMenu && G.mode === 'map' ? UI.openMenu() : 0")
        for _ in range(3): key('ArrowDown', 60)
        key('z'); key('z', 400); shot('saved'); key('x'); key('x')
        pg.evaluate("G.mode === 'menu' ? UI.navBack() : 0")
        saved = pg.evaluate("!!localStorage.getItem('holzwege.slot1')")
        print(tag, 'slot1 saved:', saved, 'mode:', pg.evaluate('G.mode'))

        pg.evaluate("Main.toTitle()"); pg.wait_for_timeout(600); shot('title')
        pg.evaluate("G.flags = {}; G.items = {}")
        labels = pg.evaluate("[...document.querySelectorAll('#title-menu .opt')].map(b => b.textContent)")
        print(tag, 'title menu:', labels)
        for _ in range(8):
            if pg.evaluate("(document.querySelector('#title-menu .opt.sel') || {}).textContent") == '读取存档': break
            key('ArrowDown', 60)
        key('z', 300); shot('loadpanel')
        key('ArrowDown', 60); key('z', 1500)
        print(tag, 'after load:', pg.evaluate("[G.mode, G.mapId, World.player.x, World.player.y, G.flags.ch, Object.keys(G.items).length]"))

        if tag == 'phone':
            pg.evaluate("window.__res = null; Battle.start('wolf').then(r => window.__res = r); 0")
            pg.wait_for_timeout(1200); key('z', 400); key('z', 400); shot('battle')
            pg.evaluate("Script.runInline([{t:'say', who:'克洛伊', text:'本小姐可不是来陪你们散步的。先说好，钟楼上面我先上。'}]); 0")
            pg.wait_for_timeout(900); shot('dialog')
        else:
            pg.evaluate("G.flags.e3_path = 1; Script.run('e3_start'); 0")
            got = False
            for i in range(600):
                if pg.evaluate("!!UI.creditsSkip"):
                    got = True; break
                st = pg.evaluate("[G.mode, !!UI.nav]")
                key('z', 90)
            pg.wait_for_timeout(2500); shot('credits')
            print(tag, 'credits shown:', got)
            key('z', 1500); shot('title_after')
            print(tag, 'after credits:', pg.evaluate("[G.mode, JSON.stringify(G.global.endings)]"),
                  pg.evaluate("$('title-menu').textContent"))
        print(tag, 'errors:', errs[:8])
        b.close()


run({'width': 1280, 'height': 720}, 'desk')
run({'width': 390, 'height': 844}, 'phone')
