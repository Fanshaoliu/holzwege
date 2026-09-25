"""Ground rendering: base textures + autotiled overlays with natural edges.
Everything samples absolute pixel coordinates, so textures never visibly repeat and edges match across cells."""
import math
import numpy as np
from .px import Canvas, rgb, mix, h2, vnoise, T
from . import pal as P


# ---------------------------------------------------------------- base textures (per absolute pixel)

def tex_grass(ax, ay, s=0, pal=None):
    G = pal or P.GRASS
    n = vnoise(ax, ay, 26, 11 + s)
    base = G[2]
    if n < 0.32: base = mix(G[2], G[1], 0.35)
    elif n > 0.72: base = mix(G[2], G[3], 0.35)
    # jittered tufts on a 4x4 lattice
    bx, by = ax // 4, ay // 4
    r = h2(bx, by, 3 + s)
    if r < 0.78:
        tx = bx * 4 + int(h2(bx, by, 5 + s) * 3)
        ty = by * 4 + int(h2(bx, by, 7 + s) * 3)
        dx, dy = ax - tx, ay - ty
        kind = int(h2(bx, by, 9 + s) * 3)
        if kind == 0:   # single blade
            if dx == 0 and dy == 0: return G[4] if n > 0.4 else G[3]
            if dx == 0 and dy == 1: return G[3]
            if dx == 0 and dy == 2: return G[1]
        elif kind == 1:  # v tuft
            if dy == 0 and dx in (-1, 1): return G[3]
            if dy == 1 and dx == 0: return G[4] if n > 0.5 else G[3]
            if dy == 2 and dx == 0: return G[1]
        else:            # dark notch
            if dx == 0 and dy == 0: return G[1]
            if dx == 1 and dy == 0: return mix(G[2], G[1], 0.5)
    return base


def tex_forest(ax, ay, s=0):
    F = P.FOREST
    n = vnoise(ax, ay, 18, 21 + s)
    c = F[2] if n > 0.45 else mix(F[2], F[1], 0.5)
    r = h2(ax, ay, 23 + s)
    if r < 0.06: return F[1]
    if r < 0.09: return F[3]
    if r < 0.105: return P.DIRT[1]
    if r < 0.115: return P.DIRT[2]
    return c


def tex_dirt(ax, ay, s=0, R=None):
    D = R or P.DIRT
    n = vnoise(ax, ay, 20, 31 + s)
    c = D[3] if n > 0.4 else mix(D[3], D[2], 0.35)
    r = h2(ax, ay, 33 + s)
    if r < 0.05: return D[2]
    if r < 0.075: return D[4]
    if r < 0.085:
        return D[1]
    # small pebble: light pixel with dark under it
    if h2(ax, ay - 1, 33 + s) < 0.012: return D[1]
    if r > 0.988: return D[4]
    return c


def tex_sand(ax, ay, s=0):
    return tex_dirt(ax, ay, s + 7, P.SAND)


def _voronoi(ax, ay, cell, s, jitter=0.8):
    gx, gy = ax // cell, ay // cell
    best = (1e9, None, None); second = 1e9
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = gx + ox, gy + oy
            fx = cx * cell + cell * (0.5 + (h2(cx, cy, s) - 0.5) * jitter)
            fy = cy * cell + cell * (0.5 + (h2(cx, cy, s + 1) - 0.5) * jitter)
            d = math.hypot(ax + 0.5 - fx, ay + 0.5 - fy)
            if d < best[0]:
                second = best[0]; best = (d, (cx, cy), (fx, fy))
            elif d < second:
                second = d
    return best, second


def tex_cobble(ax, ay, s=0, R=None, cell=6):
    C = R or P.COBBLE
    (d1, cid, (fx, fy)), d2 = _voronoi(ax, ay, cell, 41 + s)
    if d2 - d1 < 1.05:
        return C[1]
    k = h2(cid[0], cid[1], 43 + s)
    base = C[3] if k > 0.55 else (C[2] if k > 0.15 else mix(C[2], C[1], 0.3))
    dx, dy = ax + 0.5 - fx, ay + 0.5 - fy
    if dx + dy < -cell * 0.35: return mix(base, C[4], 0.6)
    if dx + dy > cell * 0.45 or d2 - d1 < 1.9: return mix(base, C[1], 0.45)
    return base


