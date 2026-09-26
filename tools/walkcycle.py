"""Rebuild the two walking frames of every 3x4 character sheet from its standing frame.

Frame 0 lifts the screen-left leg, frame 2 the screen-right leg, so steps visibly alternate.
The right-facing row stays a mirror of the left-facing row. Originals are read from gen/chars_orig/.
"""
import glob, os, sys
import numpy as np
from PIL import Image

FW, FH = 26, 38
SRC, DST = 'gen/chars_orig', 'assets/chars'


def outline_color(fr):
    a = fr[..., 3] > 0
    edge = []
    for y in range(FH):
        for x in range(FW):
            if not a[y, x]: continue
            if any(not (0 <= y + dy < FH and 0 <= x + dx < FW) or not a[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edge.append(tuple(fr[y, x]))
    vals, counts = np.unique(np.array(edge), axis=0, return_counts=True)
    return vals[counts.argmax()]


def leg_box(fr, side_view):
    a = fr[..., 3] > 0
    ys = np.where(a.any(axis=1))[0]
    top, bottom = ys.min(), ys.max()
    leg_len = max(5, round((bottom - top + 1) * 0.23))
    leg_top = bottom - leg_len + 1
    cols = np.where(a[leg_top:bottom + 1].any(axis=0))[0]
    split = (cols.min() + cols.max() + 1) // 2
    if not side_view:
        # prefer the gap between the feet if there is one
        low = a[bottom - 2:bottom + 1]
        occ = low.any(axis=0)
        inner = [x for x in range(cols.min() + 2, cols.max() - 1) if not occ[x]]
        if inner:
            split = int(round(np.mean(inner)))
    return leg_top, bottom, split


def lift(fr, leg_top, bottom, split, left, oc, amount=2):
    out = fr.copy()
    xs = slice(0, split) if left else slice(split, FW)
    block = fr[leg_top:bottom + 1, xs].copy()
    out[leg_top:bottom + 1, xs] = 0
    dst = out[leg_top - amount:bottom + 1 - amount, xs]
    m = block[..., 3] > 0
    dst[m] = block[m]
    # close the silhouette where the other leg used to cover it
    a = out[..., 3] > 0
    is_oc = np.all(out == oc, axis=2)
    add = []
    for y in range(max(0, leg_top - amount - 1), FH):
        for x in range(FW):
            if a[y, x] or not any(0 <= y + dy < FH and 0 <= x + dx < FW and a[y + dy, x + dx] and not is_oc[y + dy, x + dx]
                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            add.append((y, x))
    for y, x in add:
        out[y, x] = oc
    # body rises one pixel while a foot is in the air; the waist row stretches so the planted leg stays on the ground
    waist = leg_top - amount - 1
    body = out[:waist].copy()
    out[:waist - 1] = body[1:]
    out[waist - 1] = body[-1]
    return out


def process(path_in, path_out):
    im = np.array(Image.open(path_in).convert('RGBA'))
    if im.shape[:2] != (FH * 4, FW * 3):
        return False
    out = im.copy()
    for r in (0, 1, 3):
        stand = im[r * FH:(r + 1) * FH, FW:2 * FW]
        if not (stand[..., 3] > 0).any():
            continue
        oc = outline_color(stand)
        leg_top, bottom, split = leg_box(stand, side_view=(r == 1))
        f0 = lift(stand, leg_top, bottom, split, True, oc)
        f2 = lift(stand, leg_top, bottom, split, False, oc)
        out[r * FH:(r + 1) * FH, 0:FW] = f0
        out[r * FH:(r + 1) * FH, 2 * FW:3 * FW] = f2
    # right-facing row mirrors the left-facing one
    left = out[FH:2 * FH]
    for c in range(3):
        out[2 * FH:3 * FH, c * FW:(c + 1) * FW] = left[:, c * FW:(c + 1) * FW][:, ::-1]
    Image.fromarray(out).save(path_out)
    return True


if __name__ == '__main__':
    names = sys.argv[1:]
    files = [os.path.join(SRC, f'{n}.png') for n in names] if names else sorted(glob.glob(os.path.join(SRC, '*.png')))
    done = 0
    for f in files:
        base = os.path.basename(f)
        if base.startswith('m_'):
            continue
        if process(f, os.path.join(DST, base)):
            done += 1
    print('walk cycles rebuilt:', done)
