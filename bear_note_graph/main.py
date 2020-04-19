import argparse
import logging
import os
import sys

from colorlog import ColoredFormatter  # type: ignore

from .generate import generate_graph
from .graph import GraphFormat
from .settings import (
    DEFAULT_CONFIGURATION,
    PALETTES,
    dump_default_config,
    dump_default_palette,
    merge_user_config_with_default,
)

logger = logging.getLogger("bear_note_graph")


def configure_logger():
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "yellow",
            "INFO": "cyan",
            "WARNING": "purple",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main(**args):
    configure_logger()
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="bear-note-graph generates a Graphviz graph of your Bear notes")
    parser.add_argument(
        "--config",
        metavar="config",
        type=str,
        help="Configuration file to use. Use --dump-config-file to get a sample",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--dump-config",
        dest="dump_config",
        action="store_true",
        help="Print the default configuration file and exit",
    )
    parser.add_argument(
        "--dump-palette",
        dest="dump_palette",
        action="store_true",
        help="Print the default palette file and exit",
    )

    parser.add_argument(
        "--anonymise",
        dest="anonymise",
        action="store_true",
        help="Mangle the tags and link names preserving 'look'",
    )
    parser.add_argument(
        "--only-tags", dest="only_tags", action="store_true", help="Show only tag links"
    )
    parser.add_argument(
        "--only-notes",
        dest="only_notes",
        action="store_true",
        help="Show only note links",
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Set logging to debug level"
    )
    args = parser.parse_args()

    if args.dump_palette:
        dump_default_palette()
        sys.exit(0)
    if args.dump_config:
        dump_default_config()
        sys.exit(0)

    def check_file(candidate_path: str):
        try:
            with open(candidate_path) as _:
                logger.debug("File found: %s", candidate_path)
                return True
        except IOError:
            logger.debug("File not found: %s (IO failed)", candidate_path)
            return False
        logger.debug("File not found: %s (no exception?)", candidate_path)
        return False

    if args.config is not None:
        config_path = os.path.join(os.getcwd(), args.config)
        if check_file(config_path):
            merge_user_config_with_default(config_path)
        else:
            raise Exception("Configuration file not found")
    config = DEFAULT_CONFIGURATION
    graph_format = GraphFormat(config, PALETTES)
    if args.anonymise:
        graph_format.anonymise = True

    if args.only_tags:
        graph_format.show_note_edges = False

    if args.only_notes:
        graph_format.show_tag_edges = False

    generate_graph(graph_format)
