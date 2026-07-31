from dataclasses import dataclass
from pathlib import Path
import tomllib

DEFAULT_CONFIG = {
    "bpm": 120,
    "sampling_rate": 48_000,
    "time_signature": {
        "top": 4,
        "bottom": 4
    },
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

DEFAULT_TOML_PATH = Path(__file__).resolve().parent.joinpath("config.toml")

ACCENTS = ["strong", "sub_strong", "weak"]

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
        if not isinstance(self.time_signature, tuple):
            raise ConfigError(f"Time signature must be in the form of a tuple with integers. Received non-tuple {self.time_signature}")
        if not isinstance(self.time_signature[0], int) or not isinstance(self.time_signature[1], int):
            raise ConfigError(f"Time signature must be a tuple of integer, received a tuple of ({type(self.time_signature[0])}, {type(self.time_signature[1])})")
        # Some validations for clicks:
        if not self.clicks:
            raise ConfigError(f"Clicks specification must be a dictionary! Received {type(self.clicks)}")
        if self.clicks.keys() != set(ACCENTS):
            raise ConfigError(f"You must supply 1 entry of specification for each type of accents in {ACCENTS}. There are only entries for {self.click.keys()} ")
        # TODO: Add a bunch more validation for fields of the dict: abit mafan to type them out here...
        beat_interval = 60 / self.bpm
        for click_accent, click_spec in self.clicks.items():
            if click_spec["duration"] > beat_interval:
                raise ConfigError(f"Click {click_accent} has duration {click_spec['duration']} longer than interval between 2 beats!")
            if click_spec["frequency"] * 2 > self.sampling_rate:
                raise ConfigError(f"Click {click_accent} has frequency {click_spec['frequency']} that may cause aliasing for sampling rate {self.sampling_rate}")


def load_toml(path: Path, *, required: bool) -> dict:
    if not path.is_file():
        if required:
            raise ConfigError(f"Config file {path} not found!")
        return {} 
    
    try:
        with path.open("rb") as f:
            toml_cfg = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid toml in {path}") from e
    
    # TODO: Validate if the read-in config dict have any extra/unknown fields/keys

    return toml_cfg


def load_config() -> Config:
    final_config = DEFAULT_CONFIG
    
    toml_layer = load_toml(DEFAULT_TOML_PATH, required=True)

    time_signature = (final_config["time_signature"]["top"], final_config["time_signature"]["bottom"])
    return Config(bpm=final_config["bpm"], sampling_rate=final_config["sampling_rate"], time_signature=time_signature, clicks=final_config["clicks"])