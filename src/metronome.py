# A simple metronome / beat generator that does not support time signature and accent
import numpy as np
import sounddevice as sd

class Metronome:
    def __init__(self, bpm=120, sampling_rate = 48_000, click = None):
        self.bpm = bpm
        self.sampling_rate = sampling_rate
        self.interval_samples = int(sampling_rate*60/bpm)
        if click and isinstance(click, np.ndarray): #TODO: validate 1D array?
            self.click = click
        else:
            # default
            duration = 0.4
            amplitude = 0.8
            freq = 440.0
            sample_indices = np.arange(sampling_rate*duration)
            t = sample_indices / sampling_rate
            envelope = np.exp(-60 * t)
            self.click = amplitude * envelope * np.sin(2*np.pi*freq*t)
        # For buffering and scheduling
        self.curr_sample_pos = 0
        self.curr_click_pos = len(self.click) # previous click has been copied all into buffer/handled

    def callback(self, outdata: np.ndarray, frames: int, time, status):
        # init outdata array otw undefine behaviour
        out = outdata[:,0]
        out.fill(0.0)
        # buffer boundaries in samples
        b_start, b_end = self.curr_sample_pos, self.curr_sample_pos + frames

        if (self.curr_click_pos < len(self.click)):
            # decide until which index/sample of the click to copy in
            # either all or part of the click will be copy in
            samples_to_copy = min(frames, len(self.click) - self.curr_click_pos)
            out[:samples_to_copy] = self.click[self.curr_click_pos:self.curr_click_pos+samples_to_copy]
            self.curr_click_pos += samples_to_copy

        # Next onset happen at a sample index which is multiples of interval(in samples) between 2 consistent beats
        # This mean, we can find ceiling of current sample index / interval as basically just add 1 to current multiple
        # We use integer division trick to calculate ceiling.
        next_onset_sample_idx = int((b_start + self.interval_samples - 1)//self.interval_samples) * self.interval_samples
        while next_onset_sample_idx < b_end:
            # Find offset from buffer start to copy the click in, and also find how much samples to copy in
            # we take either the remaining buffer (if click is longer than buffer) or copy the whole click (if click is smaller than remaining buffer space)
            offset_onset_start = next_onset_sample_idx - b_start
            samples_to_copy = min(frames - offset_onset_start, len(self.click))
            out[offset_onset_start:offset_onset_start+samples_to_copy] = self.click[:samples_to_copy]
            #TODO: Can we guarantee that if samples_to_copy is not whole of click, the next_onset_sample_idx won't happen in 
            # this buffer iteration also (i.e no overlap)
            self.curr_click_pos = samples_to_copy # copied how much already
            # update to next planned onset, if it is still within current buffer, loop will handle it
            next_onset_sample_idx += self.interval_samples

        # move the sample tracker forward
        self.curr_sample_pos += frames


if __name__ == "__main__":
    bpm = 250
    fs = 48_000
    metronome = Metronome(bpm=250, sampling_rate=fs)
    with sd.OutputStream(channels=1, samplerate=fs,
                     dtype='float32', callback=metronome.callback):
        input("Playing... press Enter to stop\n")