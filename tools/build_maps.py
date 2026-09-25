"""Render all maps and export data/maps.js"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import mapkit
import maps_ch1
MODULES = [maps_ch1]
for extra in ('maps_ch2', 'maps_ch3', 'maps_ch4', 'maps_ch5'):
    try:
        MODULES.append(__import__(extra))
    except ImportError:
        pass

def main(only=None):
    out = {}
    dfile = 'data/maps.json'
    if os.path.exists(dfile):
        out = json.load(open(dfile, encoding='utf-8'))
    for mod in MODULES:
        for fn in mod.MAPS:
            if only and fn.__name__ not in only: continue
            t = time.time()
            m = fn()
            data = mapkit.render(m, 'assets/maps')
            out[m.id] = data
            print(f'{m.id}: {m.grid.w}x{m.grid.h} {time.time()-t:.1f}s')
    os.makedirs('data', exist_ok=True)
    json.dump(out, open(dfile, 'w', encoding='utf-8'), ensure_ascii=False)
    with open('data/maps.js', 'w', encoding='utf-8') as f:
        f.write('window.MAPS = ' + json.dumps(out, ensure_ascii=False) + ';\n')

if __name__ == '__main__':
    main(sys.argv[1:] or None)
