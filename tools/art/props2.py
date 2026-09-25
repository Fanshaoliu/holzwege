"""Map-specific props (registered into props.PROPS)."""
import math
from .px import Canvas, mix, h2
from . import pal as P
from .props import PROPS, rock, bed

OUT = P.OUT


def stairs(down=True):
    c = Canvas(16, 16)
    S = P.STONE
    if down:
        c.rect(0, 0, 16, 16, P.VOID[1])
        for i in range(4):
            c.rect(1, 1 + i * 4, 14, 3, S[3 - (i % 2)]); c.hline(1, 14, 1 + i * 4, S[4])
    else:
        W = P.WOOD
        for i in range(4):
            y = 12 - i * 4
            c.rect(2, y, 12, 4, W[3]); c.hline(2, 13, y, W[4]); c.hline(2, 13, y + 3, W[1])
        c.vline(1, 0, 15, W[1]); c.vline(14, 0, 15, W[1])
    return c, 0, 0


def bed_hof(seed=0):
    c, ax, ay = bed(P.SLATE_B)
    # old man's head on the pillow
    c.circle(8, 8, 3.2, (232, 186, 150, 255)); c.ellipse(8, 11, 3.5, 2.2, P.PLASTER[4]); c.px(7, 7, OUT); c.px(9, 7, OUT)
    c.hline(5, 11, 13, P.SLATE_B[4])
    return c, ax, ay


def millstone(seed=0):
    S = P.STONE
    c = Canvas(32, 28)
    c.ellipse(16, 18, 14, 8, S[1]); c.rect(2, 12, 28, 6, S[2]); c.ellipse(16, 12, 14, 7, S[3]); c.ellipse(15, 11, 11, 5, S[4], only='opaque')
    c.ellipse(16, 12, 3, 1.6, S[1]); c.rect(15, 0, 3, 12, P.WOOD[2]); c.rect(4, 2, 24, 3, P.WOOD[3])
    c.outline(OUT)
    return c, 8, 12


def sacks(seed=0):
    c = Canvas(16, 16)
    for (x, y) in ((5, 10), (11, 10), (8, 5)):
        c.ellipse(x, y, 4, 4, P.PLASTER[2]); c.ellipse(x - 1, y - 1, 2.6, 2.6, P.PLASTER[4], only='opaque'); c.px(x, y - 4, P.WOOD[2])
    c.outline(OUT)
    return c, 0, 0


def sluice(seed=0):
    W = P.WOOD; M = P.METAL
    c = Canvas(16, 24)
    c.rect(7, 8, 2, 16, W[2]); c.circle(8, 7, 6, M[1]); c.circle(8, 7, 4.6, M[3]); c.circle(8, 7, 1.5, M[1])
    for a in range(4):
        ang = a * math.pi / 2 + 0.4
        c.line(8, 7, int(8 + math.cos(ang) * 5), int(7 + math.sin(ang) * 5), M[1])
    c.outline(OUT)
    return c, 0, 8


