"""Extract true-pixel walk frames from generated sprite sheets (solid key background).
Robust to irregular column counts: detects sprites as connected components, clusters them into rows,
splits rows into characters by the largest horizontal gaps."""
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

FW, FH = 26, 38   # output frame size (feet on the bottom row)


def load_key(path):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int32)
    # key colour = median of the border
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    key = np.median(border, axis=0)
    d = np.sqrt(((a - key) ** 2).sum(-1))
    # magenta-ish hue test too, to kill anti-aliased fringes
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    fringe = (r > 150) & (b > 90) & (g < 90) & (np.abs(r - key[0]) < 90)
    fringe2 = (r > g + 45) & (b > g + 35) & (r > 90)
    mask = (d > 100) & ~fringe & ~fringe2
    mask = ndimage.binary_opening(mask, iterations=1)
    return a.astype(np.uint8), mask


def components(mask, min_frac=0.15):
    # merge detached bits (antennas, canes) with a small dilation for labelling only
    lab, n = ndimage.label(ndimage.binary_dilation(mask, iterations=4))
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    big = max(sizes) if len(sizes) else 0
    out = []
    for i, sl in enumerate(objs):
        if sizes[i] < big * min_frac: continue
        ys, xs = sl
        sub = (lab[sl] == i + 1) & mask[sl]
        out.append(dict(y0=ys.start, y1=ys.stop, x0=xs.start, x1=xs.stop, mask=sub,
                        cy=(ys.start + ys.stop) / 2, cx=(xs.start + xs.stop) / 2, h=ys.stop - ys.start))
    return out


def cluster_rows(objs, nrows=4):
    objs = sorted(objs, key=lambda o: o['cy'])
    hs = np.median([o['h'] for o in objs])
    rows, cur = [], [objs[0]]
    for o in objs[1:]:
        if o['cy'] - cur[-1]['cy'] > hs * 0.5:
            rows.append(cur); cur = [o]
        else:
            cur.append(o)
    rows.append(cur)
    return [sorted(r, key=lambda o: o['cx']) for r in rows]


def split_chars(row, nchars):
    if nchars == 1: return [row]
    gaps = [(row[i + 1]['x0'] - row[i]['x1'], i) for i in range(len(row) - 1)]
    cuts = sorted(sorted(gaps, reverse=True)[:nchars - 1], key=lambda g: g[1])
    groups, start = [], 0
    for g, i in cuts:
        groups.append(row[start:i + 1]); start = i + 1
    groups.append(row[start:])
    return groups


def dominant(block):
    keys = (block[:, 0].astype(np.int64) << 16) | (block[:, 1].astype(np.int64) << 8) | block[:, 2]
    vals, counts = np.unique(keys, return_counts=True)
    k = vals[counts.argmax()]
    return np.array([(k >> 16) & 255, (k >> 8) & 255, k & 255], np.uint8)


def reduce(rgb, mask, f):
    """Area-average reduction after edge-preserving colour fill + unsharp mask (keeps eyes readable)."""
    from PIL import ImageFilter
    H, W = mask.shape
    ow, oh = max(1, int(round(W / f))), max(1, int(round(H / f)))
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    filled = rgb[idx[0], idx[1]]
    im = Image.fromarray(filled).filter(ImageFilter.UnsharpMask(radius=2, percent=170, threshold=2))
    small = np.asarray(im.resize((ow, oh), Image.BOX))
    al = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((ow, oh), Image.BOX)) > 115
    out = np.zeros((oh, ow, 4), np.uint8)
    out[..., :3] = small; out[..., 3] = al * 255
    return out


def to_frame(small):
    sh, sw = small.shape[:2]
    top = small[: max(1, int(sh * 0.4)), :, 3] > 0
    xs = np.nonzero(top.any(0))[0]
    cx = (xs.min() + xs.max()) / 2 if len(xs) else sw / 2
    ox = int(round(FW / 2 - 0.5 - cx)); oy = FH - sh
    fr = np.zeros((FH, FW, 4), np.uint8)
    for j in range(sh):
        for i in range(sw):
            if small[j, i, 3] and 0 <= i + ox < FW and 0 <= j + oy < FH:
                fr[j + oy, i + ox] = small[j, i]
    return fr


