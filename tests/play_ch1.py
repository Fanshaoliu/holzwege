"""Play chapter 1 (and the start of chapter 2) with real movement and interaction."""
import sys, time
from playwright.sync_api import sync_playwright
URL = 'http://127.0.0.1:8792/index.html'

def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 960, 'height': 640})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto(URL); pg.wait_for_timeout(1500)
        pg.evaluate("localStorage.clear()")
        pg.reload(); pg.wait_for_timeout(1500)
        pg.evaluate("G.settings.speed = 3")

        def advance(limit=400):
            n = 0
            while n < limit:
                st = pg.evaluate("[G.mode, Script.running, !!UI.nav, !$('namebox').classList.contains('hidden'), Battle.waiting]")
                mode, running, nav, namebox, bwait = st
                if namebox:
                    pg.click('#name-ok'); pg.wait_for_timeout(100); n += 1; continue
                if mode in ('map',) and not running:
                    return n
                pg.keyboard.press('z'); pg.wait_for_timeout(60); n += 1
            return n

        def walk(x, y, face=False, timeout=25):
            m0 = pg.evaluate("G.mapId")
            for attempt in range(4):
                pg.evaluate(f"World.pathTo({x},{y},{str(face).lower()})")
                t0 = time.time()
                while time.time() - t0 < timeout:
                    st = pg.evaluate("[World.autoPath ? World.autoPath.length : 0, World.player.moving, G.mode, !!World.pendingInteract, World.busy, Script.running, G.mapId, World.player.x, World.player.y]")
                    if st[5] or st[2] != 'map':
                        return 'scene'
                    if st[6] != m0:
                        return 'warped'
                    if st[0] == 0 and not st[1] and not st[3] and not st[4]:
                        break
                    pg.wait_for_timeout(80)
                px, py = pg.evaluate("[World.player.x, World.player.y]")
                if (px, py) == (x, y) or (face and abs(px-x)+abs(py-y) == 1):
                    return 'arrived'
                pg.wait_for_timeout(400)
            print('   !! walk failed to', (x, y), 'at', at())
            return 'failed'

        def talk(tx, ty):
            r = walk(tx, ty, face=True)
            pg.wait_for_timeout(300)
            return advance()

        def at():
            return pg.evaluate("[G.mapId, World.player.x, World.player.y]")

        def flags():
            return pg.evaluate("G.flags")

        pg.keyboard.press('z'); pg.wait_for_timeout(400)   # new game
        advance()
        print('after intro:', at(), flags())
        walk(7, 2); pg.wait_for_timeout(800); advance()
        print('workshop?', at())
        talk(5, 4); print('hammer:', pg.evaluate("G.items"))
        walk(6, 9); pg.wait_for_timeout(900); advance()
        print('village?', at())
        talk(31, 11); print('hans:', flags().get('c1_hans_talked'))
        walk(14, 23); pg.wait_for_timeout(900); advance(); print('tavern?', at())
        pg.evaluate("World.pathTo(3,4,false)"); walk(3, 4); pg.evaluate("World.player.dir='up'"); pg.keyboard.press('z'); pg.wait_for_timeout(200); advance()
        print('molly:', flags().get('c1_knows_chief'))
        walk(6, 9); pg.wait_for_timeout(900); advance()
        px, py = pg.evaluate("(()=>{const n=World.npcs.find(n=>n.id==='pip'); return [n.x,n.y]})()")
        talk(px, py); print('pip:', flags().get('c1_knows_plank'))
        walk(23, 23); pg.wait_for_timeout(900); advance(); print('chief?', at())
        talk(5, 4); print('key:', pg.evaluate("G.items.sluice_key"))
        walk(5, 8); pg.wait_for_timeout(900); advance()
        walk(33, 3); pg.evaluate("World.player.dir='right'"); pg.keyboard.press('z'); pg.wait_for_timeout(200); advance()
        print('plank:', flags().get('c1_plank_fixed'))
        walk(32, 3); pg.evaluate("World.player.dir='up'"); pg.keyboard.press('z'); pg.wait_for_timeout(200); advance()
        print('sluice:', flags().get('c1_sluice_open'))
        talk(31, 11); print('broke:', flags().get('c1_hammer_broke'), pg.evaluate("G.items"))
        px, py = pg.evaluate("(()=>{const n=World.npcs.find(n=>n.id==='pip'); return [n.x,n.y]})()")
        talk(px, py); print('head:', pg.evaluate("G.items.hammer_head"))
        walk(6, 8); pg.wait_for_timeout(900); advance()
        talk(5, 4); print('fixed:', flags().get('c1_hammer_fixed'))
        walk(6, 9); pg.wait_for_timeout(900); advance()
        talk(31, 11); print('mill done:', flags().get('c1_mill_done'))
        walk(20, 12); advance(); print('chloe arrived:', flags().get('c1_chloe_arrived'), pg.evaluate("G.party"))
        walk(7, 12); walk(4, 13); pg.evaluate("World.player.dir='left'"); pg.keyboard.press('z'); pg.wait_for_timeout(200); advance()
        print('tin:', flags().get('c1_tin_joined'), pg.evaluate("G.party"))
        pg.screenshot(path='/tmp/shots/ch1_party.png')
        walk(6, 8); pg.wait_for_timeout(1200); advance(); pg.wait_for_timeout(800); advance()
        print('night/morning:', flags().get('c1_night_done'), flags().get('c1_done'), flags().get('ch'), at())
        walk(6, 9); pg.wait_for_timeout(900); advance()
        walk(21, 0); pg.wait_for_timeout(1500); advance()
        print('forest:', at(), flags().get('c2_gate_done'))
        pg.screenshot(path='/tmp/shots/ch2_forest.png')
        print('codex:', list(pg.evaluate("G.codex").keys()))
        print('errors:', errs[:10])
        b.close()

main()