def sluice_gate(open_=False):
    W = P.WOOD
    c = Canvas(48, 20)
    c.rect(0, 2, 4, 18, W[2]); c.rect(44, 2, 4, 18, W[2]); c.rect(0, 0, 48, 4, W[3]); c.hline(0, 47, 0, W[5])
    if not open_:
        for x in range(4, 44, 4):
            c.rect(x, 4, 4, 14, W[3] if (x // 4) % 2 else W[4]); c.vline(x, 4, 17, W[1])
    else:
        c.rect(4, 4, 40, 4, W[3])
    c.outline(OUT)
    return c


def wheel_frame(frame=0):
    W = P.WOOD
    c = Canvas(28, 32)
    cx, cy, r = 14, 16, 13
    c.circle(cx, cy, r, W[1]); c.circle(cx, cy, r - 2, (0, 0, 0, 0))
    for yy in range(32):
        for xx in range(28):
            d = math.hypot(xx - cx, yy - cy)
            if r - 2.2 <= d <= r: c.px(xx, yy, W[2] if d < r - 1 else W[1])
    for k in range(8):
        ang = k * math.pi / 4 + frame * (math.pi / 16)
        x1, y1 = cx + math.cos(ang) * (r - 1), cy + math.sin(ang) * (r - 1)
        c.line(cx, cy, int(round(x1)), int(round(y1)), W[3])
        px, py = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        c.rect(int(px) - 1, int(py) - 1, 3, 3, W[4])
    c.circle(cx, cy, 2.4, P.METAL[2])
    c.outline(OUT)
    return c


def wheel_strip():
    frames = [wheel_frame(i) for i in range(4)]
    c = Canvas(28 * 4, 32)
    for i, f in enumerate(frames): c.blit(f, i * 28, 0)
    return c


def rock_lizard(seed=0):
    c, ax, ay = rock(0, True)
    # tiny lizard basking on top
    G = [(60, 120, 60, 255), (100, 170, 80, 255)]
    c.hline(4, 10, 5, G[0]); c.hline(5, 9, 4, G[1]); c.px(11, 4, G[0]); c.px(12, 3, G[0]); c.px(3, 6, G[0]); c.px(2, 7, G[0])
    c.px(6, 6, G[0]); c.px(8, 6, G[0]); c.px(10, 5, OUT)
    return c, ax, ay


def trapdoor(open_=False):
    W = P.WOOD
    c = Canvas(16, 16)
    if open_:
        c.rect(1, 1, 14, 14, P.VOID[0]); c.rect(2, 2, 12, 3, P.STONE[2]); c.rect(2, 6, 12, 3, P.STONE[1])
    else:
        c.rect(1, 1, 14, 14, W[2])
        for x in range(1, 15, 4): c.vline(x, 1, 14, W[1])
        c.rect(6, 7, 4, 2, P.METAL[3])
    c.outline(OUT)
    return c, 0, 0


def echostone(seed=0):
    c = Canvas(16, 26)
    S = P.STONE
    c.rect(3, 14, 10, 11, S[3]); c.rect(2, 12, 12, 3, S[4]); c.rect(3, 14, 2, 11, S[4])
    c.ellipse(8, 8, 5, 5, S[2]); c.ellipse(7, 7, 3.6, 3.6, S[3], only='opaque')
    for (x, y) in ((6, 6), (9, 8), (7, 10)): c.px(x, y, P.GLOW[2])
    c.outline(OUT)
    return c, 0, 10


def telescope(seed=0):
    M = P.METAL
    c = Canvas(16, 24)
    c.line(4, 22, 8, 12, M[2]); c.line(12, 22, 8, 12, M[2]); c.line(8, 22, 8, 12, M[1])
    c.line(3, 10, 13, 4, P.GOLD[2]); c.line(3, 11, 13, 5, P.GOLD[3]); c.rect(12, 3, 3, 3, P.GOLD[4])
    c.outline(OUT)
    return c, 0, 8


def painting(seed=0):
    c = Canvas(32, 28)
    c.rect(0, 0, 32, 24, P.GOLD[2]); c.rect(2, 2, 28, 20, (58, 48, 34, 255))
    # the peasant shoes
    for (x, y) in ((9, 12), (19, 13)):
        c.ellipse(x, y, 5, 3.5, (104, 70, 40, 255)); c.ellipse(x - 1, y - 1, 3, 2, (70, 46, 26, 255)); c.hline(x - 4, x + 4, y + 3, (40, 26, 16, 255))
    c.hline(4, 27, 18, (84, 64, 40, 255))
    c.outline(OUT)
    return c, 8, 12


def tablet(seed=0, frame=0):
    c = Canvas(32, 24)
    c.rect(2, 10, 28, 12, P.MARBLE[2]); c.rect(2, 10, 28, 2, P.MARBLE[4])
    c.rect(6, 2, 20, 10, P.GLOW[1]); c.rect(7, 3, 18, 8, P.GLOW[2])
    for y in range(4, 10, 2): c.hline(9, 9 + int(h2(y, frame, 3) * 12), y, P.GLOW[4])
    c.outline(OUT)
    return c, 8, 8


def shelf_white(seed=0):
    c = Canvas(16, 32)
    M = P.MARBLE
    c.rect(1, 1, 14, 30, M[3]); c.rect(2, 3, 12, 27, M[1])
    for y in (3, 10, 17, 24):
        c.rect(2, y + 6, 12, 1, M[4])
        for x in range(2, 14, 2):
            c.rect(x, y + 1, 2, 5, M[5] if h2(x, y, seed + 9) > 0.3 else M[4]); c.px(x, y + 1, M[5])
    c.outline(OUT)
    return c, 0, 16


def subway_sign(seed=0):
    c = Canvas(32, 16)
    c.rect(1, 2, 30, 10, P.SLATE_B[1]); c.rect(2, 3, 28, 8, P.SLATE_B[2]); c.circle(7, 7, 3, P.PLASTER[4]); c.hline(12, 26, 6, P.PLASTER[3]); c.hline(12, 22, 8, P.PLASTER[2])
    c.outline(OUT)
    return c, 8, 0


def phone_floor(seed=0):
    c = Canvas(16, 16)
    c.rect(5, 6, 6, 9, (18, 18, 24, 255)); c.rect(6, 7, 4, 7, (40, 44, 58, 255)); c.line(6, 8, 9, 12, P.METAL[4])
    return c, 0, 0


def drawing(seed=0):
    c = Canvas(16, 16)
    c.rect(2, 2, 12, 11, P.PLASTER[4]); c.circle(11, 5, 1.6, P.GOLD[4]); c.rect(4, 7, 2, 4, P.RED[3]); c.circle(5, 6, 1.2, P.SAND[3])
    c.rect(8, 8, 3, 3, P.METAL[3]); c.hline(6, 8, 9, OUT)
    return c, 0, 0


def potter_wheel(seed=0):
    c = Canvas(16, 16)
    c.ellipse(8, 11, 6, 3, P.WOOD[1]); c.ellipse(8, 10, 5, 2.4, P.WOOD[3]); c.rect(6, 5, 4, 5, P.TERRA[3]); c.ellipse(8, 5, 2, 1, P.TERRA[1])
    c.outline(OUT)
    return c, 0, 0


def jugs(seed=0):
    c = Canvas(16, 16)
    for i, (x, y) in enumerate(((4, 10), (9, 11), (13, 9))):
        col = [P.TERRA[3], P.SAND[2], P.TERRA[2]][i]
        c.ellipse(x, y, 3, 3.5, col); c.rect(x - 1, y - 6, 2, 3, col); c.px(x - 1, y - 1, mix(col, (255, 255, 255), 0.3))
    c.outline(OUT)
    return c, 0, 0


def clock_shelf(seed=0):
    c = Canvas(16, 32)
    W = P.WOOD
    c.rect(1, 1, 14, 30, W[2]); c.rect(2, 2, 12, 28, W[1])
    for y in (4, 12, 20):
        c.rect(2, y + 6, 12, 1, W[3])
        for x in (5, 11):
            c.circle(x, y + 3, 2.4, P.GOLD[3]); c.circle(x, y + 3, 1.6, P.PLASTER[4]); c.px(x, y + 2, OUT)
    c.outline(OUT)
    return c, 0, 16


def gear_big(frame=0):
    c = Canvas(32, 32)
    G = P.GOLD
    cx = cy = 16; r = 11
    for a in range(10):
        ang = a * math.pi / 5 + frame * 0.2
        x = cx + math.cos(ang) * (r + 2); y = cy + math.sin(ang) * (r + 2)
        c.rect(int(x) - 2, int(y) - 2, 4, 4, G[2])
    c.circle(cx, cy, r, G[2]); c.circle(cx - 1, cy - 1, r - 2, G[3], only='opaque'); c.circle(cx, cy, 4, G[1]); c.circle(cx, cy, 2, G[4])
    c.outline(OUT)
    return c, 8, 16


def kiosk(seed=0):
    c = Canvas(16, 28)
    c.rect(3, 8, 10, 19, P.MARBLE[3]); c.rect(4, 10, 8, 7, P.GLOW[2]); c.rect(1, 4, 14, 5, P.SLATE_B[3]); c.hline(1, 14, 4, P.SLATE_B[5])
    c.outline(OUT)
    return c, 0, 12


def lamp_white(seed=0):
    c = Canvas(16, 30)
    M = P.MARBLE
    c.rect(7, 8, 2, 20, M[3]); c.rect(5, 27, 6, 2, M[2]); c.circle(8, 5, 4, P.GLOW[3]); c.circle(8, 5, 2.4, P.GLOW[4])
    c.outline(OUT)
    return c, 0, 14


def banner(seed=0):
    c = Canvas(16, 30)
    c.vline(3, 0, 29, P.GOLD[3]); c.rect(4, 2, 10, 16, P.SLATE_B[3]); c.hline(4, 13, 2, P.GOLD[4])
    c.circle(9, 9, 3, P.GOLD[4]); c.circle(9, 9, 1.5, P.SLATE_B[3])
    for x in range(4, 14, 2): c.px(x, 18, P.SLATE_B[3])
    c.outline(OUT)
    return c, 0, 14


def bell_pedestal(seed=0):
    c = Canvas(16, 22)
    S = P.STONE
    c.rect(3, 10, 10, 11, S[3]); c.rect(2, 9, 12, 2, S[4])
    c.ellipse(8, 5, 3.5, 4, P.GOLD[3]); c.rect(4, 7, 8, 2, P.GOLD[2]); c.px(7, 3, P.GOLD[5])
    c.outline(OUT)
    return c, 0, 6


def desk(seed=0):
    W = P.WOOD
    c = Canvas(32, 22)
    c.rect(1, 3, 30, 9, W[3]); c.rect(1, 3, 30, 2, W[4]); c.rect(1, 12, 30, 8, W[2]); c.rect(4, 14, 8, 5, W[1]); c.rect(20, 14, 8, 5, W[1])
    c.rect(6, 1, 7, 3, P.PLASTER[4]); c.rect(18, 0, 2, 4, P.GOLD[3]); c.rect(22, 1, 5, 3, P.GLOW[2])
    c.outline(OUT)
    return c, 0, 6


def book_pile(seed=0):
    c = Canvas(16, 16)
    for i in range(4):
        col = [P.RED[3], P.SLATE_B[3], P.TEAL[3], P.GOLD[3]][i]
        c.rect(3 + (i % 2), 12 - i * 3, 10, 3, col); c.hline(3 + (i % 2), 12 + (i % 2), 12 - i * 3, mix(col, (255, 255, 255), 0.35))
    c.outline(OUT)
    return c, 0, 0


def cage_bird(seed=0):
    c = Canvas(16, 20)
    c.ellipse(8, 10, 5, 7, P.GOLD[2]); c.ellipse(8, 10, 4, 6, (0, 0, 0, 0))
    for yy in range(4, 17):
        for xx in range(3, 14):
            if ((xx - 8) / 5) ** 2 + ((yy - 10) / 7) ** 2 <= 1 and xx % 2 == 0: c.px(xx, yy, P.GOLD[2])
    c.ellipse(8, 12, 2, 1.6, P.STONE[3])
    c.outline(OUT)
    return c, 0, 4


# ---------------- world map props
def wtrees(seed=0):
    c = Canvas(16, 16)
    L = P.LEAF
    for (x, y, r) in ((5, 6, 4), (11, 5, 4), (8, 11, 4.5)):
        c.circle(x, y, r, L[1]); c.circle(x - 0.8, y - 0.8, r - 1.4, L[3], only='opaque'); c.px(int(x - 1), int(y - 2), L[4])
    c.outline(OUT)
    return c, 0, 0


def wtrees_dark(seed=0):
    c = Canvas(16, 16)
    L = P.PINE
    for (x, y) in ((4, 9), (9, 7), (13, 10), (7, 13)):
        for yy in range(5):
            c.hline(x - yy // 2 - 1, x + yy // 2 + 1, y - 4 + yy, L[1] if yy % 2 else L[2])
        c.px(x, y - 5, L[3])
    c.outline(OUT)
    return c, 0, 0


def mountain(seed=0):
    c = Canvas(16, 16)
    R = P.ROCK
    for yy in range(14):
        half = int((yy + 1) * 0.6)
        c.hline(8 - half, 8 + half, yy + 1, R[2])
        c.hline(8 - half, 8, yy + 1, R[3])
    c.px(8, 1, P.PLASTER[4]); c.hline(7, 9, 2, P.PLASTER[4]); c.hline(6, 8, 3, P.PLASTER[3])
    c.line(8, 4, 11, 14, R[1])
    c.outline(OUT)
    return c, 0, 0


def town_icon(kind='village'):
    c = Canvas(32, 32)
    if kind == 'village':
        for (x, y, col) in ((4, 12, P.THATCH), (16, 8, P.TERRA), (12, 18, P.THATCH)):
            c.rect(x, y + 6, 12, 7, P.PLASTER[3]); c.rect(x + 4, y + 9, 3, 4, P.WOOD[2])
            for i in range(7): c.hline(x + 6 - i - 1, x + 6 + i, y + i, col[3] if i % 2 else col[2])
    elif kind == 'harbor':
        c.rect(12, 2, 8, 22, P.STONE[3]); c.circle(16, 8, 3, P.PLASTER[4]); c.rect(11, 0, 10, 3, P.TEAL[3])
        c.rect(2, 16, 10, 8, P.PLASTER[3]); c.rect(20, 16, 10, 8, P.PLASTER[3])
        for i in range(5): c.hline(7 - i, 7 + i, 11 + i, P.SLATE_B[3]); c.hline(25 - i, 25 + i, 11 + i, P.SLATE_B[3])
        c.rect(0, 26, 32, 5, P.WATER[3])
    elif kind == 'capital':
        c.rect(2, 12, 28, 16, P.MARBLE[3]); c.rect(2, 12, 28, 2, P.MARBLE[5])
        for x in (4, 13, 22):
            c.rect(x, 2, 6, 12, P.MARBLE[4]); c.rect(x, 0, 6, 3, P.SLATE_B[3])
        c.rect(13, 20, 6, 8, P.SLATE_B[1])
    elif kind == 'forest':
        for (x, y) in ((8, 14), (16, 10), (24, 14), (12, 22), (20, 22)):
            for yy in range(8): c.hline(x - yy // 2 - 1, x + yy // 2 + 1, y - 7 + yy, P.PINE[1] if yy % 2 else P.PINE[2])
        c.circle(16, 17, 3, P.AMBER[3])
    c.outline(OUT)
    return c, 8, 16


PROPS.update({
    'stairs_down': lambda s=0: stairs(True), 'stairs_up': lambda s=0: stairs(False), 'bed_hof': bed_hof,
    'millstone': millstone, 'sacks': sacks, 'sluice': sluice, 'rock_lizard': rock_lizard,
    'trapdoor': lambda s=0: trapdoor(False), 'trapdoor_open': lambda s=0: trapdoor(True), 'echostone': echostone,
    'telescope': telescope, 'painting': painting, 'tablet': tablet, 'shelf_white': shelf_white,
    'subway_sign': subway_sign, 'phone_floor': phone_floor, 'drawing': drawing, 'potter_wheel': potter_wheel,
    'jugs': jugs, 'clock_shelf': clock_shelf, 'gear_big': gear_big, 'kiosk': kiosk, 'lamp_white': lamp_white,
    'banner': banner, 'bell_pedestal': bell_pedestal, 'desk': desk, 'book_pile': book_pile, 'cage': cage_bird,
    'wtrees': wtrees, 'wtrees_dark': wtrees_dark, 'mountain': mountain,
    'town_village': lambda s=0: town_icon('village'), 'town_harbor': lambda s=0: town_icon('harbor'),
    'town_capital': lambda s=0: town_icon('capital'), 'town_forest': lambda s=0: town_icon('forest'),
})