def outline_fix(fr, dark=(27, 26, 42)):
    """Add a crisp 1px dark outline outside the silhouette."""
    a = fr[..., 3] > 0
    n = np.zeros_like(a)
    n[1:, :] |= a[:-1, :]; n[:-1, :] |= a[1:, :]; n[:, 1:] |= a[:, :-1]; n[:, :-1] |= a[:, 1:]
    n &= ~a
    fr[n, :3] = dark; fr[n, 3] = 255
    return fr


def similarity(a, b):
    ma, mb = a[..., 3] > 0, b[..., 3] > 0
    inter = (ma & mb).sum(); uni = (ma | mb).sum()
    return inter / max(1, uni)


def _hist(rgb, o):
    px = rgb[o['y0']:o['y1'], o['x0']:o['x1']][o['mask']].astype(int)
    q = (px // 64)
    idx = q[:, 0] * 16 + q[:, 1] * 4 + q[:, 2]
    h = np.bincount(idx, minlength=64).astype(float)
    return h / max(1, h.sum())


def _kmeans2(X, iters=20):
    X = np.asarray(X)
    d = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    i, j = np.unravel_index(d.argmax(), d.shape)
    C = np.stack([X[i], X[j]])
    for _ in range(iters):
        lab = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
        for k in range(2):
            if (lab == k).any(): C[k] = X[lab == k].mean(0)
    return lab, C


def extract(path, nchars=1, heights=(30,), colors=32, order=None):
    """order: for 2-char sheets, which k-means cluster is 'A' is decided by mean x (left = A)."""
    rgb, mask = load_key(path)
    objs = components(mask)
    rows = cluster_rows(objs)
    if len(rows) != 4:
        print('WARN', path, 'rows=', len(rows), [len(r) for r in rows])
    rows = rows[:4]
    flat = [o for r in rows for o in r]
    if nchars == 2:
        Wimg = rgb.shape[1]
        H = [_hist(rgb, o) for o in flat]
        for o in flat: o['char'] = 0 if o['cx'] < Wimg / 2 else 1
        for _ in range(2):
            means = [np.mean([h for h, o in zip(H, flat) if o['char'] == k], axis=0) for k in range(2)]
            for h, o in zip(H, flat):
                d_own = np.abs(h - means[o['char']]).sum(); d_oth = np.abs(h - means[1 - o['char']]).sum()
                if d_oth < d_own * 0.6: o['char'] = 1 - o['char']
    else:
        for o in flat: o['char'] = 0
    results = []
    for ci in range(nchars):
        per_row = [[o for o in r if o['char'] == ci] for r in rows]
        allc = [o for r in per_row for o in r]
        hmax = max(o['h'] for o in allc)
        f = hmax / heights[ci]

        def pick(lst):
            if not lst: return None
            if len(lst) >= 3: return lst[:3]
            if len(lst) == 2: return [lst[0], lst[1], lst[0]]
            return [lst[0]] * 3
        print('  ', path.split('/')[-1], 'char', ci, 'per-row', [len(r) for r in per_row])
        down = pick(per_row[0]) or pick(per_row[1]) or pick(per_row[2])
        left = pick(per_row[1]) or pick(per_row[2]) or down
        up = pick(per_row[3]) or down
        grid = []
        for src in (down, left, None, up):
            if src is None:
                grid.append(None); continue
            fr = []
            for o in src:
                crop = rgb[o['y0']:o['y1'], o['x0']:o['x1']]
                fr.append(to_frame(reduce(crop, o['mask'], f)))
            grid.append(fr)
        grid[2] = [fr[:, ::-1].copy() for fr in grid[1]]
        sheet = np.zeros((4 * FH, 3 * FW, 4), np.uint8)
        for ri in range(4):
            for k in range(3):
                sheet[ri * FH:(ri + 1) * FH, k * FW:(k + 1) * FW] = grid[ri][k]
        img = Image.fromarray(sheet, 'RGBA')
        q = img.convert('RGB').quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
        out = np.dstack([np.asarray(q), sheet[..., 3]])
        for ri in range(4):
            for k in range(3):
                outline_fix(out[ri * FH:(ri + 1) * FH, k * FW:(k + 1) * FW])
        results.append(out)
    return results


def erase_face(sheet, skin=None, rows=(0, 1, 2)):
    """Faceless variant: paint over eye/mouth pixels inside the face area with the local skin tone."""
    out = sheet.copy()
    for ri in rows:
        for k in range(3):
            fr = out[ri * FH:(ri + 1) * FH, k * FW:(k + 1) * FW]
            a = fr[..., 3] > 0
            ys = np.nonzero(a.any(1))[0]
            if len(ys) == 0: continue
            top = ys.min(); hh = ys.max() - top
            # head region ~ top 40% of the figure
            y0, y1 = top + int(hh * 0.16), top + int(hh * 0.36)
            px = fr[y0:y1 + 1]
            cols = px[..., :3].reshape(-1, 3)[px[..., 3].reshape(-1) > 0].astype(int)
            if len(cols) == 0: continue
            # skin guess: most common warm light colour
            warm = cols[(cols[:, 0] > 150) & (cols[:, 0] > cols[:, 2] + 20)]
            if len(warm) == 0: continue
            keys, cnt = np.unique(warm, axis=0, return_counts=True)
            sk = keys[cnt.argmax()] if skin is None else np.array(skin)
            for y in range(y0, y1 + 1):
                xs = np.nonzero(fr[y, :, 3] > 0)[0]
                if len(xs) < 3: continue
                for x in range(xs.min() + 2, xs.max() - 1):
                    p = fr[y, x, :3].astype(int)
                    # replace dark / saturated feature pixels (eyes, brows, mouth) flanked by skin
                    lum = p.sum()
                    left = fr[y, max(0, x - 2), :3].astype(int); right = fr[y, min(FW - 1, x + 2), :3].astype(int)
                    near_skin = (np.abs(left - sk).sum() < 90) or (np.abs(right - sk).sum() < 90)
                    if near_skin and np.abs(p - sk).sum() > 60 and not (p[2] > p[0] + 40 and y < y0 + 1):
                        fr[y, x, :3] = sk
    return out


if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1]))
    for item in cfg:
        res = extract(item['src'], len(item['names']), item['heights'])
        for name, arr in zip(item['names'], res):
            Image.fromarray(arr, 'RGBA').save(f"{item.get("out","assets/chars")}/{name}.png")
            print('saved', name)


