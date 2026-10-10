#!/usr/bin/env python3
"""Examine low-freq bright content (rows 518-520, 543) in top channel."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape
chan_h = h // 2
top_chan = arr[:chan_h, :]

# Look at low freq rows in top channel: 518-520, 543
print('=== Rows 515-550 of top channel (low freq end) ===')
for r in range(515, 552):
    bc = np.sum(top_chan[r] > 100)
    if bc > 0:
        print(f'  row {r}: {bc} bright pixels')

# Check rows 518-520 specifically - extract pattern
print('\n=== Pattern in rows 518-520 across full width ===')
# Print ASCII art of these 3 rows in chunks of 200 cols
for chunk_start in range(0, w, 200):
    chunk_end = min(chunk_start + 200, w)
    print(f'\n--- cols {chunk_start}-{chunk_end} ---')
    for r in [518, 519, 520, 521, 522]:
        line = ''
        for c in range(chunk_start, chunk_end, 1):
            line += '#' if top_chan[r, c] > 100 else '.'
        print(f'r{r}: {line}')

# Same for row 543
print('\n=== Pattern in rows 540-547 ===')
for chunk_start in range(0, w, 200):
    chunk_end = min(chunk_start + 200, w)
    print(f'\n--- cols {chunk_start}-{chunk_end} ---')
    for r in [540, 541, 542, 543, 544, 545]:
        line = ''
        for c in range(chunk_start, chunk_end, 1):
            line += '#' if top_chan[r, c] > 100 else '.'
        print(f'r{r}: {line}')
