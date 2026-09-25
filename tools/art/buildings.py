"""Parametric SFC-style buildings. A building occupies a rectangular footprint of w x (roof_h+wall_h) tiles.
The canvas has TOP extra pixels above the footprint for chimneys / spires (drawn in the 'above' layer)."""
import math
from .px import Canvas, rgb, mix, h2
from . import pal as P

TOP = 12
OUT = P.OUT

ROOFS = {'thatch': P.THATCH, 'slate_b': P.SLATE_B, 'slate_p': P.SLATE_P, 'terra': P.TERRA, 'teal': P.TEAL,
         'moss': [rgb(c) for c in ('#16261a', '#24402a', '#355c36', '#4e7a40', '#74a052', '#a6c878')],
         'gold': P.GOLD, 'white': P.MARBLE}


def _roof(c, x0, y0, w, h, style, seed):
    R = ROOFS[style]
    if style == 'thatch':
        for y in range(h):
            row = y // 4; yy = y % 4
            for x in range(w):
                col = R[3]
                if yy == 0: col = R[4]
                if yy == 3: col = R[1]
                if yy in (1, 2) and h2(x, row, seed + 1) < 0.3: col = R[2]
                if yy == 1 and h2(x, row, seed + 2) < 0.12: col = R[5]
                c.px(x0 + x, y0 + y, col)
    elif style in ('slate_b', 'slate_p', 'teal', 'moss', 'white'):
        for y in range(h):
            row = y // 3; yy = y % 3
            off = (row % 2) * 2
            for x in range(w):
                xx = (x + off) % 4
                k = h2((x + off) // 4, row, seed + 3)
                base = R[3] if k > 0.35 else R[2]
                col = base
                if yy == 0: col = R[4] if xx < 3 else R[2]
                if yy == 2 or xx == 3: col = R[1]
                if yy == 0 and xx == 0 and k > 0.7: col = R[5]
                if style == 'moss' and h2(x, y, seed + 4) < 0.12: col = P.LEAF[3]
                c.px(x0 + x, y0 + y, col)
    elif style in ('terra', 'gold'):
        for y in range(h):
            yy = y % 5
            for x in range(w):
                xx = x % 4
                col = [R[2], R[3], R[4], R[3]][xx]
                if yy == 4: col = R[1]
                if yy == 0 and xx == 2: col = R[5]
                c.px(x0 + x, y0 + y, col)
    # ridge cap
    for x in range(w):
        if style == 'thatch':
            wav = int(1 + math.sin((x + seed) * 0.9) * 1.2)
            for y in range(0, 3 + wav):
                c.px(x0 + x, y0 + y, R[2] if y > wav else R[4])
            c.px(x0 + x, y0 + 3 + wav, R[1])
        else:
            c.px(x0 + x, y0, P.STONE[4]); c.px(x0 + x, y0 + 1, P.STONE[3]); c.px(x0 + x, y0 + 2, P.STONE[1])
    # eave
    for x in range(w):
        c.px(x0 + x, y0 + h - 2, R[1]); c.px(x0 + x, y0 + h - 1, OUT)
    # verges
    for y in range(h):
        c.px(x0, y0 + y, OUT); c.px(x0 + w - 1, y0 + y, OUT)
        c.px(x0 + 1, y0 + y, mix(R[1], OUT, 0.3))


def _dormer(c, x, y, style):
    R = ROOFS[style]
    for i in range(6):
        c.hline(x + 6 - i - 1, x + 6 + i, y + i, R[1])
    c.hline(x + 1, x + 10, y + 5, OUT)
    c.rect(x + 3, y + 6, 6, 5, P.WOOD[1]); c.rect(x + 4, y + 7, 4, 4, P.WATER[3]); c.px(x + 4, y + 7, P.WATER[5])
    c.hline(x + 2, x + 9, y + 11, R[1])


def _wall(c, x0, y0, w, h, style, seed, posts=True):
    if style == 'plaster':
        c.rect(x0, y0, w, h, P.PLASTER[3])
        for y in range(h):
            for x in range(w):
                if h2(x0 + x, y0 + y, seed + 5) < 0.05: c.px(x0 + x, y0 + y, P.PLASTER[2])
        # timber frame
        c.rect(x0, y0, w, 3, P.TIMBER[2]); c.hline(x0, x0 + w - 1, y0, P.TIMBER[3])
        if posts:
            xs = [x0, x0 + w - 3] + [x for x in range(x0 + 30, x0 + w - 8, 32)]
            for x in xs:
                c.rect(x, y0, 3, h, P.TIMBER[2]); c.vline(x, y0, y0 + h - 1, P.TIMBER[3])
            for i in range(len(xs) - 1):
                pass
        c.rect(x0, y0 + h - 4, w, 4, P.STONE[2]); c.hline(x0, x0 + w - 1, y0 + h - 4, P.STONE[4])
        for x in range(x0, x0 + w, 5): c.vline(x, y0 + h - 3, y0 + h - 1, P.STONE[1])
    elif style in ('stone', 'marble', 'brick'):
        S = {'stone': P.STONE, 'marble': P.MARBLE, 'brick': P.BRICK}[style]
        bw, bh = (8, 5) if style != 'brick' else (6, 3)
        for y in range(h):
            row = y // bh
            off = (row % 2) * (bw // 2)
            for x in range(w):
                xx = (x + off) % bw; yy = y % bh
                k = h2((x + off) // bw, row, seed + 6)
                col = S[3] if k > 0.4 else mix(S[3], S[2], 0.5)
                if yy == bh - 1 or xx == bw - 1: col = S[1]
                elif yy == 0: col = mix(col, S[4], 0.6)
                c.px(x0 + x, y0 + y, col)
        if style == 'marble':
            for x in [x0] + list(range(x0 + 16, x0 + w - 4, 24)) + [x0 + w - 4]:
                c.rect(x, y0, 4, h, P.MARBLE[4]); c.vline(x, y0, y0 + h - 1, P.MARBLE[5]); c.vline(x + 3, y0, y0 + h - 1, P.MARBLE[1])
            c.rect(x0, y0, w, 3, P.MARBLE[4]); c.hline(x0, x0 + w - 1, y0 + 2, P.MARBLE[1])
    elif style == 'wood':
        for x in range(w):
            xx = x % 5
            col = P.WOOD[3] if h2(x // 5, 0, seed + 7) > 0.5 else P.WOOD[2]
            for y in range(h):
                cc = col
                if xx == 4: cc = P.WOOD[1]
                elif xx == 0: cc = mix(col, P.WOOD[4], 0.5)
                c.px(x0 + x, y0 + y, cc)
        c.rect(x0, y0, w, 3, P.TIMBER[2])
        c.rect(x0, y0 + h - 3, w, 3, P.STONE[2])
    elif style == 'log':
        for y in range(h):
            yy = y % 5
            for x in range(w):
                col = [P.WOOD[4], P.WOOD[3], P.WOOD[3], P.WOOD[2], P.WOOD[1]][yy]
                if h2(x, y // 5, seed + 8) < 0.06 and yy in (1, 2): col = P.WOOD[2]
                c.px(x0 + x, y0 + y, col)
        for y in range(0, h, 5):
            for (xe) in (x0, x0 + w - 4):
                c.rect(xe, y0 + y, 4, 4, P.WOOD[4]); c.px(xe + 1, y0 + y + 1, P.WOOD[2]); c.px(xe + 2, y0 + y + 2, P.WOOD[2])
    # shadow under eave
    c.hline(x0, x0 + w - 1, y0, mix(OUT, P.TIMBER[1], 0.3))
    c.hline(x0, x0 + w - 1, y0 + 1, mix(c.get(x0 + 3, y0 + 1), OUT, 0.35))
    c.vline(x0, y0, y0 + h - 1, OUT); c.vline(x0 + w - 1, y0, y0 + h - 1, OUT)


def _door(c, x, ybot, h=22, style='wood', arch=True):
    W = P.WOOD
    x0 = x + 2; w = 12
    y0 = ybot - h
    c.rect(x0 - 1, y0 - 1, w + 2, h + 1, P.STONE[1] if style != 'dark' else OUT)
    fill = W[3] if style != 'dark' else (24, 18, 30, 255)
    c.rect(x0, y0, w, h, fill)
    if arch:
        for i in range(3):
            c.px(x0 + i, y0 + (2 - i), P.STONE[1]); c.px(x0 + w - 1 - i, y0 + (2 - i), P.STONE[1])
        c.px(x0, y0, P.STONE[1]); c.px(x0 + w - 1, y0, P.STONE[1])
    if style != 'dark':
        for xx in range(x0 + 2, x0 + w, 3): c.vline(xx, y0 + 2, ybot - 1, W[2])
        c.vline(x0 + 1, y0 + 2, ybot - 1, W[4])
        for yy in (y0 + h // 3, y0 + 2 * h // 3): c.hline(x0, x0 + w - 1, yy, P.METAL[2])
        c.px(x0 + w - 3, y0 + h // 2, P.GOLD[4]); c.px(x0 + w - 3, y0 + h // 2 + 1, P.GOLD[2])
    c.hline(x0 - 1, x0 + w, ybot - 1, OUT)


def _window(c, x, y, shutters=True, flowers=True, glow=False):
    W = P.WOOD
    c.rect(x + 2, y, 12, 11, W[1])
    glass = P.AMBER[3] if glow else P.WATER[3]
    c.rect(x + 3, y + 1, 10, 9, glass)
    c.rect(x + 3, y + 1, 4, 3, P.AMBER[4] if glow else P.WATER[5])
    c.vline(x + 8, y + 1, y + 9, W[1]); c.hline(x + 3, x + 12, y + 5, W[1])
    if shutters:
        c.rect(x, y, 2, 11, W[3]); c.rect(x + 14, y, 2, 11, W[3])
        c.vline(x + 1, y, y + 10, W[2]); c.vline(x + 15, y, y + 10, W[2])
    if flowers:
        c.rect(x + 2, y + 11, 12, 3, W[2]); c.hline(x + 2, x + 13, y + 11, W[4])
        for i in range(5):
            c.px(x + 3 + i * 2, y + 10, P.FLOWERS[1 + i % 4]); c.px(x + 4 + i * 2, y + 10, P.GRASS[3])


def _chimney(c, x, ytop, height, style='brick'):
    S = P.BRICK if style == 'brick' else P.STONE
    c.rect(x, ytop, 7, height, S[2])
    for y in range(ytop + 2, ytop + height, 3): c.hline(x, x + 6, y, S[1])
    c.rect(x - 1, ytop, 9, 2, S[3]); c.hline(x - 1, x + 7, ytop, S[4])
    c.rect(x + 1, ytop + 2, 1, height - 2, S[3])
    for yy in range(ytop, ytop + height): c.px(x - 1 if yy > ytop + 1 else x - 2, yy, OUT); c.px(x + 7, yy, OUT)
    c.hline(x - 2, x + 8, ytop - 1, OUT)


SIGNS = {}


def _sign(c, x, y, kind):
    W = P.WOOD
    c.hline(x - 2, x + 6, y, P.METAL[1]); c.vline(x + 6, y, y + 2, P.METAL[1])
    c.rect(x, y + 2, 11, 9, W[4]); c.rect(x, y + 2, 11, 1, W[5]); c.rect(x, y + 10, 11, 1, W[1])
    c.vline(x, y + 2, y + 10, W[2]); c.vline(x + 10, y + 2, y + 10, W[2])
    cx, cy = x + 5, y + 6
    if kind == 'cup':
        c.rect(cx - 2, cy - 2, 4, 5, P.PLASTER[4]); c.px(cx + 2, cy - 1, P.PLASTER[4]); c.px(cx + 3, cy, P.PLASTER[4]); c.px(cx + 2, cy + 1, P.PLASTER[4])
        c.hline(cx - 2, cx + 1, cy - 2, P.PLASTER[2])
    elif kind == 'tool':
        c.line(cx - 3, cy + 3, cx + 2, cy - 2, P.METAL[3]); c.rect(cx + 1, cy - 3, 3, 2, P.METAL[4])
    elif kind == 'clock':
        c.circle(cx, cy, 3, P.PLASTER[4]); c.vline(cx, cy - 2, cy, OUT); c.hline(cx, cx + 2, cy, OUT)
    elif kind == 'pot':
        c.ellipse(cx, cy + 1, 3, 2.5, P.TERRA[3]); c.rect(cx - 1, cy - 3, 3, 2, P.TERRA[3])
    elif kind == 'book':
        c.rect(cx - 3, cy - 2, 6, 5, P.RED[3]); c.vline(cx, cy - 2, cy + 2, P.GOLD[4])
    elif kind == 'echo':
        c.circle(cx, cy, 3, P.GLOW[2]); c.circle(cx, cy, 1.5, P.GLOW[4])
    elif kind == 'inn':
        c.rect(cx - 3, cy, 7, 3, P.SLATE_B[3]); c.rect(cx - 3, cy - 2, 3, 2, P.PLASTER[4])
    elif kind == 'star':
        c.px(cx, cy - 3, P.GOLD[4]); c.hline(cx - 3, cx + 3, cy, P.GOLD[4]); c.vline(cx, cy - 3, cy + 3, P.GOLD[4])


def house(w=5, roof_h=3, wall_h=2, roof='thatch', wall='plaster', doors=(2,), windows=(), chimney=None,
          sign=None, sign_col=None, dormers=(), seed=0, door_style='wood', glow=False, flowers=True):
    W, Hh = w * 16, (roof_h + wall_h) * 16
    c = Canvas(W, Hh + TOP)
    y_roof = TOP
    y_wall = TOP + roof_h * 16
    _roof(c, 0, y_roof, W, roof_h * 16 + 2, roof, seed)
    for d in dormers:
        _dormer(c, d * 16 + 2, y_roof + 7, roof)
    _wall(c, 1, y_wall + 1, W - 2, wall_h * 16 - 1, wall, seed)
    ybot = TOP + Hh
    for wc in windows:
        _window(c, wc * 16, y_wall + (wall_h * 16) // 2 - 7 + (2 if wall_h == 1 else 0), flowers=flowers, glow=glow)
    for dc in doors:
        _door(c, dc * 16, ybot, h=min(22, wall_h * 16 - 3), style=door_style)
    if chimney is not None:
        _chimney(c, chimney * 16 + 4, TOP - 8, 8 + 10, 'brick' if roof != 'thatch' else 'stone')
    if sign:
        sc = sign_col if sign_col is not None else (doors[0] + 1 if doors else 1)
        _sign(c, sc * 16 + 3, y_wall + 3, sign)
    c.hline(0, W - 1, ybot - 1, OUT)
    return c


def clock_tower(frame_time=None, stopped=True):
    """3 tiles wide, 9 tall footprint."""
    w, h = 3, 9
    W, Hh = w * 16, h * 16
    c = Canvas(W, Hh + TOP + 10)
    y0 = TOP + 10
    # spire (teal)
    R = P.TEAL
    for i in range(34):
        half = int(i * 0.72)
        c.hline(24 - half, 23 + half, i, R[2] if i % 4 else R[1])
        c.hline(24 - half, 24 - half + max(0, half // 3), i, R[4])
    c.px(23, 0, P.GOLD[4]); c.px(24, 0, P.GOLD[4])
    for i in range(34): c.px(24 - int(i * 0.72) - 1, i, OUT); c.px(23 + int(i * 0.72) + 1, i, OUT)
    c.hline(0, 47, 34, OUT)
    # tower body
    _wall(c, 2, 35, W - 4, Hh + TOP + 10 - 35, 'stone', 7, posts=False)
    # clock face
    cx, cy = 24, 52
    c.circle(cx, cy, 11, P.GOLD[2]); c.circle(cx, cy, 10, P.PLASTER[4]); c.circle(cx, cy, 9, P.PLASTER[3])
    for a in range(12):
        ang = a * math.pi / 6
        c.px(int(round(cx + math.cos(ang) * 8)), int(round(cy + math.sin(ang) * 8)), OUT)
    # hands: 10:10 when stopped
    c.line(cx, cy, cx - 5, cy - 3, OUT); c.line(cx, cy, cx + 5, cy - 4, OUT); c.px(cx, cy, P.GOLD[4])
    # windows & door
    for yy in (75, 100):
        c.rect(20, yy, 8, 12, OUT); c.rect(21, yy + 1, 6, 11, P.AMBER[2] if yy == 100 else P.WATER[2])
        c.px(21, yy + 1, OUT); c.px(26, yy + 1, OUT)
    _door(c, 16, Hh + TOP + 10, h=24)
    c.hline(0, W - 1, Hh + TOP + 9, OUT)
    return c


def city_wall_segment(w=1, h=3):
    S = P.MARBLE
    c = Canvas(w * 16, h * 16 + TOP)
    _wall(c, 0, TOP + 6, w * 16, h * 16 - 6, 'marble', 3, posts=False)
    for x in range(0, w * 16, 8):
        c.rect(x, TOP, 5, 7, S[3]); c.hline(x, x + 4, TOP, S[5]); c.vline(x + 4, TOP, TOP + 6, S[1])
    c.hline(0, w * 16 - 1, TOP + h * 16 - 1, OUT)
    return c


def hut():
    return house(w=4, roof_h=2, wall_h=2, roof='moss', wall='log', doors=(1,), windows=(3,), chimney=2, seed=5, flowers=False)
