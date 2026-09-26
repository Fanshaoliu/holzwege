"""Record which scene every NPC/talk-spot would give at each step of the main route, then flag suspicious ones."""
import json, re, sys
from playwright.sync_api import sync_playwright
URL = 'http://127.0.0.1:8792/index.html'
JS = open('tests/audit_js.txt', encoding='utf-8').read()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(URL); pg.wait_for_timeout(1500); pg.evaluate("localStorage.clear()")
    r = pg.evaluate(JS, 'e3_start')
    json.dump(r, open('/tmp/audit.json', 'w', encoding='utf-8'), ensure_ascii=False)
    b.close()
s = open('data/story.js', encoding='utf-8').read()
story = json.loads(s[s.index('window.STORY = ') + 15:s.index(';\nwindow.CODEX')])
def chain(sid, seen=None):
    seen = seen or set()
    if sid in seen or sid not in story: return seen
    seen.add(sid)
    def walk(cmds):
        for c in cmds:
            if c['t'] in ('goto', 'call'): chain(c['id'], seen)
            if c['t'] == 'choice': [chain(o['goto'], seen) for o in c['options']]
            if c['t'] == 'if': walk(c['then']); walk(c.get('else', []))
    walk(story[sid]['cmds']); return seen
def effects(sid):
    out = set()
    def walk(cmds):
        for c in cmds:
            if c['t'] in ('give', 'battle', 'party'): out.add(c['t'] + ':' + str(c.get('item') or c.get('id')))
            if c['t'] == 'set' and not str(c['k']).startswith('show_'): out.add('set:' + c['k'])
            if c['t'] == 'if': walk(c['then']); walk(c.get('else', []))
    for x in chain(sid): walk(story[x]['cmds'])
    return out
offers = r['offers']
flag_repeat, flag_stale = {}, {}
for o in offers:
    ran = set(o['ran'])
    for mid, who, sc in o['rows']:
        eff = effects(sc)
        if sc in ran and eff:
            flag_repeat.setdefault((mid, who, sc), (o['step'], sorted(eff)))
        m = re.match(r'c(\d)_', sc)
        if m and int(m.group(1)) < o['ch'] and eff:
            flag_stale.setdefault((mid, who, sc), (o['ch'], o['step']))
print('steps recorded:', len(offers))
print('GOALS:')
last = None
for o in offers:
    if o['goal'] != last:
        print(f"  after {o['step']:40s} -> {o['goal']}"); last = o['goal']
print('\n[A] scenes offered again after already played, and they have side effects:')
for k, v in flag_repeat.items(): print('  ', k, 'first seen repeat at', v[0], 'effects', v[1])
print('\n[B] chapter-N scenes with side effects still offered in a later chapter:')
for k, v in flag_stale.items(): print('  ', k, 'in ch', v[0], 'at', v[1])
# per-NPC timeline of distinct scenes by chapter, for major characters
tl = {}
for o in offers:
    for mid, who, sc in o['rows']:
        key = (mid, who)
        lst = tl.setdefault(key, [])
        if not lst or lst[-1][1] != sc: lst.append((o['ch'], sc))
json.dump({f'{k[0]}|{k[1]}': v for k, v in tl.items()}, open('/tmp/audit_timeline.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
