"""Props: trees, bushes, rocks, fences, furniture... Each returns (Canvas, anchor_x, anchor_y)
where the anchor is the pixel (in the canvas) that sits at the TOP-LEFT of the object's base tile."""
import math
from .px import Canvas, rgb, mix, h2, vnoise
from . import pal as P

OUT = P.OUT


def _shade_blob(c, cx, cy, rx, ry, ramp, seed=0, light=(-1, -1)):
    """Draw a shaded leafy blob: dark full shape, lighter shifted layers, leaf specks."""
    c.ellipse(cx, cy, rx, ry, ramp[1])
    c.ellipse(cx - 0.6, cy - 0.8, rx - 1.0, ry - 1.0, ramp[2], only='opaque')
    c.ellipse(cx - 1.4, cy - 1.8, rx - 2.4, ry - 2.4, ramp[3], only='opaque')
    c.ellipse(cx - 2.2, cy - 2.6, max(1, rx - 4.2), max(1, ry - 4.2), ramp[4], only='opaque')


def tree_round(seed=0, ramp=None):
    """DQ6-like rounded deciduous tree, 16x28 canvas, base tile at y=12..27."""
    L = ramp or P.LEAF
    c = Canvas(18, 30)
    # trunk
    c.rect(7, 21, 4, 8, P.WOOD[2]); c.rect(7, 21, 1, 8, P.WOOD[3]); c.rect(10, 22, 1, 7, P.WOOD[1])
    c.px(6, 28, P.WOOD[1]); c.px(11, 28, P.WOOD[1])
    # canopy clumps
    k = seed
    clumps = [(9, 9, 7, 7), (5.5, 14, 4.5, 4.5), (12.5, 14, 4.5, 4.5), (9, 16.5, 6, 4), (9, 5, 5, 4.5)]
    for (cx, cy, rx, ry) in clumps:
        c.ellipse(cx, cy, rx, ry, L[1])
    for (cx, cy, rx, ry) in clumps:
        c.ellipse(cx - 0.8, cy - 1.0, rx - 1.3, ry - 1.3, L[2], only='opaque')
    for (cx, cy, rx, ry) in clumps[:1] + clumps[4:]:
        c.ellipse(cx - 1.4, cy - 1.6, rx - 2.6, ry - 2.6, L[3], only='opaque')
    c.ellipse(5.0, 12.8, 2.2, 2.0, L[3], only='opaque')
    c.ellipse(7.0, 3.6, 2.2, 1.8, L[4], only='opaque')
    c.ellipse(6.2, 7.2, 1.8, 1.6, L[4], only='opaque')
    # leaf specks
    for y in range(c.h):
        for x in range(c.w):
            if c.opaque(x, y) and y < 22:
                r = h2(x, y, 300 + k)
                col = tuple(c.get(x, y))
                if r < 0.10 and col[:3] != tuple(P.WOOD[2][:3]):
                    c.px(x, y, L[4] if y < 12 else L[3])
                elif r > 0.93:
                    c.px(x, y, L[0])
    c.outline(OUT)
    return c, 1, 14


def tree_pine(seed=0):
    L = P.PINE
    c = Canvas(18, 32)
    c.rect(8, 24, 3, 7, P.WOOD[2]); c.rect(8, 24, 1, 7, P.WOOD[3])
    tiers = [(9, 4, 3), (9, 9, 5), (9, 14, 6), (9, 19, 7), (9, 23, 7.5)]
    for (cx, cy, w) in tiers:
        for yy in range(6):
            half = int(w * (yy + 1) / 6)
            y = cy - 3 + yy
            c.hline(int(cx - half), int(cx + half), y, L[1])
    # light side
    for y in range(c.h):
        row = [x for x in range(c.w) if c.opaque(x, y) and y < 24]
        if not row: continue
        x0, x1 = min(row), max(row)
        for x in row:
            t = (x - x0) / max(1, x1 - x0)
            if t < 0.35: c.px(x, y, L[3])
            elif t < 0.6: c.px(x, y, L[2])
            if (y % 5 == 1) and x > x0 and x < x1: c.px(x, y, L[0] if t > 0.5 else L[2])
    c.px(8, 0, L[4]); c.px(9, 0, L[3])
    for y in range(c.h):
        for x in range(c.w):
            if c.opaque(x, y) and y < 24 and h2(x, y, 400 + seed) < 0.07:
                c.px(x, y, L[4])
    c.outline(OUT)
    return c, 1, 16