def tex_water(ax, ay, s=0, W=None):
    W = W or P.WATER
    n = vnoise(ax, ay, 30, 51 + s)
    c = W[2] if n > 0.35 else mix(W[2], W[1], 0.45)
    # wave strokes on a jittered 8x5 lattice
    bx, by = ax // 8, ay // 5
    if h2(bx, by, 53 + s) < 0.62:
        tx = bx * 8 + int(h2(bx, by, 55 + s) * 5)
        ty = by * 5 + int(h2(bx, by, 57 + s) * 3)
        ln = 2 + int(h2(bx, by, 59 + s) * 3)
        if ay == ty and tx <= ax < tx + ln: return W[4] if ax > tx else W[3]
        if ay == ty + 1 and tx + 1 <= ax < tx + ln + 1: return W[1]
    return c


def tex_wood(ax, ay, s=0):
    Wd = P.WOOD
    row = ay // 5
    yy = ay % 5
    off = int(h2(row, 0, 61 + s) * 24)
    seg = (ax + off) // 24
    xx = (ax + off) % 24
    tone = h2(seg, row, 63 + s)
    base = Wd[3] if tone > 0.5 else mix(Wd[3], Wd[4], 0.35)
    if yy == 4: return Wd[1]
    if xx == 0: return Wd[1]
    if yy == 0: return mix(base, Wd[5], 0.35)
    r = h2(ax, ay, 65 + s)
    if r < 0.07: return Wd[2]
    if yy == 2 and h2(ax // 3, row, 67 + s) < 0.3: return mix(base, Wd[2], 0.6)
    return base


def tex_stonefloor(ax, ay, s=0, R=None, size=8):
    S = R or P.STONE
    tx, ty = ax // size, ay // size
    xx, yy = ax % size, ay % size
    k = h2(tx, ty, 71 + s)
    base = S[3] if k > 0.5 else mix(S[3], S[2], 0.4)
    if xx == size - 1 or yy == size - 1: return S[1]
    if xx == 0 or yy == 0: return mix(base, S[4], 0.5)
    if h2(ax, ay, 73 + s) < 0.04: return S[2]
    return base


def tex_marble(ax, ay, s=0):
    M = P.MARBLE
    tx, ty = ax // 16, ay // 16
    xx, yy = ax % 16, ay % 16
    base = M[4] if (tx + ty) % 2 == 0 else M[3]
    if xx == 15 or yy == 15: return M[1]
    if xx == 0 or yy == 0: return M[5]
    v = vnoise(ax, ay, 7, 75 + s)
    if 0.49 < v < 0.52: return mix(base, M[1], 0.35)
    return base


def tex_plaza(ax, ay, s=0):
    M = P.MARBLE
    row = ay // 6
    off = (row % 2) * 5
    xx = (ax + off) % 10
    yy = ay % 6
    k = h2((ax + off) // 10, row, 77 + s)
    base = M[4] if k > 0.4 else M[3]
    if yy == 5 or xx == 9: return mix(M[2], M[1], 0.3)
    if yy == 0 or xx == 0: return M[5]
    if h2(ax, ay, 79 + s) < 0.03: return M[2]
    return base


def tex_carpet(ax, ay, s=0, R=None):
    Rr = R or P.RED
    xx, yy = ax % 8, ay % 8
    d = abs(xx - 3.5) + abs(yy - 3.5)
    if d < 1.2: return Rr[4]
    if 2.6 < d < 3.6: return Rr[2]
    return Rr[3]


def tex_void(ax, ay, s=0):
    if h2(ax, ay, 81 + s) < 0.004: return P.VOID[2]
    return P.VOID[0]


def tex_concrete(ax, ay, s=0):
    C = P.CONCRETE
    n = vnoise(ax, ay, 14, 83 + s)
    base = C[2] if n > 0.4 else mix(C[2], C[1], 0.4)
    if (ax % 32 == 0) or (ay % 32 == 0): return C[1]
    if h2(ax, ay, 85 + s) < 0.03: return C[1]
    if 0.495 < vnoise(ax, ay, 9, 87 + s) < 0.505: return C[0]
    return base


def tex_tiles(ax, ay, s=0):
    xx, yy = ax % 8, ay % 8
    k = h2(ax // 8, ay // 8, 89 + s)
    base = P.MARBLE[4] if k > 0.2 else P.MARBLE[2]
    if xx == 7 or yy == 7: return P.CONCRETE[3]
    if k < 0.06: return P.CONCRETE[1] if (xx + yy) % 3 == 0 else base
    return base


def tex_snowless_rock(ax, ay, s=0):
    return tex_cobble(ax, ay, s + 3, P.ROCK, cell=7)


BASES = {
    'grass': tex_grass, 'forest': tex_forest, 'dirt': tex_dirt, 'sand': tex_sand,
    'cobble': tex_cobble, 'water': tex_water, 'wood': tex_wood, 'stone': tex_stonefloor,
    'marble': tex_marble, 'plaza': tex_plaza, 'carpet': tex_carpet, 'void': tex_void,
    'concrete': tex_concrete, 'tiles': tex_tiles, 'rock': tex_snowless_rock,
    'canal': lambda x, y, s=0: tex_water(x, y, s + 5, P.CANAL),
    'carpet_b': lambda x, y, s=0: tex_carpet(x, y, s, P.SLATE_B),
}


# ---------------------------------------------------------------- overlays

OVERLAY = {
    # name: (texture, base thickness, wobble amp, rim colours inside [d0,d1], outside ring colours [d1,d2], radius)
    'dirt':   dict(tex='dirt', b=3, wob=1.6, rim=[P.DIRT[2]], ring=[P.GRASS[1]], r=3),
    'sand':   dict(tex='sand', b=3, wob=1.6, rim=[P.SAND[1]], ring=[P.GRASS[1]], r=3),
    'cobble': dict(tex='cobble', b=2, wob=1.0, rim=[P.COBBLE[1]], ring=[P.GRASS[1]], r=2),
    'water':  dict(tex='water', b=3, wob=1.2, rim=[P.WATER[4], P.WATER[3]], ring=[P.DIRT[1], mix(P.GRASS[1], P.DIRT[1], 0.4)], r=3),
    'canal':  dict(tex='canal', b=5, wob=0.0, rim=[P.CANAL[0], P.CANAL[1]], ring=None, r=0, coping=True),
    'forest': dict(tex='forest', b=3, wob=2.0, rim=[], ring=None, r=3, dither=True),
    'carpet': dict(tex='carpet', b=1, wob=0.0, rim=[P.GOLD[3], P.GOLD[2]], ring=None, r=0),
    'carpet_b': dict(tex='carpet_b', b=1, wob=0.0, rim=[P.GOLD[3], P.GOLD[2]], ring=None, r=0),
    'plaza':  dict(tex='plaza', b=1, wob=0.0, rim=[P.MARBLE[1]], ring=[P.GRASS[1]], r=1),
}


def _wob(t, s, amp):
    if amp <= 0: return 0.0
    return (vnoise(t, 0, 5, s) - 0.5) * 2 * amp


def overlay_inside(px_, py_, same, ax, ay, spec, seed):
    """Return (inside:bool, dist_inside:int, dist_outside:int) for local pixel in a cell of an overlay terrain.
    same: dict with keys N,S,W,E,NW,NE,SW,SE -> bool."""
    b0, amp, r = spec['b'], spec['wob'], spec['r']
    west = px_ < 8; north = py_ < 8
    H = 'W' if west else 'E'; V = 'N' if north else 'S'
    D = ('N' if north else 'S') + ('W' if west else 'E')
    dx = px_ if west else 15 - px_
    dy = py_ if north else 15 - py_
    # edge thickness wobbles along the edge (absolute coords -> seamless)
    bh = b0 + _wob(ax, seed + (0 if north else 1), amp)      # for horizontal edge (top/bottom)
    bv = b0 + _wob(ay, seed + (2 if west else 3), amp)       # for vertical edge (left/right)
    hs, vs, ds = same[H], same[V], same[D]
    if hs and vs:
        if ds:
            return True, 99, 0
        rr = b0 + 0.5
        dd = math.hypot(dx + 0.5, dy + 0.5)
        if dd < rr:
            return False, 0, int(rr - dd) + 1
        return True, int(dd - rr), 0
    if not hs and vs:
        if dx >= bv: return True, int(dx - bv), 0
        return False, 0, int(bv - dx)
    if hs and not vs:
        if dy >= bh: return True, int(dy - bh), 0
        return False, 0, int(bh - dy)
    # outer corner
    if dx < bv or dy < bh:
        return False, 0, int(max(bv - dx, bh - dy))
    if r > 0 and dx < bv + r and dy < bh + r:
        cx, cy = bv + r, bh + r
        dd = math.hypot(dx + 0.5 - cx, dy + 0.5 - cy)
        if dd > r:
            return False, 0, int(dd - r) + 1
        return True, int(r - dd), 0
    return True, int(min(dx - bv, dy - bh)), 0


def render_ground(grid, legend, seed=0, tile=T):
    """grid: list[str]; legend: char -> dict(base=..., over=..., cliff=bool).
    Returns Canvas."""
    H = len(grid); W = max(len(r) for r in grid)
    cv = Canvas(W * tile, H * tile)
    arr = cv.a

    def L(x, y):
        if y < 0 or y >= H or x < 0 or x >= W: return None
        ch = grid[y][x] if x < len(grid[y]) else ' '
        return legend.get(ch, legend.get('default'))

    for cy in range(H):
        for cx in range(W):
            spec = L(cx, cy)
            if spec is None: continue
            base = BASES[spec.get('base', 'grass')]
            over = spec.get('over')
            ox, oy = cx * tile, cy * tile
            bs = spec.get('seed', 0)
            # base
            for yy in range(tile):
                for xx in range(tile):
                    arr[oy + yy, ox + xx] = base(ox + xx, oy + yy, bs)
            if over:
                o = OVERLAY[over]
                tex = BASES[o['tex']]

                def same_at(dx, dy):
                    n = L(cx + dx, cy + dy)
                    if n is None: return True
                    return n.get('over') == over or over in n.get('joins', ())
                same = {'N': same_at(0, -1), 'S': same_at(0, 1), 'W': same_at(-1, 0), 'E': same_at(1, 0),
                        'NW': same_at(-1, -1), 'NE': same_at(1, -1), 'SW': same_at(-1, 1), 'SE': same_at(1, 1)}
                full = all(same.values())
                for yy in range(tile):
                    for xx in range(tile):
                        ax, ay = ox + xx, oy + yy
                        if full:
                            arr[ay, ax] = tex(ax, ay, 0); continue
                        ins, di, do = overlay_inside(xx, yy, same, ax, ay, o, seed + 101)
                        if ins:
                            if o.get('dither') and di == 0 and (ax + ay) % 2 == 0:
                                continue
                            rim = o['rim']
                            if di < len(rim): arr[ay, ax] = rim[di]
                            else: arr[ay, ax] = tex(ax, ay, 0)
                        else:
                            if o.get('coping'):
                                # stone embankment on the land side
                                arr[ay, ax] = _coping(ax, ay, do)
                            elif o['ring'] and 1 <= do <= len(o['ring']):
                                arr[ay, ax] = o['ring'][do - 1]
    return cv


def _coping(ax, ay, d):
    S = P.STONE
    if d <= 1: return S[1]
    if d == 2: return S[4]
    blk = ((ax // 5) + (ay // 5)) % 2
    if ax % 5 == 0 or ay % 5 == 0: return S[2]
    return S[3] if blk else mix(S[3], S[4], 0.3)


# ---------------------------------------------------------------- cliffs (rock faces, DQ6 style)

def render_cliffs(cv, grid, legend, tile=T, seed=0):
    H = len(grid); W = max(len(r) for r in grid)

    def is_cliff(x, y):
        if y < 0 or y >= H or x < 0 or x >= W: return True
        ch = grid[y][x] if x < len(grid[y]) else ' '
        s = legend.get(ch, legend.get('default')) or {}
        return bool(s.get('cliff'))
    R = P.ROCK
    for cy in range(H):
        for cx in range(W):
            if not is_cliff(cx, cy): continue
            top = not is_cliff(cx, cy - 1)
            bot = not is_cliff(cx, cy + 1)
            lft = not is_cliff(cx - 1, cy)
            rgt = not is_cliff(cx + 1, cy)
            for yy in range(tile):
                for xx in range(tile):
                    ax, ay = cx * tile + xx, cy * tile + yy
                    (d1, cid, (fx, fy)), d2 = _voronoi(ax, ay, 7, 131 + seed, 0.9)
                    k = h2(cid[0], cid[1], 133)
                    base = R[3] if k > 0.5 else R[2]
                    dxv, dyv = ax + 0.5 - fx, ay + 0.5 - fy
                    if d2 - d1 < 1.1: c = R[0]
                    elif dxv + dyv < -3.0: c = mix(base, R[5], 0.55)
                    elif dxv + dyv < -1.0: c = mix(base, R[4], 0.5)
                    elif dxv + dyv > 3.0 or d2 - d1 < 2.0: c = mix(base, R[1], 0.55)
                    else: c = base
                    # vertical strata shading
                    if bot and yy >= tile - 3:
                        c = mix(c, R[0], 0.5 if yy < tile - 1 else 0.8)
                    if lft and xx == 0: c = R[0]
                    if rgt and xx == tile - 1: c = mix(c, R[0], 0.6)
                    cv.a[ay, ax] = c
            if top:
                # grass lip overhanging the rock face
                for xx in range(tile):
                    ax = cx * tile + xx
                    depth = 3 + int(vnoise(ax, cy, 4, 137) * 3)
                    for yy in range(depth):
                        ay = cy * tile + yy
                        cv.a[ay, ax] = tex_grass(ax, ay) if yy < depth - 1 else P.GRASS[1]
                    cv.a[cy * tile + depth, ax] = P.ROCK[0]
    return cv
