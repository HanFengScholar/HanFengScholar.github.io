#!/usr/bin/env python3
"""Look at the bright regions of the spectrogram more carefully."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape
print(f'Image: {w} x {h}')

# SoX with 2 channels makes 2 spectrograms stacked. Each is h/2 tall.
# Each channel shows 0-22050 Hz. Top row of each = 22050 Hz, bottom row = 0 Hz.
chan_h = h // 2
print(f'Per channel height: {chan_h}')

# Examine row 29 of TOP channel (high freq end)
top_chan = arr[:chan_h, :]
print(f'\nTop channel shape: {top_chan.shape}')

# Row 29 had 10847 bright pixels - that's almost all. Confirm:
print(f'Row 29 of top channel, bright count: {np.sum(top_chan[29] > 100)} / {w}')

# So row 29 is essentially solid bright - this is a constant carrier tone.
# Now look at rows 16-24 (different freq, with scattered bright pixels).
# Extract rows 16-24 and save as a separate image - that's the data
data_band = top_chan[16:25, :]  # rows 16-24
print(f'\nData band (rows 16-24) shape: {data_band.shape}')
# Per-column brightness in this band
col_bright = np.sum(data_band > 100, axis=0)
print(f'Per-col bright count stats: min={col_bright.min()} max={col_bright.max()} mean={col_bright.mean():.2f}')
print(f'Columns with bright count > 0: {np.sum(col_bright > 0)} / {w}')

# Threshold: col is "on" if bright_count >= 1
on_cols = col_bright > 0
# Find transitions
diff = np.diff(on_cols.astype(int))
on_starts = np.where(diff == 1)[0] + 1
on_ends = np.where(diff == -1)[0] + 1
print(f'\nNumber of "on" segments: {min(len(on_starts), len(on_ends))}')

# Print first 30 segments with start, end, width
n_seg = min(len(on_starts), len(on_ends))
print('First 30 segments (col_start, col_end, width):')
for i in range(min(30, n_seg)):
    s = on_starts[i] if i < len(on_starts) else -1
    e = on_ends[i] if i < len(on_ends) else -1
    if s >= 0 and e >= 0:
        print(f'  seg {i:2d}: start={s:5d} end={e:5d} width={e-s:4d}')

# Save data band as a wider/cleaner image for inspection
data_img = Image.fromarray((data_band > 100).astype(np.uint8) * 255)
data_img.save('/workspace/data_band.png')
print(f'\nSaved /workspace/data_band.png (size: {data_img.size})')

# Save as ASCII art across whole width, in chunks
print(f'\n=== ASCII ART of data band (rows 16-24, scaled to 1 char per 4 cols) ===')
# Each row is 9 pixels (16-24). Print as 9 lines per chunk.
# Downsample cols by 2: print every 2nd col.
for chunk_start in range(0, w, 200):
    chunk_end = min(chunk_start + 200, w)
    print(f'\n--- cols {chunk_start}-{chunk_end} ---')
    for r in range(9):
        line = ''
        for c in range(chunk_start, chunk_end, 2):
            line += '#' if data_band[r, c] > 100 else '.'
        print(f'r{r+16:2d}: {line}')