def tree_dead(seed=0):
    c = Canvas(18, 30)
    W = P.WOOD
    c.rect(8, 10, 3, 19, W[1]); c.rect(8, 10, 1, 19, W[2])
    c.line(9, 14, 3, 7, W[1]); c.line(9, 12, 15, 5, W[1]); c.line(4, 8, 2, 4, W[1]); c.line(14, 6, 16, 2, W[1])
    c.line(9, 18, 14, 13, W[1]); c.line(9, 10, 9, 3, W[1])
    c.outline(OUT)
    return c, 1, 14


def tree_big(seed=0):
    """Large old tree for the clearing: 40x46, base 2 tiles."""
    L = P.LEAF
    c = Canvas(42, 48)
    c.rect(16, 30, 10, 17, P.WOOD[2]); c.rect(16, 30, 3, 17, P.WOOD[3]); c.rect(23, 32, 3, 15, P.WOOD[1])
    c.line(15, 46, 12, 47, P.WOOD[1]); c.line(26, 46, 30, 47, P.WOOD[1])
    clumps = [(21, 14, 15, 11), (10, 22, 9, 7), (32, 22, 9, 7), (21, 26, 13, 7), (21, 7, 10, 6), (12, 12, 7, 6), (30, 12, 7, 6)]
    for cl in clumps: c.ellipse(*cl, L[1])
    for (cx, cy, rx, ry) in clumps: c.ellipse(cx - 1, cy - 1.4, rx - 1.8, ry - 1.8, L[2], only='opaque')
    for (cx, cy, rx, ry) in clumps[:1] + clumps[4:6]: c.ellipse(cx - 2, cy - 2.4, rx - 4, ry - 3.6, L[3], only='opaque')
    c.ellipse(14, 6, 4, 3, L[4], only='opaque'); c.ellipse(9, 10, 3, 2.4, L[4], only='opaque')
    for y in range(c.h):
        for x in range(c.w):
            if c.opaque(x, y) and y < 31:
                r = h2(x, y, 500 + seed)
                if r < 0.08: c.px(x, y, L[4] if y < 18 else L[3])
                elif r > 0.94: c.px(x, y, L[0])
    c.outline(OUT)
    return c, 5, 16


def bush(seed=0, ramp=None, flowers=False):
    L = ramp or P.LEAF
    c = Canvas(16, 16)
    for (cx, cy, rx, ry) in [(8, 9, 7, 5.5), (5, 8, 4, 4), (11, 8, 4, 4), (8, 6, 4.5, 3.5)]:
        c.ellipse(cx, cy, rx, ry, L[1])
    c.ellipse(7.2, 7.8, 5.5, 4.2, L[2], only='opaque')
    c.ellipse(6.5, 6.6, 3.2, 2.6, L[3], only='opaque')
    c.ellipse(5.8, 5.6, 1.4, 1.2, L[4], only='opaque')
    for y in range(16):
        for x in range(16):
            if c.opaque(x, y) and h2(x, y, 600 + seed) < 0.08: c.px(x, y, L[4])
    if flowers:
        for i in range(5):
            x = 3 + int(h2(i, seed, 601) * 10); y = 4 + int(h2(i, seed, 602) * 8)
            if c.opaque(x, y): c.px(x, y, P.FLOWERS[1 + i % 4])
    c.outline(OUT)
    # crop outline overflow
    return c, 0, 0


def rock(seed=0, big=False):
    R = P.STONE
    c = Canvas(16, 16)
    if big:
        c.ellipse(8, 9, 7, 5.5, R[1]); c.ellipse(7, 8, 5.8, 4.4, R[3], only='opaque')
        c.ellipse(6, 7, 3.5, 2.6, R[4], only='opaque'); c.px(5, 6, R[5]); c.px(6, 6, R[5])
        c.line(9, 8, 11, 11, R[2])
    else:
        c.ellipse(8, 11, 4.5, 3.2, R[1]); c.ellipse(7.4, 10.4, 3.4, 2.2, R[3], only='opaque')
        c.px(6, 9, R[4]); c.px(7, 9, R[5])
    c.outline(OUT)
    return c, 0, 0


def stump(seed=0):
    W = P.WOOD
    c = Canvas(16, 16)
    c.ellipse(8, 11, 5, 3, W[1]); c.rect(3, 8, 11, 4, W[2]); c.ellipse(8, 8, 5, 2.4, W[4])
    c.ellipse(8, 8, 3, 1.4, W[3]); c.px(8, 8, W[2])
    c.outline(OUT)
    return c, 0, 0


