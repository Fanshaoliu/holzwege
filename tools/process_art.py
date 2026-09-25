"""Turn generated illustrations into true-pixel game assets: portraits, battle sprites, CGs, cover."""
import os
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
import sprites as S  # noqa: E402

GEN = 'gen'
OUT = 'assets'
PS = 80  # portrait size

PORTRAIT_SHEETS = [
    ('test_portraits_2x2.png', ['hero', 'chloe', 'tin', 'hof']),
    ('portraits_b.png', ['ister', 'sera', 'deca', 'gest']),
    ('portraits_c.png', ['fried', 'rena', 'otto', 'marta']),
    ('portraits_d.png', ['bato', 'molly', 'hans', 'greta']),
    ('portraits_e.png', ['pip', 'lily', 'priest', 'woodcutter']),
    ('portraits_f.png', ['lucy', 'coinlady', 'museumman', 'echo']),
    ('portraits_g.png', ['faceless', 'knewit', 'youth', 'sailor']),
]


def block_mode(im, ow, oh):
    a = np.asarray(im.convert('RGB'))
    H, W, _ = a.shape
    out = np.zeros((oh, ow, 3), np.uint8)
    ys = np.linspace(0, H, oh + 1).astype(int); xs = np.linspace(0, W, ow + 1).astype(int)
    for j in range(oh):
        for i in range(ow):
            y0, y1, x0, x1 = ys[j], ys[j + 1], xs[i], xs[i + 1]
            dy = max(1, (y1 - y0) // 5); dx = max(1, (x1 - x0) // 5)
            blk = a[y0 + dy:y1 - dy, x0 + dx:x1 - dx].reshape(-1, 3)
            if len(blk) == 0: blk = a[y0:y1, x0:x1].reshape(-1, 3)
            keys = (blk[:, 0].astype(np.int32) << 16) | (blk[:, 1].astype(np.int32) << 8) | blk[:, 2]
            v, c = np.unique(keys, return_counts=True)
            k = v[c.argmax()]
            out[j, i] = ((k >> 16) & 255, (k >> 8) & 255, k & 255)
    return Image.fromarray(out)


def quant(im, n):
    return im.convert('RGB').quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')


def portraits():
    os.makedirs(f'{OUT}/portraits', exist_ok=True)
    for sheet, names in PORTRAIT_SHEETS:
        im = Image.open(f'{GEN}/{sheet}').convert('RGB')
        W, H = im.size
        inset = int(W * 0.012)
        cells = [(0, 0), (1, 0), (0, 1), (1, 1)]
        for (cx, cy), name in zip(cells, names):
            box = (cx * W // 2 + inset, cy * H // 2 + inset, (cx + 1) * W // 2 - inset, (cy + 1) * H // 2 - inset)
            cell = quant(im.crop(box), 72)
            p = quant(block_mode(cell, PS, PS), 48)
            p.save(f'{OUT}/portraits/{name}.png')
    # faceless variants derived from the normal portraits
    for name in ('sera', 'gest'):
        a = np.asarray(Image.open(f'{OUT}/portraits/{name}.png').convert('RGB')).copy()
        Image.fromarray(erase_portrait_face(a)).save(f'{OUT}/portraits/{name}_faceless.png')
    print('portraits done')


def erase_portrait_face(a):
    """Fill eyes/brows/mouth/nose (holes inside the facial skin region) with skin, add porcelain sheen."""
    H, W, _ = a.shape
    reg = a.astype(int)
    # skin: warm light colours
    r, g, b = reg[..., 0], reg[..., 1], reg[..., 2]
    skin = (r > 150) & (r > g) & (g > b) & (r - b > 30) & (r - b < 140)
    skin[int(H * 0.72):] = False
    lab, n = ndimage.label(skin)
    sizes = ndimage.sum(skin, lab, range(1, n + 1))
    face = lab == (int(np.argmax(sizes)) + 1)
    closed = ndimage.binary_closing(face, structure=np.ones((5, 5)), iterations=2)
    filled = ndimage.binary_fill_holes(closed)
    ys, xs = np.nonzero(face)
    keys, cnt = np.unique(reg[face], axis=0, return_counts=True)
    sk = keys[cnt.argmax()]
    out = a.copy()
    holes = filled & ~face
    # smooth the whole face to a soft two-tone blank
    fy, fx = np.nonzero(filled)
    cy, cx = fy.mean(), fx.mean()
    light = np.minimum(255, sk + 18); shade = (sk * 0.86).astype(int)
    for y, x in zip(fy, fx):
        d = (x - cx) + (y - cy) * 0.6
        out[y, x] = light if d < -6 else (shade if d > 9 else sk)
    return out.astype(np.uint8)


MONSTERS = [
    ('monsters_a.png', 'grid2', [('slime', 64), ('bat', 64), ('mask', 76), ('wolf', 84)]),
    ('monsters_b.png', 'halves', [('giant', 112), ('sentinel', 124)]),
    ('monster_noone.png', 'single', [('noone', 150)]),
]


def key_black(a, thr=34):
    dark = a.astype(int).sum(-1) < thr
    lab, n = ndimage.label(dark)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    return ~bg


def monsters():
    os.makedirs(f'{OUT}/monsters', exist_ok=True)
    for sheet, mode, items in MONSTERS:
        im = np.asarray(Image.open(f'{GEN}/{sheet}').convert('RGB'))
        H, W, _ = im.shape
        if mode == 'grid2':
            boxes = [(0, 0, W // 2, H // 2), (W // 2, 0, W, H // 2), (0, H // 2, W // 2, H), (W // 2, H // 2, W, H)]
        elif mode == 'halves':
            boxes = [(0, 0, W // 2, H), (W // 2, 0, W, H)]
        else:
            boxes = [(0, 0, W, H)]
        for (x0, y0, x1, y1), (name, th) in zip(boxes, items):
            cell = im[y0:y1, x0:x1]
            m = key_black(cell)
            m = ndimage.binary_opening(m, iterations=1)
            lab, n = ndimage.label(m)
            sizes = ndimage.sum(m, lab, range(1, n + 1))
            keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.004])
            ys, xs = np.nonzero(keep)
            yy0, yy1, xx0, xx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            crop = cell[yy0:yy1, xx0:xx1]; km = keep[yy0:yy1, xx0:xx1]
            f = (yy1 - yy0) / th
            small = S.reduce(crop, km, f)
            rgb = quant(Image.fromarray(small[..., :3]), 40)
            out = np.dstack([np.asarray(rgb), small[..., 3]])
            S.outline_fix(out, dark=(8, 6, 14))
            Image.fromarray(out, 'RGBA').save(f'{OUT}/monsters/{name}.png')
    print('monsters done')


CGS = ['cg_dream', 'cg_ister', 'cg_core2', 'cg_end1', 'cg_end2b', 'cg_end3b', 'cover_holzwege']
CG_NAMES = {'cg_dream': 'dream', 'cg_ister': 'ister', 'cg_core2': 'core', 'cg_end1': 'end1', 'cg_end2b': 'end2',
            'cg_end3b': 'end3', 'cover_holzwege': 'cover'}


def cgs():
    os.makedirs(f'{OUT}/cg', exist_ok=True)
    for n in CGS:
        im = Image.open(f'{GEN}/{n}.png').convert('RGB')
        im = im.filter(ImageFilter.UnsharpMask(radius=1.5, percent=60, threshold=2))
        small = im.resize((640, 360), Image.BOX)
        q = quant(small, 160)
        q.save(f'{OUT}/cg/{CG_NAMES[n]}.png', optimize=True)
    print('cgs done')


MINIS = [('slime', 17), ('wolf', 22), ('bat', 18), ('mask', 22), ('giant', 44), ('sentinel', 38)]


def minis():
    for name, h in MINIS:
        im = Image.open(f'{OUT}/monsters/{name}.png').convert('RGBA')
        a = np.asarray(im)
        f = im.height / h
        small = S.reduce(a[..., :3].copy(), a[..., 3] > 0, f)
        rgb = quant(Image.fromarray(small[..., :3]), 24)
        out = np.dstack([np.asarray(rgb), small[..., 3]])
        S.outline_fix(out, dark=(8, 6, 14))
        Image.fromarray(out, 'RGBA').save(f'{OUT}/chars/m_{name}.png')
    print('minis done')


if __name__ == '__main__':
    what = sys.argv[1:] or ['portraits', 'monsters', 'cgs', 'minis']
    for w in what: globals()[w]()
