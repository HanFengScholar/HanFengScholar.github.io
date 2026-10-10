#!/usr/bin/env python3
"""Look at BOTH channels of the spectrogram, save regions as separate images."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape
print(f'Image: {w} x {h}')

# Two channels, each h/2 tall
chan_h = h // 2
top_chan = arr[:chan_h, :]      # channel 1
bot_chan = arr[chan_h:, :]      # channel 2

# For each channel, find rows with significant bright content
for name, chan in [('TOP', top_chan), ('BOT', bot_chan)]:
    print(f'\n=== {name} channel ===')
    # Per-row bright count
    row_bright = np.sum(chan > 100, axis=1)
    print(f'Rows with >100 bright pixels:')
    sig_rows = np.where(row_bright > 100)[0]
    print(f'  count={len(sig_rows)}, rows: {sig_rows[:30]}')
    if len(sig_rows) > 30:
        print(f'    ... and {len(sig_rows) - 30} more')

# For each channel, check if there are SCATTERED bright pixels at high-freq (top rows)
# Top channel: top row 0 = 22050 Hz, row 551 = 0 Hz
# Find regions where there's a clear TEXT pattern (clusters of bright pixels in specific shape)
print('\n=== Looking for text-like patterns ===')
# Text would have specific (x, y) clusters. Try detecting with simple connected components.

# But first: let's save the top-channel top 60 rows as a separate image, scaled
top_60 = top_chan[:60, :]
img_60 = Image.fromarray(top_60)
img_60_big = img_60.resize((w, 600))
img_60_big.save('/workspace/top_chan_top60.png')
print(f'Saved /workspace/top_chan_top60.png')

# Save bottom channel top 60 rows
bot_60 = bot_chan[:60, :]
img_b60 = Image.fromarray(bot_60)
img_b60_big = img_b60.resize((w, 600))
img_b60_big.save('/workspace/bot_chan_top60.png')
print(f'Saved /workspace/bot_chan_top60.png')
