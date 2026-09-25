"""Tiny deterministic pixel-art toolkit on numpy RGBA arrays."""
import numpy as np
from PIL import Image

T = 16  # tile size


def rgb(c):
    if isinstance(c, str):
        c = c.lstrip('#')
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)
    if len(c) == 3:
        return (c[0], c[1], c[2], 255)
    return tuple(c)


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(int(round(int(a[i]) + (int(b[i]) - int(a[i])) * t)) for i in range(3)) + (255,)


def shade(c, k):
    """k<0 darker (cooler), k>0 lighter (warmer). Simple hue-shift ramp step."""
    r, g, b, a = rgb(c)
    if k < 0:
        f = 1 + k
        return (int(r * f * 0.92), int(g * f * 0.96), min(255, int(b * f * 1.04 + 6 * -k)), a)
    f = k
    return (min(255, int(r + (255 - r) * f + 10 * f)), min(255, int(g + (255 - g) * f + 4 * f)), min(255, int(b + (255 - b) * f * 0.7)), a)


def h2(x, y, s=0):
    """Deterministic hash -> [0,1)."""
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF) / float(0x1000000)


def vnoise(x, y, scale, s=0):
    """Value noise in [0,1)."""
    fx, fy = x / scale, y / scale
    x0, y0 = int(np.floor(fx)), int(np.floor(fy))
    tx, ty = fx - x0, fy - y0
    tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
    a = h2(x0, y0, s); b = h2(x0 + 1, y0, s); c = h2(x0, y0 + 1, s); d = h2(x0 + 1, y0 + 1, s)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        if fill is not None:
            self.a[:, :] = rgb(fill)

    @classmethod
    def from_array(cls, arr):
        c = cls(arr.shape[1], arr.shape[0]); c.a = arr.copy(); return c

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            c = rgb(c)
            if c[3] == 255:
                self.a[y, x] = c
            elif c[3] > 0:
                base = self.a[y, x].astype(float); al = c[3] / 255.0
                self.a[y, x, :3] = (base[:3] * (1 - al) + np.array(c[:3]) * al).astype(np.uint8)
                self.a[y, x, 3] = max(self.a[y, x, 3], c[3])

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(self.a[y, x])
        return (0, 0, 0, 0)

    def opaque(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.a[y, x, 3] > 0

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y); x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            c = rgb(c)
            if c[3] == 255:
                self.a[y0:y1, x0:x1] = c
            else:
                for yy in range(y0, y1):
                    for xx in range(x0, x1):
                        self.px(xx, yy, c)

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1): self.px(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1): self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    def ellipse(self, cx, cy, rx, ry, c, only=None):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if rx <= 0 or ry <= 0: continue
                if ((x - cx) / (rx + 0.35)) ** 2 + ((y - cy) / (ry + 0.35)) ** 2 <= 1.0:
                    if only == 'opaque' and not self.opaque(x, y): continue
                    self.px(x, y, c)

    def circle(self, cx, cy, r, c, only=None):
        self.ellipse(cx, cy, r, r, c, only)

    def blit(self, src, x, y, flip=False):
        s = src.a if isinstance(src, Canvas) else src
        if flip: s = s[:, ::-1]
        h, w = s.shape[:2]
        for yy in range(h):
            ty = y + yy
            if ty < 0 or ty >= self.h: continue
            for xx in range(w):
                tx = x + xx
                if tx < 0 or tx >= self.w: continue
                p = s[yy, xx]
                if p[3] == 0: continue
                if p[3] == 255: self.a[ty, tx] = p
                else: self.px(tx, ty, tuple(int(v) for v in p))

    def blit_fast(self, src, x, y):
        s = src.a if isinstance(src, Canvas) else src
        h, w = s.shape[:2]
        x0, y0 = max(0, x), max(0, y); x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0: return
        sub = s[y0 - y:y1 - y, x0 - x:x1 - x]
        m = sub[:, :, 3] > 0
        self.a[y0:y1, x0:x1][m] = sub[m]

    def outline(self, c, where='outside', only_empty=True):
        """1px outline around opaque pixels."""
        m = self.a[:, :, 3] > 0
        c = rgb(c)
        if where == 'outside':
            n = np.zeros_like(m)
            n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
            n &= ~m
            self.a[n] = c
        else:
            e = np.zeros_like(m)
            e[1:, :] |= ~m[:-1, :]; e[:-1, :] |= ~m[1:, :]; e[:, 1:] |= ~m[:, :-1]; e[:, :-1] |= ~m[:, 1:]
            e[0, :] = True; e[-1, :] = True; e[:, 0] = True; e[:, -1] = True
            e &= m
            self.a[e] = c

    def replace(self, old, new):
        old, new = rgb(old), rgb(new)
        m = np.all(self.a == np.array(old, np.uint8), axis=-1)
        self.a[m] = new

    def save(self, path, scale=1):
        im = Image.fromarray(self.a, 'RGBA')
        if scale != 1: im = im.resize((self.w * scale, self.h * scale), Image.NEAREST)
        im.save(path)

    def image(self):
        return Image.fromarray(self.a, 'RGBA')
