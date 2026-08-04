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
    
    validate_no_unknown_keys(toml_cfg, DEFAULT_CONFIG, str(path))
    return toml_cfg

def validate_no_unknown_keys(data: dict, ref: dict, src_name: str, prefix: str = "") -> None:
    """Validate that there are no unknown keys inside that data that does not appear/show up in the reference dict.
    Also make sure nested structure matched

    Args:
        data (dict): dictionary that we wish to validates
        ref (dict): reference dictionary containing "allowed"/"whitelisted" keys.
        src_name (str): name of the data source, i.e. from which config file path, from cli, etc => for debugging purpose
        prefix (str, optional): representing the parent node/nested level where the keys we are validating be at. Defaults to "".

    Raises:
        ConfigError: should a key in data does not exist in ref or the key shouldn't be a dict.
    """
    for key, value in data.items():
        curr_path = f"{prefix}{key}" # from root level
        if key not in ref.keys():
            raise ConfigError(f"The key {curr_path!r} in {src_name} does not exist in reference config")
        if isinstance(value, dict):
            # validates if such nested structure / same key is a dict in ref?
            if not isinstance(ref.get(key, None), dict):
                raise ConfigError(f"They key {curr_path!r} in {src_name} shouldn't be a dictionary according to reference config!")
            # curr key's value is a dictionary, thus we need to check the equivalent nested structure
            # in reference
            validate_no_unknown_keys(data[key], ref[key], src_name, prefix=f"{curr_path}.")

def merge_layer_into_cfg(target: dict, layer: dict, active_layer_tracker: dict, src_name: str, prefix: str = "") -> None:
    """Deeply merge nested structure of layer into target and also updates if changes has happen due this layer/src_name. Recursive call
    to make deep merge happens

    Args:
        target (dict): the destination dictionary to merge into
        layer (dict): the source destination to copy into target
        active_layer_tracker (dict): a dictionary of key being the config key being changed/replaced and value is the name of layer/ active layer
        that cause that changed. I.e name of src where the config key's value is from
        src_name (str): representative name of the current layer being merged into target
        prefix (str, optional): Use to build key path, dotted-separated to represent a path from root to the current key. Defaults to "".
    """
    for cfg_key, cfg_value in layer.items():
        curr_path = f"{prefix}{cfg_key}" # from root level to this cfg_key
        if isinstance(cfg_value, dict) and isinstance(target.get(cfg_key, None), dict):
            # Proceed to merge on the next layer recursively
            merge_layer_into_cfg(target[cfg_key], cfg_value, active_layer_tracker, src_name, prefix=f"{curr_path}.")
        else:
            # just replace value and keep track of replacement/changes overwritten by active layer
            target[cfg_key] = cfg_value
            active_layer_tracker[curr_path] = src_name


def load_config() -> Config:
    final_config = {}
    cfg_active_layer = {}

    merge_layer_into_cfg(final_config, DEFAULT_CONFIG, cfg_active_layer, "built-in defaults")
    
    toml_layer = load_toml(DEFAULT_TOML_PATH, required=True)
    merge_layer_into_cfg(final_config, toml_layer, cfg_active_layer, DEFAULT_TOML_PATH)

    time_signature = (final_config["time_signature"]["top"], final_config["time_signature"]["bottom"])
    return Config(bpm=final_config["bpm"], sampling_rate=final_config["sampling_rate"], time_signature=time_signature, clicks=final_config["clicks"])