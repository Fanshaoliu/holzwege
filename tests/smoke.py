"""Headless smoke test: load the game, walk through the opening, capture console errors and screenshots."""
import sys
import time
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8792/index.html'
OUT = '/tmp/shots'


def run(viewport, name, mobile=False):
    import os
    os.makedirs(OUT, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = b.new_context(viewport=viewport, device_scale_factor=2 if mobile else 1, has_touch=mobile, is_mobile=mobile)
        pg = ctx.new_page()
        pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        pg.goto(URL)
        pg.wait_for_timeout(2500)
        pg.screenshot(path=f'{OUT}/{name}_title.png')
        # new game
        pg.keyboard.press('z')           # 开始新的旅程 is selected unless an auto save exists
        pg.wait_for_timeout(600)
        for i in range(12):
            pg.keyboard.press('z'); pg.wait_for_timeout(250)
        pg.screenshot(path=f'{OUT}/{name}_intro.png')
        # name box
        if pg.is_visible('#namebox'):
            pg.fill('#name-input', '林恩')
            pg.click('#name-ok')
        pg.wait_for_timeout(500)
        for i in range(10):
            pg.keyboard.press('z'); pg.wait_for_timeout(300)
        pg.screenshot(path=f'{OUT}/{name}_dream.png')
        for i in range(12):
            pg.keyboard.press('z'); pg.wait_for_timeout(300)
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f'{OUT}/{name}_attic.png')
        print(name, 'mode=', pg.evaluate('G.mode'), 'map=', pg.evaluate('G.mapId'), 'flags=', pg.evaluate('JSON.stringify(G.flags)'))
        b.close()
    return errors


if __name__ == '__main__':
    e1 = run({'width': 1280, 'height': 720}, 'desk')
    e2 = run({'width': 390, 'height': 844}, 'phone', mobile=True)
    for e in (e1 + e2)[:40]:
        print(e)
