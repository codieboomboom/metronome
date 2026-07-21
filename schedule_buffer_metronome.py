import numpy as np
import sounddevice as sd

SAMPLING_RATE = 48_000
BPM = 100
CLICK_INTERVAL_IN_SAMPLES = int(round((60 * SAMPLING_RATE)/BPM))

def cook_click(amplitude = 0.8, freq = 440.0, duration = 0.5, sampling_freq = 48_000):
    num_samples = duration * sampling_freq
    sample_indices = np.arange(num_samples)
    t = sample_indices / sampling_freq # what is time each sample was taken (secs)
    envelope = np.exp(-60 * t) # decay
    return amplitude * envelope * np.sin(2 * np.pi * freq * t)

metronome_click = cook_click(sampling_freq=SAMPLING_RATE)
curr_sample_pos = 0 # track number of samples we have feed to the audio card
# the x-axis of click is in time, but number of samples still stay same
# this variable is to track where into the click position have we copied
# into buffer. There are case where buffer only partially copied the click
# which mean we have to copy the rest into another round of buffer
curr_click_pos = len(metronome_click) 

def callback(outdata: np.ndarray, frames: int, time, status):
    # status log
    if status:
        print(status, flush=True)

    global curr_sample_pos, curr_click_pos
    # Reset/Init the out buffer to all zero, otw undefined behaviour at runtime
    out = outdata[:,0]
    out.fill(0.0)
    # Buffer boundaries / which sample start/stop
    buffer_start = curr_sample_pos
    buffer_end = curr_sample_pos + frames

    # If there is a click midway, not yet fully copy in previous buffer, we need to handle it here
    if curr_click_pos < len(metronome_click):
        # determine how much more to copy in: either full buffer if click >> buffer or the remaining of click should buffer >> click
        n = min(frames, len(metronome_click) - curr_click_pos)
        # copy n samples into the buffer from the start
        out[:n] = metronome_click[curr_click_pos: curr_click_pos+n]
        # done copying either all, not all of buffer, so we should update the pos in the click
        curr_click_pos += n

    # TODO: assumed no overlap of click
    # Next onset is at sample number which is "next multiples of interval"
    next_onset_at_sample = int((curr_sample_pos + CLICK_INTERVAL_IN_SAMPLES - 1)//CLICK_INTERVAL_IN_SAMPLES) * CLICK_INTERVAL_IN_SAMPLES
    while next_onset_at_sample < buffer_end:
        # the next onset is within this round of buffer still
        # it would be silence until the onset of click where we have to copy the click waveform into our buffer
        click_start_at_buffer_index = next_onset_at_sample - buffer_start
        n = min(frames - click_start_at_buffer_index, len(metronome_click))
        out[click_start_at_buffer_index:click_start_at_buffer_index + n] = metronome_click[:n] # copy until n, either all or not all of the click
        curr_click_pos = n # how much of click have i written in? if equals length then we have copy all this click
        # update to next onset, might still be within this round buffer if buffer is large and high BPM
        next_onset_at_sample += CLICK_INTERVAL_IN_SAMPLES

    # Done with this buffer, so update the tracker/pos of sample
    curr_sample_pos = buffer_end

with sd.OutputStream(channels=1, samplerate=SAMPLING_RATE,
                     dtype='float32', callback=callback):
    input("Playing... press Enter to stop\n")