#!/usr/bin/env python3
"""Render band 0 (top of spectrogram = highest freq) as ASCII art."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape
print(f'Image: {w} wide x {h} tall')

# Extract top band (rows 0-55, the very high frequency region)
band0 = arr[0:55, :]
# Find rows that have any bright pixels
row_bright_count = np.sum(band0 > 100, axis=1)
print('\nRow bright counts in band 0 (rows 0-54):')
for r in range(55):
    print(f'  row {r:2d}: {row_bright_count[r]}')

# Identify rows with significant content
sig_rows = np.where(row_bright_count > 50)[0]
print(f'\nSignificant rows (>50 bright pixels): {sig_rows}')
