#!/usr/bin/env python3
"""Verify Morse code decoding by running on each row of the band separately."""
import numpy as np
from PIL import Image

img = Image.open('/tmp/song_tall.png').convert('L')
arr = np.array(img)
h, w = arr.shape
chan_h = h // 2
top_chan = arr[:chan_h, :]

MORSE_TABLE = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
    '--..': 'Z',
    '-----': '0', '.----': '1', '..---': '2', '...--': '3',
    '....-': '4', '.....': '5', '-....': '6', '--...': '7',
    '---..': '8', '----.': '9',
}

def decode_row(row_data, threshold=100, min_width=4, max_width=15, large_gap=20):
    """Decode a single row's bright pattern as Morse code."""
    col_bright = row_data > threshold
    # Find segments
    segs = []
    in_seg = False
    seg_start = 0
    for c in range(len(col_bright)):
        if col_bright[c] and not in_seg:
            in_seg = True
            seg_start = c
        elif not col_bright[c] and in_seg:
            in_seg = False
            segs.append((seg_start, c, c - seg_start))
    if in_seg:
        segs.append((seg_start, len(col_bright), len(col_bright) - seg_start))

    real_segs = [(s, e, w_) for s, e, w_ in segs if min_width <= w_ <= max_width]

    # Group into characters
    chars = []
    current_char = []
    for s, e, w_ in real_segs:
        if current_char:
            gap = s - current_char[-1][1]
            if gap > large_gap:
                chars.append(current_char)
                current_char = []
        current_char.append((s, e, w_))
    if current_char:
        chars.append(current_char)

    decoded = []
    for char_segs in chars:
        morse = ''
        for s, e, w_ in char_segs:
            morse += '.' if w_ < 8 else '-'
        letter = MORSE_TABLE.get(morse, f'?({morse})')
        decoded.append(letter)
    return decoded, chars

# Decode each row separately
for row in [518, 519, 520]:
    decoded, chars = decode_row(top_chan[row])
    # Filter out noise (single-segment chars with width 3)
    filtered = []
    for ci, char_segs in enumerate(chars):
        # noise = single seg with width <= 3
        if len(char_segs) == 1 and char_segs[0][2] <= 3:
            continue
        filtered.append(decoded[ci])
    text = ''.join(filtered)
    print(f'Row {row}: {text}')
    print(f'  raw decoded: {"".join(decoded)}')

# Also try combining all 3 rows (mark col as bright if any row is bright)
combined = np.any(top_chan[518:521, :] > 100, axis=0)
# Decode combined
combined_2d = combined.reshape(1, -1).astype(np.uint8) * 255
decoded, chars = decode_row(combined_2d[0])
filtered = []
for ci, char_segs in enumerate(chars):
    if len(char_segs) == 1 and char_segs[0][2] <= 3:
        continue
    filtered.append(decoded[ci])
text = ''.join(filtered)
print(f'\nCombined (any of 518-520): {text}')

# Also print the 32-char hex
hex_str = text
print(f'\nLength: {len(hex_str)}')
print(f'Hex string: {hex_str}')
print(f'Lowercase: {hex_str.lower()}')
print(f'Uppercase: {hex_str.upper()}')
# Looks like MD5 - check format
import re
if re.match(r'^[0-9A-Fa-f]{32}$', hex_str):
    print('Looks like an MD5 hash (32 hex chars)')

print(f'\nFlag (uppercase): flag{{{hex_str.upper()}}}')
print(f'Flag (lowercase): flag{{{hex_str.lower()}}}')
print(f'Flag (as-is):     flag{{{hex_str}}}')
