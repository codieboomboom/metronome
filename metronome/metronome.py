# A simple metronome / beat generator that does not support time signature and accent
import numpy as np
import sounddevice as sd
from enum import IntEnum

class Accent(IntEnum):
    REST = 0
    WEAK = 1
    SUB_STRONG = 2
    STRONG = 3

TIME_SIGNATURE_TO_BEATS = {
    (4, 4): [Accent.STRONG, Accent.WEAK, Accent.WEAK, Accent.WEAK],
    (3, 4): [Accent.STRONG, Accent.WEAK, Accent.WEAK],
    (6, 8): [Accent.STRONG, Accent.WEAK, Accent.WEAK, Accent.SUB_STRONG, Accent.WEAK, Accent.WEAK ]
}

class Metronome:
    def __init__(self, bpm=120, sampling_rate = 48_000, clicks: dict = None, time_signature: tuple[int, int] = (4,4)):
        self.bpm = bpm
        self.sampling_rate = sampling_rate
        self.interval_samples = int(sampling_rate*60/bpm)

        # Initialize different clicks for different accents
        if clicks:
            self.clicks = clicks
        else:
            self.clicks = self._default_clicks()
        self._assert_clicks(self.interval_samples)

        # Determine the accents pattern based on time_signature
        if time_signature and time_signature in TIME_SIGNATURE_TO_BEATS:
            self.measure = TIME_SIGNATURE_TO_BEATS[time_signature]
        else:
            raise ValueError("Invalid time signature!")

        # absolute CLK to keep track of sample, source of truth...
        self.sample_clk = 0
        # Keep track of which sound (accent) that is in between the buffer
        self.active_sound = None
        self.active_sound_pos = 0

        # Stream
        self._stream = sd.OutputStream(channels=1, samplerate=sampling_rate,
                     dtype='float32', callback=self.callback)

    def callback(self, outdata: np.ndarray, frames: int, time, status):
        # init outdata array otw undefine behaviour
        out = outdata[:,0]
        out.fill(0.0)
        # buffer boundaries in samples
        b_start, b_end = self.sample_clk, self.sample_clk + frames

        if (self.active_sound is not None and self.active_sound_pos < len(self.active_sound)):
            # decide until which index/sample of the click to copy in
            # either all or part of the click will be copy in
            samples_to_copy = min(frames, len(self.active_sound) - self.active_sound_pos)
            out[:samples_to_copy] = self.active_sound[self.active_sound_pos:self.active_sound_pos+samples_to_copy]
            self.active_sound_pos += samples_to_copy

        # Next onset happen at a sample index which is multiples of interval(in samples) between 2 consistent beats
        # This mean, we can find ceiling of current sample index / interval as basically just add 1 to current multiple
        # We use integer division trick to calculate ceiling.
        # ASSUMPTION 1: beat are generated constant interval from each other. I.e. there is no swing, no triplets, etc, just beats
        # ASSUMPTION 2: approximation of interval samples to nearest int
        next_onset_sample_idx = int((b_start + self.interval_samples - 1)//self.interval_samples) * self.interval_samples
        beat_accent_idx_in_measure = (next_onset_sample_idx // self.interval_samples) % len(self.measure) # which beat in measure
        sound = self.clicks.get(self.measure[beat_accent_idx_in_measure]) # get a sine wave corresponding to the particular accent of next onset
        while next_onset_sample_idx < b_end:
            # Find offset from buffer start to copy the click in, and also find how much samples to copy in
            # we take either the remaining buffer (if click is longer than buffer) or copy the whole click (if click is smaller than remaining buffer space)
            offset_onset_start = next_onset_sample_idx - b_start
            samples_to_copy = min(frames - offset_onset_start, len(sound))
            out[offset_onset_start:offset_onset_start+samples_to_copy] = sound[:samples_to_copy]
            #TODO: Can we guarantee that if samples_to_copy is not whole of click, the next_onset_sample_idx won't happen in 
            # this buffer iteration also (i.e no overlap)
            self.active_sound = sound
            self.active_sound_pos = samples_to_copy
            # update to next planned onset, if it is still within current buffer, loop will handle it
            next_onset_sample_idx += self.interval_samples

        # move the sample tracker forward
        self.sample_clk += frames

    def _default_clicks(self):
        return {
            Accent.STRONG : cook_click(2000.0, 1, 0.05, 60, 48000),
            Accent.SUB_STRONG: cook_click(1000.0, 0.9, 0.05, 60, 48000),
            Accent.WEAK: cook_click(440.0, 0.8, 0.05, 60, 48000)
        }

    def _assert_clicks(self, interval_samples):
        # Guarantee the invariant that the clicks always fit inside the interval_samples
        for _, click in self.clicks.items():
            assert len(click) < interval_samples 

    def start(self):
        self._stream.start()

    def stop(self):
        self._stream.stop()

    def close(self):
        self._stream.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
        self.close()


def cook_click(freq = 440.0, amplitude = 0.8, duration_s = 0.05, decay_rate = 60, sampling_freq = 48_000):
    t = np.arange(duration_s * sampling_freq) / sampling_freq
    envelope = np.exp(-decay_rate * t)
    return amplitude * envelope * np.sin(2*np.pi*freq*t)

if __name__ == "__main__":
    #TODO: how can I measure/guarantee that my metronome is indeed more exact than using time?
    bpm = 100
    fs = 48_000
    metronome = Metronome(bpm=bpm, sampling_rate=fs, time_signature=(3,4))
    with metronome as m:
        input("Playing... press Enter to stop\n")