"""Losslessly re-encode PNGs with <=256 distinct RGBA colours as indexed PNGs (verified pixel-exact)."""
import glob, io, os, sys
import numpy as np
from PIL import Image


def to_indexed(im):
    rgba = np.array(im.convert('RGBA'))
    flat = rgba.reshape(-1, 4)
    cols, inv = np.unique(flat, axis=0, return_inverse=True)
    if len(cols) > 256:
        return None
    p = Image.fromarray(inv.reshape(rgba.shape[:2]).astype(np.uint8), 'P')
    pal = cols[:, :3].astype(np.uint8).flatten().tolist()
    p.putpalette(pal + [0] * (768 - len(pal)))
    alpha = cols[:, 3].astype(np.uint8)
    if (alpha < 255).any():
        p.info['transparency'] = bytes(alpha.tolist())
    return p, rgba


def main(root):
    before = after = 0
    for path in sorted(glob.glob(os.path.join(root, '**', '*.png'), recursive=True)):
        raw = open(path, 'rb').read()
        before += len(raw)
        im = Image.open(io.BytesIO(raw))
        res = to_indexed(im)
        if res is None:
            after += len(raw); continue
        p, rgba = res
        buf = io.BytesIO()
        p.save(buf, 'PNG', optimize=True, transparency=p.info.get('transparency'))
        data = buf.getvalue()
        back = np.array(Image.open(io.BytesIO(data)).convert('RGBA'))
        same = np.array_equal(back[rgba[..., 3] > 0], rgba[rgba[..., 3] > 0]) and np.array_equal(back[..., 3], rgba[..., 3])
        if same and len(data) < len(raw):
            open(path, 'wb').write(data); after += len(data)
        else:
            after += len(raw)
    print(f'{root}: {before/1024:.0f} KB -> {after/1024:.0f} KB')


if __name__ == '__main__':
    for r in sys.argv[1:] or ['assets']:
        main(r)
