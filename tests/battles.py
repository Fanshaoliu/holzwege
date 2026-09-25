"""Fight every 心象对决 through the real battle UI with keyboard navigation."""
import time
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8792/index.html'

PLANS = {
    'slime':    ['追问'] * 3,
    'wolf':     ['动手'] * 3,
    'bat':      ['等待'] * 3,
    'mask':     ['动手'] * 3,
    'giant':    ['等待'] * 3 + ['眼下'] * 2,
    'sentinel': ['宝物:空壶', '宝物:诗人的残页', '宝物:霍夫的锤子'],
    'nothing':  ['等待'] * 3,
    'noone':    ['追问', '追问', '沉默', '倾听', '克洛伊·移位', '罐头·分析', '等待'],
}
SETUP = """
  UI.hideTitle();
  G.party = ['chloe','tin'];
  Object.assign(G.items, {hammer:1, lantern:1, jug:1, poem:1, photo:1, bell:1, watch:1, bridge_nail:1});
  await World.load('village', 20, 16, 'down'); G.mode = 'map';
"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 960, 'height': 640})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto(URL); pg.wait_for_timeout(1500)

        def cmd_labels():
            return pg.evaluate("[...document.querySelectorAll('#b-cmd .opt')].map(b => b.textContent)")

        def cmd_visible():
            return pg.evaluate("!$('b-cmd').classList.contains('hidden') && document.querySelectorAll('#b-cmd .opt').length > 0")

        def pick(label):
            labels = cmd_labels()
            if label not in labels:
                return False
            i = labels.index(label)
            for _ in range(i // 2): pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(30)
            for _ in range(i % 2): pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(30)
            pg.keyboard.press('z'); pg.wait_for_timeout(120)
            return True

        def fight(bid, plan, idle_last=False):
            pg.evaluate("async () => {" + SETUP + "}")
            pg.evaluate(f"window.__res = null; Battle.start('{bid}').then(r => window.__res = r); 0")
            step, log, t0 = 0, [], time.time()
            while time.time() - t0 < 180:
                res = pg.evaluate("window.__res")
                if res: break
                if cmd_visible():
                    if step >= len(plan):
                        if idle_last:
                            pg.wait_for_timeout(500); continue
                        log.append('OUT-OF-PLAN'); pick(cmd_labels()[0]); continue
                    want = plan[step]
                    if idle_last and step == len(plan) - 1:
                        log.append('(idle)'); step += 1; continue
                    if want.startswith('宝物:'):
                        pick('宝物'); pg.wait_for_timeout(200)
                        ok = pick(want[3:])
                        log.append(want if ok else want + '?MISSING ' + str(cmd_labels()))
                    else:
                        ok = pick(want)
                        log.append(want if ok else want + '?MISSING ' + str(cmd_labels()))
                    step += 1
                    hp = pg.evaluate("$('b-hp').style.width"); mind = pg.evaluate("$('b-mind').style.width")
                    log[-1] += f'[{hp},{mind}]'
                else:
                    pg.keyboard.press('z'); pg.wait_for_timeout(90)
            res = pg.evaluate("window.__res")
            pg.wait_for_timeout(900)
            return res, log

        for bid, plan in PLANS.items():
            res, log = fight(bid, plan)
            print(f'{bid:9s} -> {res}  steps={len(log)}  ' + ' '.join(log))

        res, log = fight('slime', ['倾听'] * 30)
        print('slime retreat test ->', res, len(log))

        res, log = fight('noone', ['追问', '追问', '沉默', '倾听', '克洛伊·移位', '罐头·分析', '等待'], idle_last=True)
        print('noone idle-finale ->', res, ' '.join(log))
        pg.screenshot(path='/tmp/shots/after_battles.png')
        print('errors:', errs[:10])
        b.close()


main()
