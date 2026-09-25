"""Phone: title panels, touch tap-to-move, D-pad, A button talk, dialog with portrait."""
from playwright.sync_api import sync_playwright
URL = 'http://127.0.0.1:8792/index.html'
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=2)
    pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(1800)
    # title -> codex panel via touch
    opts = pg.query_selector_all('#title-menu .opt')
    [o for o in opts if o.text_content().startswith('思想手记')][0].tap(); pg.wait_for_timeout(400)
    pg.screenshot(path='/tmp/ui/phone_title_codex.png')
    pg.query_selector('#panel .btn').tap(); pg.wait_for_timeout(300)
    pg.evaluate("""async () => { UI.hideTitle(); G.party=['chloe']; Object.assign(G.flags,{ch:2,c1_done:1}); await World.load('village', 20, 16, 'down'); G.mode='map'; $('menu-btn').classList.remove('hidden'); }""")
    pg.wait_for_timeout(300)
    box = pg.query_selector('#game').bounding_box()
    scale = pg.evaluate("World.scale / (window.devicePixelRatio||1)")
    cam = pg.evaluate("[World.cam.x, World.cam.y]")
    # tap on the tile 4 to the right, 2 down
    tx, ty = 24, 18
    cx = box['x'] + (tx * 16 - cam[0] + 8) * scale; cy = box['y'] + (ty * 16 - cam[1] + 8) * scale
    pg.touchscreen.tap(cx, cy); pg.wait_for_timeout(2500)
    print('tap-to-move ->', pg.evaluate("[World.player.x, World.player.y]"), 'target', (tx, ty))
    # D-pad: press left for a bit
    dp = pg.query_selector('#pad .dpad') or pg.query_selector('#dpad')
    bb = dp.bounding_box()
    pg.mouse.move(bb['x'] + bb['width'] * 0.15, bb['y'] + bb['height'] * 0.5)
    pg.dispatch_event('#pad .dpad, #dpad', 'pointerdown', {'clientX': bb['x'] + bb['width'] * 0.15, 'clientY': bb['y'] + bb['height'] * 0.5, 'pointerId': 1})
    pg.wait_for_timeout(700)
    pg.dispatch_event('#pad .dpad, #dpad', 'pointerup', {'pointerId': 1})
    pg.wait_for_timeout(400)
    print('dpad left ->', pg.evaluate("[World.player.x, World.player.y, World.player.dir]"))
    # talk to an NPC by tapping it
    n = pg.evaluate("(()=>{const p=World.player; const v=World.npcs.filter(n=>World.npcVisible(n)); v.sort((a,b)=>(Math.abs(a.x-p.x)+Math.abs(a.y-p.y))-(Math.abs(b.x-p.x)+Math.abs(b.y-p.y))); const n=v[0]; return [n.id,n.x,n.y]})()")
    print('npc', n)
    cam = pg.evaluate("[World.cam.x, World.cam.y]")
    cx = box['x'] + (n[1] * 16 - cam[0] + 8) * scale; cy = box['y'] + (n[2] * 16 - cam[1] + 8) * scale
    pg.touchscreen.tap(cx, cy); pg.wait_for_timeout(3500)
    print('talk ->', pg.evaluate("[G.mode, Script.running, document.querySelector('#dlg .name') ? document.querySelector('#dlg .name').textContent : $('dlg').textContent.slice(0,40)]"))
    pg.screenshot(path='/tmp/ui/phone_talk.png')
    print('errors', errs[:5])
    b.close()
