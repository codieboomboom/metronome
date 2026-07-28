from metronome import Metronome

if __name__ == "__main__":
    #TODO: how can I measure/guarantee that my metronome is indeed more exact than using time?
    bpm = 85
    fs = 48_000
    metronome = Metronome(bpm=bpm, sampling_rate=fs, time_signature=(4,4))
    with metronome as m:
        input("Playing... press Enter to stop\n")