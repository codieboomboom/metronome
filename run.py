from metronome import Metronome, load_config

if __name__ == "__main__":
    #TODO: how can I measure/guarantee that my metronome is indeed more exact than using time?
    cfg = load_config()
    metronome = Metronome(cfg)
    with metronome as m:
        input("Playing... press Enter to stop\n")