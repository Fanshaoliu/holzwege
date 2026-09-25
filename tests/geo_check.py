"""Static geometry check: every NPC / event / chest / spot must be reachable from where the player enters the map,
and every warp must land on a walkable tile."""
import json
from collections import deque

maps = json.load(open('data/maps.json', encoding='utf-8'))
s = open('data/story.js', encoding='utf-8').read()
story = json.loads(s[s.index('window.STORY = ') + 15:s.index(';\nwindow.CODEX')])


def scene_warps():
    out = []
    def scan(cmds):
        for c in cmds:
            if c.get('t') == 'warp': out.append((c['map'], c['x'], c['y']))
            if c.get('t') == 'if': scan(c.get('then', [])); scan(c.get('else', []))
    for sc in story.values(): scan(sc['cmds'])
    return out


entries = {mid: [] for mid in maps}
for mid, m in maps.items():
    for w in m.get('warps', []):
        if w['to'] in entries: entries[w['to']].append((w['tx'], w['ty'], f'warp from {mid}'))
for (mid, x, y) in scene_warps():
    if mid in entries: entries[mid].append((x, y, 'scene warp'))

problems = []
for mid, m in maps.items():
    W, H = m['w'], m['h']
    solid = [[c == '1' for c in row] for row in m['solid']]
    for d in m.get('decals', []):
        for (x, y) in d.get('walk') or []: solid[y][x] = False
    for c in m.get('chests', []): solid[c['y']][c['x']] = True
    walk = lambda x, y: 0 <= x < W and 0 <= y < H and not solid[y][x]
    for (x, y, why) in entries[mid]:
        if not walk(x, y): problems.append(f'{mid}: arrival ({x},{y}) from {why} is solid')
    seen = set(); q = deque()
    for (x, y, _) in entries[mid]:
        if walk(x, y) and (x, y) not in seen: seen.add((x, y)); q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if walk(nx, ny) and (nx, ny) not in seen: seen.add((nx, ny)); q.append((nx, ny))
    if not entries[mid]:
        problems.append(f'{mid}: no way in'); continue
    talkover = {tuple(c) for c in m.get('talkover') or []}
    def near(x, y):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) in seen: return True
            if (x + dx, y + dy) in talkover and (x + 2 * dx, y + 2 * dy) in seen: return True
        return False
    for n in m.get('npcs', []):
        if n.get('show') == 'false': continue
        if not near(n['x'], n['y']) and (n['x'], n['y']) not in seen:
            problems.append(f"{mid}: npc {n['id']} at ({n['x']},{n['y']}) unreachable")
    for e in m.get('events', []):
        if e['trigger'] in ('auto', 'none'): continue
        cells = [(e['x'] + i, e['y'] + j) for i in range(e.get('w') or 1) for j in range(e.get('h') or 1)]
        if e['trigger'] == 'step':
            if not any(c in seen for c in cells): problems.append(f"{mid}: step event {e.get('scene') or e.get('pages')} at {cells[0]} unreachable")
        else:
            if not any(near(*c) for c in cells): problems.append(f"{mid}: talk event {e.get('scene') or (e.get('pages') or [[0, '?']])[-1][1]} at {cells[0]} unreachable")
    for c in m.get('chests', []) + (m.get('spots') or []):
        if not near(c['x'], c['y']): problems.append(f"{mid}: chest/spot {c['id']} at ({c['x']},{c['y']}) unreachable")
    for w in m.get('warps', []):
        cells = [(w['x'] + i, w['y'] + j) for i in range(w.get('w') or 1) for j in range(w.get('h') or 1)]
        if not any(c in seen for c in cells): problems.append(f"{mid}: warp to {w['to']} at {cells[0]} unreachable")

print('maps:', len(maps), 'problems:', len(problems))
for p in problems: print('  ', p)