def flowers(seed=0):
    c = Canvas(16, 16)
    for i in range(7):
        x = 2 + int(h2(i, seed, 700) * 12); y = 3 + int(h2(i, seed, 701) * 11)
        col = P.FLOWERS[int(h2(i, seed, 702) * 5)]
        c.px(x, y + 1, P.GRASS[1]); c.px(x, y, col); c.px(x - 1, y, mix(col, (0, 0, 0), 0.25)); c.px(x + 1, y, col); c.px(x, y - 1, col)
        c.px(x, y, P.FLOWERS[1] if col != P.FLOWERS[1] else P.FLOWERS[0])
    return c, 0, 0


def tallgrass(seed=0):
    c = Canvas(16, 16)
    G = P.GRASS
    for i in range(9):
        x = 1 + int(h2(i, seed, 710) * 14); y = 6 + int(h2(i, seed, 711) * 9)
        c.vline(x, y - 3, y, G[4]); c.px(x, y + 1, G[1]); c.px(x + 1, y - 1, G[3])
    return c, 0, 0


def fence_h(seed=0):
    W = P.WOOD
    c = Canvas(16, 16)
    c.rect(0, 6, 16, 2, W[4]); c.rect(0, 8, 16, 1, W[2]); c.rect(0, 11, 16, 2, W[3]); c.rect(0, 13, 16, 1, W[1])
    for x in (2, 13):
        c.rect(x, 3, 2, 12, W[3]); c.px(x, 3, W[5]); c.vline(x + 1, 4, 14, W[1])
    return c, 0, 0


def fence_v(seed=0):
    W = P.WOOD
    c = Canvas(16, 16)
    c.rect(7, 0, 2, 16, W[3]); c.vline(8, 0, 15, W[1])
    c.rect(6, 5, 4, 2, W[4]); c.rect(6, 12, 4, 2, W[4])
    return c, 0, 0


def signpost(seed=0):
    W = P.WOOD
    c = Canvas(16, 18)
    c.rect(7, 7, 2, 11, W[2]); c.vline(8, 7, 17, W[1])
    c.rect(2, 2, 12, 7, W[3]); c.rect(2, 2, 12, 1, W[5]); c.rect(2, 8, 12, 1, W[1])
    c.hline(4, 11, 4, W[1]); c.hline(4, 9, 6, W[1])
    c.outline(OUT)
    return c, 0, 2


def barrel(seed=0):
    W = P.WOOD
    c = Canvas(16, 18)
    c.ellipse(8, 10, 6, 7.5, W[2]); c.rect(3, 4, 10, 12, W[3]); c.rect(3, 4, 3, 12, W[4])
    c.ellipse(8, 4, 5, 2, W[4]); c.ellipse(8, 4, 3.6, 1.2, W[2])
    for y in (7, 13): c.hline(2, 13, y, P.METAL[2]); c.px(3, y, P.METAL[4])
    c.vline(12, 5, 15, W[1])
    c.outline(OUT)
    return c, 0, 2


def crate(seed=0):
    W = P.WOOD
    c = Canvas(16, 18)
    c.rect(2, 3, 12, 13, W[3]); c.rect(2, 3, 12, 3, W[4])
    c.rect(2, 3, 12, 1, W[5]); c.rect(2, 15, 12, 1, W[1])
    c.line(3, 7, 12, 14, W[2]); c.line(3, 14, 12, 7, W[2])
    c.rect(2, 6, 12, 1, W[1]); c.vline(13, 4, 15, W[1])
    c.outline(OUT)
    return c, 0, 2


def pot(seed=0):
    T_ = P.TERRA
    c = Canvas(16, 18)
    c.ellipse(8, 11, 5.5, 5.5, T_[2]); c.rect(5, 3, 6, 4, T_[2])
    c.ellipse(8, 3, 3.5, 1.3, T_[1]); c.hline(5, 10, 2, T_[4])
    c.ellipse(6.5, 10, 2.2, 3, T_[3], only='opaque'); c.px(5, 8, T_[5]); c.px(5, 9, T_[4])
    c.hline(3, 12, 12, T_[1])
    c.outline(OUT)
    return c, 0, 2


