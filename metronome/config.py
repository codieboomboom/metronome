from dataclasses import dataclass

DEFAULT_CONFIG = {
    "bpm": 120,
    "sampling_rate": 48_000,
    "time_signature": (4,4),
    "clicks": {
        "strong": {
            "amplitude": 1,
            "frequency": 1500,
            "duration": 0.05,
            "decay": 60
        },
        "sub_strong": {
            "amplitude": 0.8,
            "frequency": 1000,
            "duration": 0.05,
            "decay": 60
        },
        "weak": {
            "amplitude": 0.5,
            "frequency": 440,
            "duration": 0.05,
            "decay": 60
        },
    }
}

class ConfigError(Exception):
    """Raise for any problems during configuration loading"""

@dataclass(frozen=True)
class Config:
    bpm: int
    sampling_rate: int
    time_signature: tuple[int, int]
    clicks: dict[str, dict]

    def __post_init__(self)->None:
        if not isinstance(self.bpm, int) or not (20 <= self.bpm <= 300):
            raise ConfigError(f"BPM must be an integer and between 20-300 BPM. Recieved bpm: {self.bpm}")
        allowed_fs = [44_100, 48_000]
        if not isinstance(self.sampling_rate, int) or self.sampling_rate not in allowed_fs:
            raise ConfigError(f"Sampling Rate must be an int and falls inside these values: {allowed_fs}. Value received: {self.sampling_rate}")
        #TODO: validate time_signature to be of 2 int
        if not isinstance(self.time_signature, tuple):
            raise ConfigError(f"Time signature must be in the form of a tuple with integers. Received non-tuple {self.time_signature}")
        if not isinstance(self.time_signature[0], int) or not isinstance(self.time_signature[1], int):
            raise ConfigError(f"Time signature must be a tuple of integer, received a tuple of ({type(self.time_signature[0])}, {type(self.time_signature[1])})")
        #TODO: validate the clicks frequency to be within Nyquist theorem

def load_config() -> Config:
    final_config = DEFAULT_CONFIG
    return Config(bpm=final_config["bpm"], sampling_rate=final_config["sampling_rate"], time_signature=final_config["time_signature"], clicks=final_config["clicks"])