def erase_face_v2(sheet, rows=(0, 1, 2), keep_eyes=False):
    """Faceless variant: eyes/brows/mouth are holes inside the skin region of the head -> fill them with skin."""
    out = sheet.copy()
    for ri in rows:
        for k in range(3):
            fr = out[ri * FH:(ri + 1) * FH, k * FW:(k + 1) * FW]
            a = fr[..., 3] > 0
            ys = np.nonzero(a.any(1))[0]
            if len(ys) == 0: continue
            top, bot = ys.min(), ys.max()
            y1 = top + int((bot - top) * 0.42)
            reg = fr[top:y1 + 1, :, :3].astype(int)
            ra = a[top:y1 + 1]
            px = reg[ra]
            warm = px[(px[:, 0] > 140) & (px[:, 0] >= px[:, 1]) & (px[:, 1] > px[:, 2]) & (px[:, 0] - px[:, 2] > 25)]
            if len(warm) < 4: continue
            keys, cnt = np.unique(warm, axis=0, return_counts=True)
            sk = keys[cnt.argmax()]
            d = np.abs(reg - sk).sum(-1)
            skin = (d < 70) & ra
            lab, n = ndimage.label(skin)
            if n == 0: continue
            sizes = ndimage.sum(skin, lab, range(1, n + 1))
            face = lab == (int(np.argmax(sizes)) + 1)
            closed = ndimage.binary_closing(face, structure=np.ones((3, 3)), iterations=1)
            filled = ndimage.binary_fill_holes(closed)
            # extend down a row for mouths sitting on the chin edge
            holes = filled & ~face & ra
            if keep_eyes:
                ysH = np.nonzero(holes.any(1))[0]
                if len(ysH):
                    holes[: ysH.min() + 2] = False
            hy, hx = np.nonzero(holes)
            for yy, xx in zip(hy, hx):
                fr[top + yy, xx, :3] = sk
            # soft porcelain highlight on the blank face
            fy, fx = np.nonzero(filled)
            if len(fy):
                cy, cx = int(fy.mean()), int(fx.mean())
                light = np.minimum(255, sk + 14).astype(np.uint8)
                for yy, xx in ((cy, cx), (cy, cx - 1), (cy - 1, cx)):
                    if filled[yy, xx]: fr[top + yy, xx, :3] = light
    return out