def chest(opened=False):
    W = P.WOOD; G = P.GOLD
    c = Canvas(16, 16)
    if not opened:
        c.rect(2, 5, 12, 10, W[3]); c.rect(2, 5, 12, 4, W[4]); c.rect(2, 5, 12, 1, W[5])
        c.rect(2, 9, 12, 1, W[1]); c.rect(2, 14, 12, 1, W[1])
        c.rect(2, 5, 1, 10, G[3]); c.rect(13, 5, 1, 10, G[2]); c.rect(2, 9, 12, 1, G[2])
        c.rect(7, 8, 2, 3, G[4]); c.px(7, 10, G[1])
    else:
        c.rect(2, 8, 12, 7, W[3]); c.rect(2, 8, 12, 2, W[1]); c.rect(3, 9, 10, 1, (20, 12, 8, 255))
        c.rect(2, 2, 12, 5, W[4]); c.rect(2, 2, 12, 1, W[5]); c.rect(2, 6, 12, 1, W[1])
        c.rect(2, 2, 1, 5, G[3]); c.rect(13, 2, 1, 5, G[2]); c.rect(2, 14, 12, 1, W[1])
    c.outline(OUT)
    return c, 0, 0


def well(seed=0):
    S = P.STONE; W = P.WOOD
    c = Canvas(16, 26)
    c.rect(2, 1, 12, 3, P.TERRA[3]); c.rect(1, 3, 14, 2, P.TERRA[2]); c.hline(2, 13, 1, P.TERRA[5])
    c.rect(3, 5, 1, 10, W[2]); c.rect(12, 5, 1, 10, W[2])
    c.hline(4, 11, 8, W[1]); c.rect(7, 8, 2, 4, W[3]); c.vline(8, 8, 13, P.METAL[3])
    c.ellipse(8, 17, 7, 3, S[1]); c.rect(1, 17, 15, 7, S[3])
    for x in range(1, 16, 4): c.vline(x, 17, 23, S[1])
    c.hline(1, 15, 20, S[2]); c.ellipse(8, 16.5, 5.5, 2, (20, 30, 60, 255)); c.hline(3, 13, 17, S[5])
    c.outline(OUT)
    return c, 0, 10


def lamp(seed=0, lit=False):
    M = P.METAL
    c = Canvas(16, 30)
    c.rect(7, 8, 2, 20, M[1]); c.vline(7, 8, 27, M[3]); c.rect(5, 27, 6, 2, M[1])
    c.rect(4, 2, 8, 7, M[1]); c.rect(5, 3, 6, 5, P.AMBER[3] if lit else P.AMBER[2]); c.rect(5, 3, 2, 5, P.AMBER[4])
    c.hline(3, 12, 1, M[2]); c.px(8, 0, M[3])
    c.outline(OUT)
    return c, 0, 14


def bench(seed=0):
    W = P.WOOD
    c = Canvas(16, 16)
    c.rect(1, 4, 14, 3, W[3]); c.rect(1, 4, 14, 1, W[5]); c.rect(1, 9, 14, 3, W[4]); c.rect(1, 12, 14, 1, W[1])
    c.rect(2, 12, 2, 3, W[1]); c.rect(12, 12, 2, 3, W[1])
    c.outline(OUT)
    return c, 0, 0


def trough(seed=0):
    W = P.WOOD
    c = Canvas(32, 16)
    c.rect(1, 4, 30, 10, W[2]); c.rect(1, 4, 30, 2, W[4]); c.rect(3, 6, 26, 5, P.WATER[3]); c.hline(4, 20, 7, P.WATER[5])
    c.rect(1, 13, 30, 1, W[1]); c.rect(2, 14, 3, 2, W[1]); c.rect(27, 14, 3, 2, W[1])
    c.outline(OUT)
    return c, 0, 0


def anvil(seed=0):
    M = P.METAL
    c = Canvas(16, 16)
    c.rect(2, 4, 12, 3, M[3]); c.rect(1, 4, 3, 2, M[3]); c.rect(2, 4, 12, 1, M[5])
    c.rect(5, 7, 6, 4, M[2]); c.rect(3, 11, 10, 3, P.WOOD[2]); c.rect(3, 11, 10, 1, P.WOOD[4])
    c.outline(OUT)
    return c, 0, 0


def junk(seed=0):
    c = Canvas(16, 16)
    M = P.METAL
    c.ellipse(8, 11, 7, 4, M[1]); c.ellipse(6, 9, 3, 2, M[3]); c.rect(9, 5, 4, 5, P.WOOD[2]); c.line(2, 6, 7, 10, M[4])
    c.ellipse(11, 12, 2, 1.5, P.TERRA[2]); c.px(4, 10, M[5]); c.rect(3, 12, 3, 2, P.WOOD[3])
    c.outline(OUT)
    return c, 0, 0


