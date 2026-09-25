"""Subset the pixel font to the characters the game actually shows (the full font stays as a lazy fallback)."""
import glob, subprocess, sys

files = glob.glob('data/*.js') + glob.glob('js/*.js') + ['index.html']
chars = set()
for f in files:
    chars |= set(open(f, encoding='utf-8').read())
chars |= {chr(c) for c in range(0x20, 0x7f)}
chars |= set('，。、；：？！…—～·「」『』（）《》〈〉【】“”‘’　▼▶◀▲↑↓←→×０１２３４５６７８９')
chars = sorted(c for c in chars if c >= ' ' and c != '\x7f')
open('/tmp/font_chars.txt', 'w', encoding='utf-8').write(''.join(chars))
print('glyphs requested:', len(chars))
subprocess.check_call([sys.executable, '-m', 'fontTools.subset', 'assets/fonts/fusion-pixel-12px-sc.woff2',
                       '--text-file=/tmp/font_chars.txt', '--flavor=woff2', '--layout-features=*',
                       '--output-file=assets/fonts/fusion-pixel-sub.woff2'])
