#!/usr/bin/env python3
"""Directly analyze high-frequency content of the WAV audio."""
import wave
import numpy as np
import struct

wav_path = '/tmp/ctf2batch2/song/来首歌吧/stego100.wav'
with wave.open(wav_path, 'rb') as w:
    nchannels = w.getnchannels()
    sampwidth = w.getsampwidth()
    framerate = w.getframerate()
    nframes = w.getnframes()
    print(f'Channels: {nchannels}, sample width: {sampwidth}, framerate: {framerate}')
    print(f'Frames: {nframes}, duration: {nframes/framerate:.2f}s')
    raw = w.readframes(nframes)

# Convert to int16 numpy array
samples = np.frombuffer(raw, dtype=np.int16)
# Reshape into stereo (n, 2)
samples = samples.reshape(-1, 2)
print(f'Samples shape: {samples.shape}')

# Take left channel
left = samples[:, 0].astype(np.float64)
right = samples[:, 1].astype(np.float64)

# FFT analysis - look at high frequency content over time
# Use 4096-sample windows (about 0.093s at 44100 Hz)
win_size = 4096
hop = 4096
nyquist = framerate // 2
print(f'\nNyquist freq: {nyquist} Hz')

# Look at one window to see what frequencies have content
# Compute FFT of first window
win = left[:win_size]
fft = np.fft.rfft(win)
power = np.abs(fft)
freqs = np.fft.rfftfreq(win_size, 1.0/framerate)
print(f'\nFFT of first window (win_size={win_size}):')
print(f'  freq bins: {len(freqs)}')
print(f'  highest 30 freq bins (Hz: power):')
for i in range(len(freqs)-30, len(freqs)):
    print(f'    {freqs[i]:8.1f} Hz: {power[i]:10.1f}')

# Now find high-freq bins with significant power
print(f'\nPower > 1000 in any window?')
# Process full audio in chunks
n_windows = (len(left) - win_size) // hop + 1
print(f'Total windows: {n_windows}')

# Track power in highest 50 frequency bins over time
top_bins = 50
power_over_time = np.zeros((n_windows, top_bins))
for i in range(n_windows):
    start = i * hop
    win = left[start:start+win_size]
    if len(win) < win_size:
        break
    fft = np.fft.rfft(win)
    power = np.abs(fft)
    power_over_time[i] = power[-top_bins:]

# Per-bin stats across all windows
print(f'\nTop {top_bins} frequency bins - mean power over time:')
for j in range(top_bins):
    freq = freqs[-(top_bins - j)]
    mean_p = power_over_time[:, j].mean()
    max_p = power_over_time[:, j].max()
    print(f'  bin {j:2d} ({freq:8.1f} Hz): mean={mean_p:10.1f} max={max_p:10.1f}')