def grave(seed=0):
    S = P.STONE
    c = Canvas(16, 18)
    c.rect(4, 4, 8, 11, S[3]); c.ellipse(8, 5, 4, 3, S[3]); c.rect(4, 4, 2, 11, S[4])
    c.hline(6, 10, 8, S[1]); c.hline(6, 10, 10, S[1]); c.rect(3, 15, 10, 2, S[2])
    c.outline(OUT)
    return c, 0, 2


def mushroom_patch(seed=0):
    c = Canvas(16, 16)
    for i in range(3):
        x = 3 + int(h2(i, seed, 720) * 10); y = 7 + int(h2(i, seed, 721) * 6)
        c.rect(x, y, 1, 3, P.PLASTER[4]); c.ellipse(x, y, 2, 1.2, P.RED[3]); c.px(x - 1, y - 1, P.FLOWERS[0])
    return c, 0, 0


def log_pile(seed=0):
    W = P.WOOD
    c = Canvas(32, 16)
    for i, (x, y) in enumerate([(3, 10), (11, 10), (19, 10), (27, 10), (7, 5), (15, 5), (23, 5)]):
        c.circle(x, y, 3.4, W[2]); c.circle(x, y, 2.4, W[4]); c.circle(x, y, 1.0, W[3])
    c.outline(OUT)
    return c, 0, 0


def reed(seed=0):
    c = Canvas(16, 16)
    for i in range(6):
        x = 2 + int(h2(i, seed, 730) * 12)
        h = 5 + int(h2(i, seed, 731) * 6)
        c.vline(x, 15 - h, 15, P.GRASS[3]); c.px(x, 15 - h, P.DIRT[2]); c.px(x, 14 - h, P.DIRT[1])
    return c, 0, 0


def statue(seed=0):
    S = P.STONE
    c = Canvas(16, 32)
    c.rect(2, 24, 12, 7, S[2]); c.rect(2, 24, 12, 1, S[4]); c.rect(3, 22, 10, 2, S[3])
    c.ellipse(8, 7, 3, 3, S[3]); c.rect(5, 10, 6, 12, S[3]); c.rect(5, 10, 2, 12, S[4])
    c.line(5, 12, 2, 17, S[3]); c.line(10, 12, 13, 8, S[3])
    c.outline(OUT)
    return c, 0, 16


def fountain(frame=0):
    S = P.MARBLE; W = P.WATER
    c = Canvas(48, 40)
    c.ellipse(24, 27, 22, 11, S[1]); c.ellipse(24, 26, 21, 10, S[3]); c.ellipse(24, 26, 18, 8, W[2])
    for i in range(8):
        x = 10 + int(h2(i, frame, 740) * 28); y = 22 + int(h2(i, frame, 741) * 8)
        c.hline(x, x + 2, y, W[4])
    c.rect(20, 10, 8, 16, S[3]); c.rect(20, 10, 3, 16, S[4]); c.ellipse(24, 10, 7, 3, S[4])
    c.ellipse(24, 9, 5, 2, W[3])
    for k in range(3):
        yy = 2 + ((frame + k) % 3) * 2
        c.px(24 - 3 - k, yy + 3, W[5]); c.px(24 + 3 + k, yy + 3, W[5]); c.px(24, 1 + (frame % 2), W[5])
    c.outline(OUT)
    return c, 0, 8


# ---------------- interior furniture

def bed(color=None):
    W = P.WOOD; B = color or P.TEAL
    c = Canvas(16, 32)
    c.rect(1, 1, 14, 30, W[2]); c.rect(1, 1, 14, 4, W[3]); c.rect(1, 1, 14, 1, W[5])
    c.rect(2, 5, 12, 6, P.PLASTER[4]); c.rect(2, 10, 12, 1, P.PLASTER[1])
    c.rect(2, 11, 12, 18, B[3]); c.rect(2, 11, 12, 2, B[4]); c.rect(2, 28, 12, 1, B[1])
    for y in (15, 20, 25): c.hline(3, 12, y, B[2])
    c.rect(1, 29, 14, 2, W[1])
    c.outline(OUT)
    return c, 0, 16


def table(w=2):
    W = P.WOOD
    c = Canvas(16 * w, 20)
    c.rect(1, 2, 16 * w - 2, 10, W[3]); c.rect(1, 2, 16 * w - 2, 2, W[4]); c.rect(1, 2, 16 * w - 2, 1, W[5])
    c.rect(1, 11, 16 * w - 2, 2, W[1])
    c.rect(2, 13, 2, 6, W[1]); c.rect(16 * w - 4, 13, 2, 6, W[1])
    for x in range(4, 16 * w - 4, 7): c.vline(x, 4, 10, W[2])
    c.outline(OUT)
    return c, 0, 4


