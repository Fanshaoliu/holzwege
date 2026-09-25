"""Map building DSL + renderer. Produces below/above layers, collision, and game data for each map."""
import json
import os
import random
from art.px import Canvas, T, h2, mix
from art import terrain as TR, props as PR, buildings as BD, pal as P

# terrain chars -> ground spec. 'solid' marks blocked terrain.
LEGEND = {
    '.': dict(base='grass'), ',': dict(base='grass', decor='flowers'), '"': dict(base='grass', decor='tallgrass'),
    '=': dict(base='grass', over='dirt'), ':': dict(base='grass', over='cobble'), 's': dict(base='grass', over='sand'),
    '~': dict(base='grass', over='water', solid=True, water=True),
    'b': dict(base='grass', over='water', joins=('water',), water=True, bridge=True),
    'x': dict(base='grass', over='water', solid=True, water=True),     # water that becomes a bridge by flag
    'C': dict(base='grass', cliff=True, solid=True),
    'F': dict(base='grass', over='forest'), 'f': dict(base='forest'),
    'T': dict(base='grass', obj='tree'), 'P': dict(base='grass', obj='pine'), 'D': dict(base='grass', obj='deadtree'),
    't': dict(base='forest', obj='tree'), 'p': dict(base='forest', obj='pine'), 'd': dict(base='forest', obj='deadtree'),
    'B': dict(base='grass', obj='bush'), 'o': dict(base='grass', obj='bigrock'), 'n': dict(base='forest', obj='bush'),
    '-': dict(base='grass', obj='fence_h'), '|': dict(base='grass', obj='fence_v'),
    'y': dict(base='grass', over='dirt', decor='field'),
    '#': dict(base='stone', wall=True, solid=True), 'W': dict(base='wood'), 'S': dict(base='stone'), 'M': dict(base='marble'),
    'K': dict(base='wood', over='carpet'), 'k': dict(base='marble', over='carpet_b'), 'X': dict(base='void'),
    'O': dict(base='concrete'), 'I': dict(base='tiles'), 'Q': dict(base='plaza'), 'q': dict(base='plaza', over='canal', solid=True, water=True),
    'w': dict(base='plaza', over='canal', solid=True, water=True), 'm': dict(base='marble', over='water', solid=True, water=True),
    'R': dict(base='roof', solid=False), 'Y': dict(base='sky', solid=True), 'Z': dict(base='void', solid=True),
    ' ': dict(base='void', solid=True),
}

# extra bases for special maps
TR.BASES['roof'] = lambda x, y, s=0: _roof_tex(x, y)
TR.BASES['sky'] = lambda x, y, s=0: _sky_tex(x, y)
TR.BASES['pave'] = lambda x, y, s=0: TR.tex_stonefloor(x, y, s + 3, P.SAND, 8)


