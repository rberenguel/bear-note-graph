import logging
from pathlib import Path

import yaml

logger = logging.getLogger("bear_note_graph.settings")

RESOURCES = Path(__file__).parent.parent.absolute() / Path("resources")


def default_palettes():
    try:
        with open(RESOURCES / Path("palettes.yaml"), "r") as data:
            return yaml.safe_load(data)
    except Exception as exc:
        raise Exception(f"Could not load the YAML file: {exc}")


PALETTES = default_palettes()


def default_config():
    try:
        with open(RESOURCES / Path("configuration.yaml"), "r") as data:
            return yaml.safe_load(data)
    except Exception as exc:
        raise Exception(f"Could not load the YAML file: {exc}")


DEFAULT_CONFIGURATION = default_config()


def dump_default_config():
    try:
        with open(RESOURCES / Path("configuration.yaml"), "r") as data:
            print(data.read())
    except Exception as exc:
        raise Exception(f"Could not load the YAML file: {exc}")


def dump_default_palette():
    try:
        with open(RESOURCES / Path("palettes.yaml"), "r") as data:
            print(data.read())
    except Exception as exc:
        raise Exception(f"Could not load the YAML file: {exc}")


def merge_user_config_with_default(user_config_path):
    with open(user_config_path, "r") as data:
        user_config = yaml.safe_load(data)
    for key in user_config.keys():
        DEFAULT_CONFIGURATION[key].update(user_config[key])
    logger.debug(DEFAULT_CONFIGURATION)
