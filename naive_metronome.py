import time
import numpy as np
import sounddevice as sd

SAMPLING_FREQUENCY = 44_100

def cook_sound(frequency: float = 440.0, duration: float = 0.05):
    num_samples = int(SAMPLING_FREQUENCY * duration)
    t = np.arange(num_samples)/SAMPLING_FREQUENCY # convert to store time that the samples are taken
    envelope = np.exp(-t*1000)
    amplitude = 0.8
    sound = (amplitude * envelope * np.sin(2*np.pi*frequency*t)).astype(np.float32)
    return sound

SOUND = cook_sound()
BPM = 150

while True:
    sd.play(SOUND, SAMPLING_FREQUENCY)
    time.sleep(60/BPM)

