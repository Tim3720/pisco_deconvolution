from collections.abc import Callable
import os
from dataclasses import dataclass


@dataclass
class Settings:
    datapath: str



def _parse_config_file(path: str):
    config = {}
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                key, value = line.split("=")
                key = key.strip()
                value = value.strip()
                config[key] = value
            except:
                print("Warning: invalid config line:", line)
                continue

    return config


def get_value(config: dict, key: str, value_parser: Callable, default_value=None):
    if key in config:
        return value_parser(config[key])

    if not default_value is None:
        return default_value

    raise ValueError(f"Missing key '{key}' in config file.")



def parse_config_file(config_file_path: str) -> Settings:
    # check if config file exists:
    if os.path.exists(config_file_path) == False:
        raise FileNotFoundError(f"Config file '{config_file_path}' not found.")

    config = _parse_config_file(config_file_path)


    datapath = get_value(config, "targetPath", str)

    return Settings(datapath)