def chair(facing='down'):
    W = P.WOOD
    c = Canvas(16, 18)
    if facing == 'down':
        c.rect(3, 1, 10, 7, W[3]); c.rect(3, 1, 10, 1, W[5]); c.rect(3, 8, 10, 4, W[4]); c.rect(3, 12, 10, 1, W[1])
        c.rect(4, 13, 2, 4, W[1]); c.rect(10, 13, 2, 4, W[1])
    else:
        c.rect(3, 7, 10, 4, W[4]); c.rect(3, 11, 10, 1, W[1]); c.rect(4, 12, 2, 5, W[1]); c.rect(10, 12, 2, 5, W[1])
    c.outline(OUT)
    return c, 0, 2


def shelf(books=True):
    W = P.WOOD
    c = Canvas(16, 32)
    c.rect(1, 1, 14, 30, W[2]); c.rect(1, 1, 14, 2, W[4]); c.rect(2, 3, 12, 27, W[1])
    for y in (3, 11, 19):
        c.rect(2, y + 7, 12, 1, W[3])
        if books:
            x = 2
            i = 0
            while x < 14:
                bw = 1 + int(h2(x, y, 800) * 2)
                col = [P.RED[3], P.SLATE_B[3], P.TEAL[3], P.GOLD[3], P.SLATE_P[3], P.WOOD[4]][int(h2(x, y, 801) * 6)]
                bh = 5 + int(h2(x, y, 802) * 2)
                c.rect(x, y + 7 - bh, bw, bh, col); c.px(x, y + 7 - bh, mix(col, (255, 255, 255), 0.4))
                x += bw
                i += 1
        else:
            c.rect(4, y + 3, 3, 4, P.TERRA[3]); c.rect(9, y + 4, 4, 3, P.PLASTER[3])
    c.rect(1, 28, 14, 3, W[2])
    c.outline(OUT)
    return c, 0, 16


def counter(w=3):
    W = P.WOOD
    c = Canvas(16 * w, 24)
    c.rect(0, 2, 16 * w, 6, W[4]); c.rect(0, 2, 16 * w, 1, W[5]); c.rect(0, 8, 16 * w, 14, W[2])
    for x in range(4, 16 * w, 8): c.vline(x, 9, 21, W[1])
    c.rect(0, 21, 16 * w, 2, W[1])
    c.outline(OUT)
    return c, 0, 8


