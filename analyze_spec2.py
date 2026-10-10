#!/usr/bin/env python3
"""Zoom into the bright regions of the spectrogram."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape

# Examine band 0 (top of image, highest freq) - find bright pixels
band0 = arr[0:55, :]
# Per-column bright count in band 0
col_bright = np.sum(band0 > 100, axis=0)
print(f'Band 0 column bright counts: max={col_bright.max()}, threshold 5:')
bright_cols = np.where(col_bright > 5)[0]
print(f'  count={len(bright_cols)}')
print(f'  columns: {bright_cols[:100]}')
if len(bright_cols) > 100:
    print(f'  columns (100-200): {bright_cols[100:200]}')
if len(bright_cols) > 200:
    print(f'  columns (200-300): {bright_cols[200:300]}')
print(f'  total span: {bright_cols.min() if len(bright_cols) else "n/a"} to {bright_cols.max() if len(bright_cols) else "n/a"}')

# Look at first 200 columns and last 200 columns specifically
print('\nFirst 200 columns, band 0 bright count per col:')
for c in range(0, 200, 10):
    print(f'  col {c}-{c+10}: {col_bright[c:c+10]}')

# Also look at vertical pattern in band 0 of bright columns - to see letter shapes
if len(bright_cols) > 0:
    print('\nVertical pattern in band 0, columns 0-100:')
    sub = arr[0:55, 0:100]
    # Print as ASCII art
    for r in range(0, 55, 2):
        line = ''
        for c in range(0, 100, 2):
            line += '#' if sub[r, c] > 100 else '.'
        print(f'  r{r:3d}: {line}')
