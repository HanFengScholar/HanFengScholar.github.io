#!/usr/bin/env python3
"""Analyze spectrogram PNG to find regions with unusual high-frequency content."""
import numpy as np
from PIL import Image

img_path = '/tmp/song_tall.png'
img = Image.open(img_path).convert('L')  # grayscale
arr = np.array(img)
print(f'Image shape: {arr.shape}')
h, w = arr.shape

print('\nBrightness by frequency band (top=high freq, bottom=low freq):')
band_count = 20
band_h = h // band_count
for i in range(band_count):
    band = arr[i*band_h:(i+1)*band_h, :]
    bright = np.mean(band > 128)
    mean = np.mean(band)
    print(f'Band {i:2d} (freq idx {i*band_h:4d}-{(i+1)*band_h:4d}): mean={mean:6.2f} bright_frac={bright:.3f}')

top_half = arr[:h//2, :]
col_brightness = np.mean(top_half > 150, axis=0)
print(f'\nColumn bright-fraction stats (top half):')
print(f'min={col_brightness.min():.3f} max={col_brightness.max():.3f} mean={col_brightness.mean():.3f}')

threshold = col_brightness.mean() + 3 * col_brightness.std()
bright_cols = np.where(col_brightness > threshold)[0]
print(f'Columns with bright high-freq content (>{threshold:.3f}): {len(bright_cols)}')
if len(bright_cols) > 0:
    print(f'  first 50: {bright_cols[:50]}')
    print(f'  last 50: {bright_cols[-50:]}')
