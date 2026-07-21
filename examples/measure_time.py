import time
import numpy as np

BPM = 120
N = 100
interval = 60/BPM

timestamps = []
for idx in range (N):
    timestamps.append(time.perf_counter())
    time.sleep(interval)

gaps = np.diff(timestamps) * 1000
target = interval * 1000

print(f"target interval : {target:.3f} ms")
print(f"mean interval   : {gaps.mean():.3f} ms   (drift per beat: {gaps.mean()-target:+.3f} ms)")
print(f"jitter (std)    : {gaps.std():.3f} ms")
print(f"worst beat      : {gaps.max():.3f} ms   ({gaps.max()-target:+.3f} ms late)")
