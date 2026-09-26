"""Reproduce 'black screen when leaving a building' with real arrow keys, a slow network, and one failed image request."""
import sys, time
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://fanshaoliu.github.io/holzwege/'
SLOW = '--slow' in sys.argv
LAG = '--lag' in sys.argv
FAIL = '--fail-village' in sys.argv
PROXY = {'server': 'http://star-proxy.oa.com:3128'} if URL.startswith('https://') else None
KEY = {'up': 'ArrowUp', 'down': 'ArrowDown', 'left': 'ArrowLeft', 'right': 'ArrowRight'}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(proxy=PROXY) if PROXY else p.chromium.launch()
        ctx = b.new_context(viewport={'width': 960, 'height': 640})
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append('pageerror ' + str(e)))
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') and 'AudioContext' not in m.text else None)
        failed_once = {'done': False}
        if FAIL:
            def route(r):
                if 'maps/village' in r.request.url and not failed_once['done']:
                    failed_once['done'] = True
                    return r.abort()
                return r.continue_()
            pg.route('**/*', route)
        pg.goto(URL, timeout=180000, wait_until='domcontentloaded')
        pg.wait_for_function("typeof G !== 'undefined' && G.mode === 'title'", timeout=180000)
        if LAG:
            cdp = ctx.new_cdp_session(pg)
            cdp.send('Network.enable')
            cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 1500, 'downloadThroughput': 150 * 1024, 'uploadThroughput': 50 * 1024})
        if SLOW:
            cdp = ctx.new_cdp_session(pg)
            cdp.send('Network.enable')
            cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 400, 'downloadThroughput': 60 * 1024, 'uploadThroughput': 30 * 1024})
            cdp.send('Network.setCacheDisabled', {'cacheDisabled': False})

        def state():
            return pg.evaluate("[G.mode, G.mapId, World.player.x, World.player.y, World.busy, +getComputedStyle($('fade')).opacity, Script.running, !$('namebox').classList.contains('hidden')]")

        def advance_until_map(limit=400):
            for _ in range(limit):
                st = state()
                if st[7]:
                    pg.click('#name-ok'); pg.wait_for_timeout(200); continue
                if st[0] == 'map' and not st[6] and not st[4] and st[5] < 0.05:
                    return st
                if st[0] in ('scene',) and not st[4]:
                    pg.keyboard.press('z')
                pg.wait_for_timeout(120)
            return state()

        def walk_keys(tx, ty, face=False):
            n = pg.evaluate(f"(World.pathTo({tx},{ty},{str(face).lower()}), World.autoPath ? World.autoPath.slice() : [])")
            pg.evaluate("World.autoPath = null; World.pendingInteract = null")
            for (x, y) in n:
                px, py = pg.evaluate("[World.player.x, World.player.y]")
                d = 'right' if x > px else 'left' if x < px else 'down' if y > py else 'up'
                pg.keyboard.down(KEY[d])
                t0 = time.time()
                while time.time() - t0 < 3:
                    cx, cy, mv, mid = pg.evaluate("[World.player.x, World.player.y, World.player.moving, G.mapId]")
                    if (cx, cy) != (px, py) or mid is None:
                        break
                    pg.wait_for_timeout(30)
                pg.keyboard.up(KEY[d])
                pg.wait_for_timeout(60)
                st = state()
                if st[4] or st[0] != 'map':
                    return 'interrupted'
            if face:
                px, py = pg.evaluate("[World.player.x, World.player.y]")
                d = 'right' if tx > px else 'left' if tx < px else 'down' if ty > py else 'up'
                pg.keyboard.press(KEY[d]); pg.wait_for_timeout(250)
                pg.keyboard.press('z')
            return 'ok'

        pg.keyboard.press('z')
        st = advance_until_map()
        print('in attic:', st)
        walk_keys(7, 2)
        t_warp = time.time()
        st = advance_until_map()
        print(f'workshop after {time.time() - t_warp:.1f}s:', st)
        walk_keys(5, 4, face=True)
        st = advance_until_map()
        print('after Hof:', st, 'items:', pg.evaluate('G.items'))
        # walk out of the door with arrow keys and watch the transition
        walk_keys(6, 8)
        pg.keyboard.down('ArrowDown')
        t0 = time.time(); shots = 0; timeline = []
        while time.time() - t0 < 40:
            st = state()
            timeline.append((round(time.time() - t0, 1), st[1], st[4], round(st[5], 2), st[0]))
            if st[1] == 'village' and not st[4] and st[5] < 0.05:
                break
            if shots < 4 and time.time() - t0 > shots * 1.5:
                pg.screenshot(path=f'/tmp/ui/door_{shots}.png'); shots += 1
            pg.wait_for_timeout(250)
        pg.keyboard.up('ArrowDown')
        dt = time.time() - t0
        print(f'door transition took {dt:.1f}s; last:', timeline[-1])
        print('timeline sample:', timeline[::4][:12])
        pg.wait_for_timeout(800)
        pg.screenshot(path='/tmp/ui/door_after.png')
        print('village bg loaded:', pg.evaluate("!!img(G.map.img)"), 'fg:', pg.evaluate("G.map.fg ? !!img(G.map.fg) : 'none'"))
        # do the arrow keys respond now?
        x0 = pg.evaluate("[World.player.x, World.player.y]")
        pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(700); pg.keyboard.up('ArrowRight'); pg.wait_for_timeout(300)
        print('arrow right moved from', x0, 'to', pg.evaluate("[World.player.x, World.player.y]"))
        print('errors:', errs[:8])
        b.close()


main()