def stove(seed=0):
    S = P.BRICK
    c = Canvas(16, 32)
    c.rect(1, 6, 14, 25, S[2])
    for y in range(8, 30, 4):
        c.hline(1, 14, y, S[1])
        off = 0 if (y // 4) % 2 else 3
        for x in range(1 + off, 15, 6): c.vline(x, y, y + 3, S[1])
    c.rect(4, 18, 8, 8, (30, 16, 10, 255)); c.rect(5, 22, 6, 4, P.AMBER[2]); c.px(7, 21, P.AMBER[3]); c.px(8, 20, P.AMBER[4])
    c.rect(0, 4, 16, 3, P.STONE[3]); c.rect(5, 0, 6, 4, S[1])
    c.outline(OUT)
    return c, 0, 16


def workbench(seed=0):
    W = P.WOOD; M = P.METAL
    c = Canvas(32, 22)
    c.rect(1, 4, 30, 8, W[3]); c.rect(1, 4, 30, 2, W[4]); c.rect(1, 12, 30, 2, W[1])
    c.rect(2, 14, 3, 7, W[1]); c.rect(27, 14, 3, 7, W[1])
    c.rect(5, 2, 7, 3, M[3]); c.rect(15, 3, 2, 3, W[5]); c.rect(20, 2, 6, 2, M[4]); c.line(22, 7, 27, 7, M[2])
    c.outline(OUT)
    return c, 0, 6


def rug(w=3, h=2, ramp=None):
    R = ramp or P.RED
    c = Canvas(16 * w, 16 * h)
    c.rect(1, 1, 16 * w - 2, 16 * h - 2, P.GOLD[3])
    c.rect(3, 3, 16 * w - 6, 16 * h - 6, R[3])
    for y in range(4, 16 * h - 4):
        for x in range(4, 16 * w - 4):
            d = abs((x % 8) - 3.5) + abs((y % 8) - 3.5)
            if d < 1.2: c.px(x, y, R[4])
            elif 2.6 < d < 3.4: c.px(x, y, R[2])
    return c, 0, 0


def fireplace(seed=0):
    S = P.STONE
    c = Canvas(32, 32)
    c.rect(1, 6, 30, 25, S[3]); c.rect(1, 4, 30, 3, S[4]); c.rect(1, 4, 30, 1, S[5])
    for y in range(8, 30, 5): c.hline(1, 30, y, S[2])
    c.rect(8, 14, 16, 16, (26, 14, 10, 255)); c.rect(10, 22, 12, 7, P.AMBER[2]); c.rect(13, 19, 6, 5, P.AMBER[3]); c.rect(15, 17, 2, 3, P.AMBER[4])
    c.outline(OUT)
    return c, 0, 16


def window_curtain(seed=0):
    c = Canvas(16, 16)
    c.rect(2, 2, 12, 11, P.WOOD[1]); c.rect(3, 3, 10, 9, P.WATER[4]); c.rect(3, 3, 3, 3, P.WATER[5])
    c.vline(8, 3, 11, P.WOOD[1]); c.hline(3, 12, 7, P.WOOD[1])
    c.rect(2, 2, 3, 12, P.RED[3]); c.rect(11, 2, 3, 12, P.RED[3])
    return c, 0, 0


def clock_wall(seed=0):
    c = Canvas(16, 16)
    c.circle(8, 8, 6, P.WOOD[2]); c.circle(8, 8, 5, P.PLASTER[4]); c.vline(8, 4, 8, P.OUT); c.hline(8, 11, 8, P.OUT)
    return c, 0, 0


def backup_cell(frame=0, off=False):
    c = Canvas(16, 32)
    c.rect(1, 2, 14, 28, P.MARBLE[2]); c.rect(1, 2, 14, 2, P.MARBLE[5])
    if not off:
        G = P.GLOW
        c.rect(3, 5, 10, 22, G[1])
        for y in range(5, 27):
            t = (y + frame * 2) % 11
            c.hline(3, 12, y, G[2] if t < 4 else (G[3] if t < 6 else G[1]))
        c.ellipse(8, 14, 2.4, 3, G[4]); c.rect(6, 17, 4, 7, G[3])
    else:
        c.rect(3, 5, 10, 22, P.VOID[2])
    c.rect(1, 28, 14, 2, P.MARBLE[1])
    c.outline(OUT)
    return c, 0, 16


def server_rack(frame=0):
    M = P.METAL
    c = Canvas(16, 32)
    c.rect(1, 1, 14, 30, M[1]); c.rect(2, 2, 12, 28, M[0])
    for y in range(4, 28, 4):
        c.hline(2, 13, y, M[2])
        on = h2(y, frame // 2, 900) > 0.4
        c.px(4, y + 2, P.GLOW[3] if on else P.GLOW[0]); c.px(6, y + 2, P.AMBER[3] if h2(y, frame, 901) > 0.6 else P.AMBER[0])
    c.outline(OUT)
    return c, 0, 16


def vending(seed=0):
    c = Canvas(16, 32)
    c.rect(1, 1, 14, 30, P.RED[2]); c.rect(1, 1, 14, 2, P.RED[4])
    c.rect(3, 4, 9, 16, (60, 70, 80, 255))
    for y in range(6, 19, 4):
        for x in range(4, 11, 3): c.rect(x, y, 2, 3, P.SAND[2])
    c.rect(3, 4, 2, 16, (140, 150, 160, 255))
    c.rect(12, 8, 2, 4, P.METAL[4]); c.rect(3, 23, 10, 4, P.VOID[1])
    c.outline(OUT)
    return c, 0, 16


def core_pillar(frame=0, lit=0):
    """Echo's first core: tall pillar with lights, 32x64."""
    M = P.METAL
    c = Canvas(32, 64)
    c.rect(6, 4, 20, 58, M[1]); c.rect(6, 4, 5, 58, M[2]); c.rect(22, 4, 4, 58, M[0])
    c.rect(4, 58, 24, 5, M[2]); c.rect(4, 0, 24, 5, M[2]); c.rect(4, 0, 24, 1, M[4])
    for y in range(8, 56, 3):
        for x in range(9, 23, 3):
            on = h2(x, y, 950 + frame // 3) < lit
            c.px(x, y, P.AMBER[3] if on else M[0])
            if on and h2(x, y, 951) < 0.3: c.px(x, y, P.AMBER[4])
    c.outline(OUT)
    return c, 8, 48


def pedestal(seed=0):
    c = Canvas(16, 20)
    S = P.STONE
    c.rect(3, 6, 10, 13, S[3]); c.rect(2, 4, 12, 3, S[4]); c.rect(3, 6, 2, 13, S[4]); c.rect(2, 18, 12, 2, S[1])
    c.outline(OUT)
    return c, 0, 4


def airship(seed=0):
    c = Canvas(64, 40)
    M = P.METAL
    c.ellipse(32, 14, 30, 11, M[3]); c.ellipse(28, 11, 24, 7, M[4], only='opaque'); c.ellipse(24, 8, 12, 3, M[5], only='opaque')
    for x in range(8, 58, 8): c.vline(x, 5, 23, M[2])
    c.rect(24, 26, 16, 7, P.WOOD[2]); c.rect(24, 26, 16, 2, P.WOOD[4]); c.line(26, 23, 24, 26, M[1]); c.line(38, 23, 40, 26, M[1])
    c.rect(2, 12, 6, 5, M[2])
    c.outline(OUT)
    return c, 0, 24


def boat(seed=0):
    W = P.WOOD
    c = Canvas(32, 16)
    c.ellipse(16, 8, 15, 6, W[1]); c.ellipse(16, 7, 13, 4.5, W[3], only='opaque'); c.ellipse(16, 7, 10, 3, W[2], only='opaque')
    c.hline(6, 26, 7, W[4])
    c.outline(OUT)
    return c, 0, 0


def poster(seed=0):
    c = Canvas(16, 16)
    c.rect(2, 1, 12, 14, P.PLASTER[3]); c.rect(3, 2, 10, 7, P.SLATE_B[2]); c.circle(8, 5, 2.5, P.GLOW[3])
    c.hline(4, 11, 11, P.OUT); c.hline(4, 9, 13, P.OUT)
    return c, 0, 0


def gear_wall(seed=0, size=24):
    M = P.GOLD
    c = Canvas(size, size)
    r = size / 2 - 2
    for a in range(12):
        ang = a * math.pi / 6
        x = size / 2 + math.cos(ang) * (r + 1); y = size / 2 + math.sin(ang) * (r + 1)
        c.rect(int(x) - 1, int(y) - 1, 3, 3, M[2])
    c.circle(size / 2, size / 2, r, M[2]); c.circle(size / 2 - 1, size / 2 - 1, r - 2, M[3], only='opaque')
    c.circle(size / 2, size / 2, r / 3, M[1])
    c.outline(OUT)
    return c, 0, 0


PROPS = {
    'tree': tree_round, 'pine': tree_pine, 'deadtree': tree_dead, 'bigtree': tree_big,
    'bush': lambda s=0: bush(s), 'bushf': lambda s=0: bush(s, flowers=True), 'rock': lambda s=0: rock(s), 'bigrock': lambda s=0: rock(s, True),
    'stump': stump, 'flowers': flowers, 'tallgrass': tallgrass, 'fence_h': fence_h, 'fence_v': fence_v,
    'sign': signpost, 'barrel': barrel, 'crate': crate, 'pot': pot, 'chest': lambda s=0: chest(False), 'chest_open': lambda s=0: chest(True),
    'well': well, 'lamp': lambda s=0: lamp(s, False), 'lamp_lit': lambda s=0: lamp(s, True), 'bench': bench, 'trough': trough, 'anvil': anvil,
    'junk': junk, 'grave': grave, 'mushrooms': mushroom_patch, 'logs': log_pile, 'reed': reed, 'statue': statue,
    'fountain': lambda s=0: fountain(0), 'bed': lambda s=0: bed(None), 'bed_red': lambda s=0: bed(P.RED),
    'table': lambda s=0: table(2), 'table3': lambda s=0: table(3),
    'table1': lambda s=0: table(1), 'chair': lambda s=0: chair('down'), 'chair_up': lambda s=0: chair('up'),
    'shelf': lambda s=0: shelf(True),
    'cupboard': lambda s=0: shelf(False), 'counter': lambda s=0: counter(3), 'counter2': lambda s=0: counter(2), 'stove': stove,
    'workbench': workbench, 'rug': lambda s=0: rug(3, 2), 'rug_b': lambda s=0: rug(3, 2, P.SLATE_B), 'fireplace': fireplace,
    'window': window_curtain, 'wallclock': clock_wall, 'backup': lambda s=0: backup_cell(0), 'backup_off': lambda s=0: backup_cell(0, True),
    'rack': lambda s=0: server_rack(0), 'vending': vending, 'core': lambda s=0: core_pillar(0, 0.0), 'pedestal': pedestal, 'airship': airship,
    'boat': boat, 'poster': poster, 'gear': gear_wall,
}