def _roof_tex(ax, ay):
    R = P.THATCH
    yy = ay % 4
    if yy == 3: return R[1]
    if yy == 0: return R[4]
    return R[2] if h2(ax, ay // 4, 7) < 0.3 else R[3]


def _sky_tex(ax, ay):
    base = mix(P.VOID[2], P.SLATE_B[0], min(1, ay / 120))
    r = h2(ax, ay, 991)
    if r < 0.006: return P.FLOWERS[5]
    if r < 0.012: return P.SLATE_B[4]
    return base


class Grid:
    def __init__(self, w, h, fill='.'):
        self.w, self.h = w, h
        self.rows = [[fill] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h: return self.rows[y][x]
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h: self.rows[y][x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w): self.set(xx, yy, c)

    def frame(self, x, y, w, h, c):
        for xx in range(x, x + w): self.set(xx, y, c); self.set(xx, y + h - 1, c)
        for yy in range(y, y + h): self.set(x, yy, c); self.set(x + w - 1, yy, c)

    def hline(self, x0, x1, y, c, width=1):
        for xx in range(min(x0, x1), max(x0, x1) + 1):
            for k in range(width): self.set(xx, y + k, c)

    def vline(self, x, y0, y1, c, width=1):
        for yy in range(min(y0, y1), max(y0, y1) + 1):
            for k in range(width): self.set(x + k, yy, c)

    def path(self, pts, c, width=1):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 == x1: self.vline(x0, y0, y1, c, width)
            elif y0 == y1: self.hline(x0, x1, y0, c, width)
            else:
                self.hline(x0, x1, y0, c, width); self.vline(x1, y0, y1, c, width)

    def scatter(self, c, n, area, seed=0, only='.'):
        x0, y0, w, h = area
        rnd = random.Random(seed)
        for _ in range(n):
            x, y = rnd.randrange(x0, x0 + w), rnd.randrange(y0, y0 + h)
            if self.get(x, y) == only: self.set(x, y, c)

    def border(self, c, thick=2, seed=0, ragged=True, gaps=()):
        rnd = random.Random(seed)
        for y in range(self.h):
            for x in range(self.w):
                d = min(x, y, self.w - 1 - x, self.h - 1 - y)
                t = thick + (rnd.random() < 0.35 if ragged else 0)
                if d < t:
                    if any(gx0 <= x <= gx1 and gy0 <= y <= gy1 for (gx0, gy0, gx1, gy1) in gaps): continue
                    self.set(x, y, c if rnd.random() > 0.25 else ('P' if c == 'T' else ('p' if c == 't' else c)))

    def lines(self):
        return [''.join(r) for r in self.rows]


class Map:
    def __init__(self, mid, name, grid, music='village', legend=None, seed=0, dark=0, night=False, indoor=False):
        self.id, self.name, self.grid, self.music, self.seed = mid, name, grid, music, seed
        self.legend = dict(LEGEND); self.legend.update(legend or {})
        self.buildings, self.props, self.npcs, self.events, self.warps, self.chests = [], [], [], [], [], []
        self.decals, self.anims, self.walkover, self.blocks = [], [], [], []
        self.dark, self.night, self.indoor = dark, night, indoor
        self.wall_style = 'wood'
        self.spots, self.talkover = [], []

    # ---- authoring
    def building(self, x, y, **kw):
        kw = dict(kw); kw['x'], kw['y'] = x, y
        self.buildings.append(kw); return kw

    def prop(self, name, x, y, solid=True, layer=None, cond=None, seed=0, talk=None):
        self.props.append(dict(name=name, x=x, y=y, solid=solid, layer=layer, cond=cond, seed=seed))
        if talk: self.events.append(dict(x=x, y=y, trigger='talk', scene=talk, cond=cond))

    def npc(self, nid, sprite, x, y, pages, dir='down', move='static', show=None, name=None, portrait=None, radius=2):
        self.npcs.append(dict(id=nid, sprite=sprite, x=x, y=y, dir=dir, move=move, show=show, pages=pages,
                              name=name, portrait=portrait, radius=radius))

    def event(self, x, y, scene, trigger='talk', cond=None, once=None, w=1, h=1):
        self.events.append(dict(x=x, y=y, w=w, h=h, trigger=trigger, scene=scene, cond=cond, once=once))

    def warp(self, x, y, to, tx, ty, dir='down', cond=None, deny=None, w=1, h=1):
        self.warps.append(dict(x=x, y=y, w=w, h=h, to=to, tx=tx, ty=ty, dir=dir, cond=cond, deny=deny))

    def chest(self, cid, x, y, item, count=1):
        self.chests.append(dict(id=cid, x=x, y=y, item=item, count=count))

    def decal(self, did, draw_fn, x, y, w, h, cond=None, walk=None, solid=None, layer='below'):
        self.decals.append(dict(id=did, fn=draw_fn, x=x, y=y, w=w, h=h, cond=cond, walk=walk, solid=solid, layer=layer))

    def anim(self, kind, x, y, cond=None, **kw):
        a = dict(kind=kind, x=x, y=y, cond=cond); a.update(kw); self.anims.append(a)


# ------------------------------------------------------------------ rendering

def _spec(m, x, y):
    ch = m.grid.get(x, y)
    if ch is None: return None
    return m.legend.get(ch, m.legend['.'])


def render_walls(cv, m):
    """Interior walls: 2-tile-tall faces above floors, dark tops elsewhere."""
    g = m.grid
    style = m.wall_style

    def is_wall(x, y):
        s = _spec(m, x, y)
        return s is None or s.get('wall')
    for y in range(g.h):
        for x in range(g.w):
            if not is_wall(x, y): continue
            below1 = not is_wall(x, y + 1) and _spec(m, x, y + 1) is not None
            below2 = (not below1) and (not is_wall(x, y + 2)) and _spec(m, x, y + 2) is not None and is_wall(x, y + 1)
            ox, oy = x * T, y * T
            if below1 or below2:
                for yy in range(T):
                    for xx in range(T):
                        ax, ay = ox + xx, oy + yy
                        cv.a[ay, ax] = _wall_face(ax, ay, yy + (T if below1 else 0), style)
            else:
                if m.indoor:
                    topc = P.VOID[1]
                else:
                    topc = {'marble': P.MARBLE[2], 'stone': P.STONE[2], 'metal': P.METAL[1]}.get(style, P.STONE[2])
                for yy in range(T):
                    for xx in range(T):
                        cv.a[oy + yy, ox + xx] = topc
                # rim lines on edges touching non-wall or faces
                edge = P.WOOD[4] if style == 'wood' else (P.MARBLE[4] if style == 'marble' else P.STONE[4])
                dark = P.OUT
                for (dx, dy, xs, ys) in ((0, -1, range(T), [0]), (0, 1, range(T), [T - 1]), (-1, 0, [0], range(T)), (1, 0, [T - 1], range(T))):
                    nb = is_wall(x + dx, y + dy)
                    face_below = dy == 1 and (not is_wall(x, y + 2) and _spec(m, x, y + 2) is not None) if nb else False
                    if not nb or face_below or (dy == 1 and nb and not is_wall(x, y + 3) and False):
                        for yy in ys:
                            for xx in xs:
                                cv.a[oy + yy, ox + xx] = edge
                for (dx, dy) in ((0, 1),):
                    pass


def _wall_face(ax, ay, fy, style):
    """fy: 0..31 within the 2-tile face (0 = top trim, 31 = floor contact)."""
    if style == 'wood':
        if fy < 3: return P.WOOD[4] if fy == 0 else P.WOOD[2]
        if fy >= 28: return P.WOOD[1] if fy < 30 else P.OUT
        if fy >= 25: return P.WOOD[3]
        xx = ax % 12
        base = P.WOOD[3] if (ax // 12) % 2 else mix(P.WOOD[3], P.WOOD[2], 0.3)
        if xx == 0: return P.WOOD[1]
        if xx == 1: return P.WOOD[4]
        if h2(ax, ay, 555) < 0.05: return P.WOOD[2]
        return base
    if style == 'plaster':
        if fy < 3: return P.TIMBER[3] if fy == 0 else P.TIMBER[2]
        if fy >= 26: return P.WOOD[2] if fy < 30 else P.OUT
        if fy == 25: return P.WOOD[4]
        if ax % 32 in (0, 1, 2): return P.TIMBER[2]
        return P.PLASTER[3] if h2(ax, ay, 556) > 0.05 else P.PLASTER[2]
    if style == 'marble':
        if fy < 3: return P.GOLD[3] if fy == 0 else P.MARBLE[4]
        if fy >= 28: return P.MARBLE[1] if fy < 30 else P.OUT
        if ax % 24 in (0, 1, 2, 3):
            return P.MARBLE[5] if ax % 24 == 0 else (P.MARBLE[2] if ax % 24 == 3 else P.MARBLE[4])
        return P.MARBLE[3] if (fy // 8) % 2 == 0 else mix(P.MARBLE[3], P.MARBLE[4], 0.4)
    if style == 'metal':
        if fy < 3: return P.METAL[3]
        if fy >= 29: return P.OUT
        if ax % 16 == 0: return P.METAL[0]
        return P.METAL[1] if (fy // 6) % 2 else P.METAL[2]
    if style == 'void':
        return P.VOID[1] if fy < 30 else P.VOID[0]
    # stone
    if fy < 3: return P.STONE[4] if fy == 0 else P.STONE[3]
    if fy >= 29: return P.OUT
    row = fy // 6
    off = (row % 2) * 6
    xx = (ax + off) % 12
    if fy % 6 == 5 or xx == 11: return P.STONE[1]
    k = h2((ax + off) // 12, row + ay // 32 * 7, 557)
    return P.STONE[3] if k > 0.4 else P.STONE[2]


def draw_decor(cv, m):
    g = m.grid
    for y in range(g.h):
        for x in range(g.w):
            s = _spec(m, x, y) or {}
            d = s.get('decor')
            if not d: continue
            if d == 'field':
                for yy in range(T):
                    for xx in range(T):
                        ax, ay = x * T + xx, y * T + yy
                        if yy % 4 == 1:
                            cv.a[ay, ax] = P.GRASS[3] if h2(ax, ay, 13) > 0.3 else P.GRASS[4]
                        elif yy % 4 == 2:
                            cv.a[ay, ax] = P.GRASS[1]
                continue
            img, ax_, ay_ = PR.PROPS[d](x * 31 + y * 7)
            cv.blit_fast(img, x * T, y * T)


def _bridge_planks(w, h, vertical=False):
    c = Canvas(w * T, h * T)
    W = P.WOOD
    if not vertical:
        for x in range(w * T):
            xx = x % 6
            col = W[3] if xx < 4 else (W[4] if xx == 4 else W[1])
            for y in range(2, h * T - 2): c.px(x, y, col)
        for x in range(w * T):
            c.px(x, 1, W[1]); c.px(x, h * T - 2, W[1]); c.px(x, 0, P.OUT); c.px(x, h * T - 1, P.OUT)
        for x in range(0, w * T, 16):
            c.rect(x, 0, 2, 3, W[2]); c.rect(x, h * T - 3, 2, 3, W[2])
    else:
        for y in range(h * T):
            yy = y % 6
            col = W[3] if yy < 4 else (W[4] if yy == 4 else W[1])
            for x in range(2, w * T - 2): c.px(x, y, col)
        for y in range(h * T):
            c.px(1, y, W[1]); c.px(w * T - 2, y, W[1]); c.px(0, y, P.OUT); c.px(w * T - 1, y, P.OUT)
    return c


def render(m, outdir):
    g = m.grid
    W, H = g.w * T, g.h * T
    lines = g.lines()
    legend = {k: v for k, v in m.legend.items()}
    legend['default'] = legend['.']
    below = TR.render_ground(lines, legend, seed=m.seed)
    TR.render_cliffs(below, lines, legend, seed=m.seed)
    render_walls(below, m)
    draw_decor(below, m)
    above = Canvas(W, H)
    solid = [[False] * g.w for _ in range(g.h)]
    water = []
    for y in range(g.h):
        for x in range(g.w):
            s = _spec(m, x, y) or {}
            if s.get('solid'): solid[y][x] = True
            if s.get('water') and not s.get('bridge'): water.append([x, y])
    # bridges drawn over water (static 'b' cells)
    for y in range(g.h):
        for x in range(g.w):
            s = _spec(m, x, y) or {}
            if s.get('bridge'):
                horiz = (_spec(m, x - 1, y) or {}).get('bridge') or (_spec(m, x + 1, y) or {}).get('bridge') or not (
                    (_spec(m, x, y - 1) or {}).get('bridge') or (_spec(m, x, y + 1) or {}).get('bridge'))
                vert_neighbors = (_spec(m, x, y - 1) or {}).get('water') and (_spec(m, x, y + 1) or {}).get('water')
                below.blit_fast(_bridge_planks(1, 1, vertical=not vert_neighbors and not horiz), x * T, y * T)
    # collect objects: (sort_y, draw callable)
    objs = []
    for y in range(g.h):
        for x in range(g.w):
            s = _spec(m, x, y) or {}
            o = s.get('obj')
            if o:
                img, ax, ay = PR.PROPS[o](x * 13 + y * 29 + m.seed)
                objs.append((y, x, img, x * T - ax, y * T - ay, y, 1))
                solid[y][x] = True
    for p in m.props:
        if p.get('cond'): continue  # conditional props are exported as decals
        img, ax, ay = PR.PROPS[p['name']](p.get('seed', 0))
        wtiles = max(1, img.w // T)
        htiles = max(1, (img.h - ay) // T)
        base_row = p['y'] + htiles - 1
        objs.append((base_row, p['x'], img, p['x'] * T - ax, p['y'] * T - ay, base_row, htiles, p.get('layer')))
        if p['solid']:
            for yy in range(p['y'], p['y'] + htiles):
                for xx in range(p['x'], p['x'] + wtiles):
                    if 0 <= yy < g.h and 0 <= xx < g.w: solid[yy][xx] = True
    for b in m.buildings:
        kind = b.get('kind', 'house')
        if kind == 'house':
            args = {k: v for k, v in b.items() if k in ('w', 'roof_h', 'wall_h', 'roof', 'wall', 'doors', 'windows', 'chimney', 'sign', 'sign_col', 'dormers', 'seed', 'door_style', 'glow', 'flowers')}
            img = BD.house(**args)
            fw, fh = b['w'], b['roof_h'] + b['wall_h']
        elif kind == 'tower':
            img = BD.clock_tower(); fw, fh = 3, 9
        elif kind == 'hut':
            img = BD.hut(); fw, fh = 4, 4
        elif kind == 'wall':
            img = BD.city_wall_segment(b['w'], b.get('h', 3)); fw, fh = b['w'], b.get('h', 3)
        top_extra = img.h - fh * T
        base_row = b['y'] + fh - 1
        objs.append((base_row, b['x'], img, b['x'] * T, b['y'] * T - top_extra, b['y'], fh, 'building'))
        for yy in range(b['y'], b['y'] + fh):
            for xx in range(b['x'], b['x'] + fw):
                if 0 <= yy < g.h and 0 <= xx < g.w: solid[yy][xx] = True
        for dc in b.get('doors', ()):
            dx, dy = b['x'] + dc, b['y'] + fh - 1
            solid[dy][dx] = False
            if b.get('warp'):
                wp = b['warp']
                m.warps.append(dict(x=dx, y=dy, w=1, h=1, to=wp['to'], tx=wp['tx'], ty=wp['ty'], dir=wp.get('dir', 'up'),
                                    cond=wp.get('cond'), deny=wp.get('deny')))
            elif b.get('locked'):
                m.events.append(dict(x=dx, y=dy, w=1, h=1, trigger='step', scene=b['locked'], cond=None, once=None, push=True))
    objs.sort(key=lambda o: (o[0], o[1]))
    if not m.indoor:
        _shadows(below, m, objs)
    for o in objs:
        base_row, x, img, px, py = o[0], o[1], o[2], o[3], o[4]
        top_row = o[5] if len(o) > 5 else base_row
        htiles = o[6] if len(o) > 6 else 1
        layer = o[7] if len(o) > 7 else None
        if layer == 'above':
            above.blit(img, px, py); continue
        if layer == 'below':
            below.blit(img, px, py); continue
        # split: pixels above the object's first collision row go to 'above'
        if layer == 'building':
            split_y = top_row * T
        else:
            split_y = (base_row - htiles + 1) * T
        top_part = img.a[:max(0, split_y - py)]
        bot_part = img.a[max(0, split_y - py):]
        if top_part.shape[0]:
            above.blit(Canvas.from_array(top_part), px, py)
            # also paint it below so nothing is missing when drawn without chars
            below.blit(Canvas.from_array(top_part), px, py)
        if bot_part.shape[0]:
            below.blit(Canvas.from_array(bot_part), px, max(py, split_y))
    os.makedirs(outdir, exist_ok=True)
    below.save(f'{outdir}/{m.id}.png')
    has_above = above.a[:, :, 3].any()
    if has_above:
        above.save(f'{outdir}/{m.id}_fg.png')
    # decals
    decal_out = []
    for d in m.decals:
        img = d['fn']()
        path = f'{outdir}/{m.id}_{d["id"]}.png'
        img.save(path)
        decal_out.append(dict(id=d['id'], img=f'assets/maps/{m.id}_{d["id"]}.png', x=d['x'], y=d['y'], cond=d['cond'],
                              walk=d['walk'], solid=d['solid'], layer=d['layer']))
    for p in m.props:
        if not p.get('cond'): continue
        img, ax, ay = PR.PROPS[p['name']](p.get('seed', 0))
        path = f'{outdir}/{m.id}_prop_{p["name"]}_{p["x"]}_{p["y"]}.png'
        img.save(path)
        htiles = max(1, (img.h - ay) // T)
        decal_out.append(dict(id=f'prop_{p["x"]}_{p["y"]}', img=path.replace(outdir, 'assets/maps'), x=p['x'], y=p['y'],
                              ox=-ax, oy=-ay, cond=p['cond'], solid=[[p['x'], p['y'] + k] for k in range(htiles)] if p['solid'] else None,
                              layer='sort'))
    data = dict(id=m.id, name=m.name, w=g.w, h=g.h, music=m.music, img=f'assets/maps/{m.id}.png',
                fg=f'assets/maps/{m.id}_fg.png' if has_above else None,
                solid=[''.join('1' if s else '0' for s in row) for row in solid], water=water,
                npcs=m.npcs, events=m.events, warps=m.warps, chests=m.chests, decals=decal_out, anims=m.anims,
                dark=m.dark, night=m.night, indoor=m.indoor, spots=m.spots, talkover=m.talkover)
    return data


def _shadows(cv, m, objs):
    g = m.grid
    sh = (0, 0, 0)
    for o in objs:
        layer = o[7] if len(o) > 7 else None
        img, px, py = o[2], o[3], o[4]
        if layer == 'building':
            base_row = o[0]
            x0 = px + img.w; y0 = (o[5]) * T + 4
            for y in range(y0, (base_row + 1) * T):
                for x in range(x0, x0 + 4):
                    if 0 <= x < cv.w and 0 <= y < cv.h:
                        p = cv.a[y, x]
                        cv.a[y, x, :3] = (p[:3] * 0.72).astype('uint8')
        else:
            base_row = o[0]
            cx = px + img.w // 2 + 2
            cy = (base_row + 1) * T - 3
            for y in range(cy - 2, cy + 3):
                for x in range(cx - 7, cx + 8):
                    if ((x - cx) / 7.5) ** 2 + ((y - cy) / 2.6) ** 2 <= 1 and 0 <= x < cv.w and 0 <= y < cv.h:
                        if (x + y) % 2 == 0 or abs(x - cx) < 5:
                            p = cv.a[y, x]
                            cv.a[y, x, :3] = (p[:3] * 0.78).astype('uint8')
