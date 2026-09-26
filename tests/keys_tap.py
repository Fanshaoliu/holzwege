"""Walk only with quick key taps (keydown+keyup inside one frame), like a player tapping arrow keys."""
import time
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8792/index.html'
KEY = {'up': 'ArrowUp', 'down': 'ArrowDown', 'left': 'ArrowLeft', 'right': 'ArrowRight'}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 960, 'height': 640})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(1500)
    pg.evaluate("localStorage.clear()")

    def st():
        return pg.evaluate("[G.mode, G.mapId, World.player.x, World.player.y, World.player.dir, World.player.moving, World.busy, Script.running]")

    def settle(limit=300):
        for _ in range(limit):
            s = st()
            if not pg.evaluate("$('namebox').classList.contains('hidden')"):
                pg.click('#name-ok'); pg.wait_for_timeout(150); continue
            if s[0] == 'map' and not s[5] and not s[6] and not s[7]:
                return s
            if s[0] == 'scene':
                pg.keyboard.press('z')
            pg.wait_for_timeout(100)
        return st()

    def tap_to(tx, ty, face=None):
        path = pg.evaluate(f"(World.pathTo({tx},{ty},false), World.autoPath ? World.autoPath.slice() : [])")
        pg.evaluate("World.autoPath = null")
        for (x, y) in path:
            s = st()
            d = 'right' if x > s[2] else 'left' if x < s[2] else 'down' if y > s[3] else 'up'
            pg.keyboard.press(KEY[d])
            t0 = time.time()
            while time.time() - t0 < 2:
                s2 = st()
                if s2[1] != s[1] or ((s2[2], s2[3]) == (x, y) and not s2[5]):
                    break
                pg.wait_for_timeout(20)
            if s2[1] != s[1]:
                return 'warped'
        if face:
            pg.keyboard.press(KEY[face]); pg.wait_for_timeout(120)
        return 'ok'

    pg.keyboard.press('z')
    print('start:', settle())
    print('stairs:', tap_to(7, 2), settle())
    print('to Hof:', tap_to(5, 5, face='up'), st())
    pg.keyboard.press('z'); settle()
    print('hammer:', pg.evaluate('G.items.hammer'))
    print('door:', tap_to(6, 9), settle())
    # a tap given mid-step should still produce one step afterwards
    s0 = st()
    pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(40); pg.keyboard.up('ArrowRight')
    pg.wait_for_timeout(60)
    pg.keyboard.press('ArrowDown')
    pg.wait_for_timeout(900)
    s1 = st()
    print('mid-step tap:', (s0[2], s0[3]), '->', (s1[2], s1[3]), 'expected', (s0[2] + 1, s0[3] + 1))
    print('errors:', errs)
    b.close()
