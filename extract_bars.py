#!/usr/bin/env python3
"""Extract the bar pattern from rows 518-520 of top channel."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape
chan_h = h // 2
top_chan = arr[:chan_h, :]

# Look at rows 518-520 (the bright low-freq content)
# But also examine surrounding rows for context

# Print full width of rows 515-525 as ASCII art (no downsampling)
print(f'Image width: {w}')
print(f'\n=== Full pattern rows 515-525 ===')
# Print as one long line per row, but we'll need to print in chunks
for r in range(515, 526):
    bc = np.sum(top_chan[r] > 100)
    if bc > 0:
        # Build the line
        line = ''.join('#' if top_chan[r, c] > 100 else '.' for c in range(w))
        print(f'r{r} ({bc:5d} bright):')
        # Print in chunks of 200
        for cs in range(0, w, 200):
            ce = min(cs + 200, w)
            chunk = line[cs:ce]
            if '#' in chunk:
                print(f'  cs={cs:5d}: {chunk}')

# Extract segments of bright/dark for row 518 (the most bright row)
print(f'\n=== Segment analysis for row 518 ===')
row = top_chan[518]
on = row > 100
# Find segments
segs = []
in_seg = False
seg_start = 0
for c in range(w):
    if on[c] and not in_seg:
        in_seg = True
        seg_start = c
    elif not on[c] and in_seg:
        in_seg = False
        segs.append((seg_start, c, c - seg_start))
if in_seg:
    segs.append((seg_start, w, w - seg_start))

print(f'Number of segments: {len(segs)}')
print('First 50 segments (start, end, width):')
for i, (s, e, w_) in enumerate(segs[:50]):
    print(f'  seg {i:2d}: start={s:5d} end={e:5d} width={w_:3d}')

# Also extract gap widths
print('\nFirst 50 gaps (between segments):')
for i in range(min(50, len(segs)-1)):
    s1, e1, _ = segs[i]
    s2, e2, _ = segs[i+1]
    gap = s2 - e1
    print(f'  gap {i:2d}: from {e1:5d} to {s2:5d}, width={gap:3d}')

# Print width distribution
widths = np.array([w_ for _, _, w_ in segs])
gaps = np.array([segs[i+1][0] - segs[i][1] for i in range(len(segs)-1)])
print(f'\nWidth distribution: min={widths.min()} max={widths.max()} mean={widths.mean():.1f}')
print(f'  unique widths: {sorted(set(widths))}')
print(f'Gap distribution: min={gaps.min()} max={gaps.max()} mean={gaps.mean():.1f}')
print(f'  unique gaps: {sorted(set(gaps))}')
