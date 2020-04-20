import logging
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .parser import MARKDOWN_PARSER, NoteLinkBlock, ParseError, TagBlock

logger = logging.getLogger("bear_note_graph.generate")


def copy_bear_db(graph_format):
    """Work on a copy of the database"""
    home = os.getenv("HOME", "")
    bear_db = Path(home) / Path(
        "Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite"
    )
    temp_db = Path(graph_format.tmp) / Path("BearExportTemp.sqlite")
    logger.info("Copying Bear database to %s", temp_db)
    shutil.copyfile(bear_db, temp_db)
    return temp_db


def get_db_data(graph_format):
    temp_db = copy_bear_db(graph_format)
    logger.info("Fetching notes from (the copy of the) database")
    with sqlite3.connect(temp_db) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT ZTITLE AS title, ZTEXT AS md_text, ZUNIQUEIDENTIFIER AS uuid FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0'"
        result_set = conn.execute(query).fetchall()
    logger.info(
        "Fetched %s notes from the (copy of) the Bear database", len(result_set)
    )
    return result_set


def bear_note_link(_id):
    return f"bear://x-callback-url/open-note?id={_id}"


def generate_graph(graph_format):
    rows = get_db_data(graph_format)
    all_tags, all_notes, all_tag_edges, all_note_edges = generate_graph_from_rows(
        graph_format, rows
    )
    process(graph_format, all_tags, all_notes, all_tag_edges, all_note_edges)
    logger.info("Graphviz file generated at %s.gv", graph_format.destination)
    run_graphviz(graph_format)


def generate_graph_from_rows(graph_format, rows: List[Dict[Any, Any]]):
    """The main loop to generate the graph. I got lazy after working on the
Markdown parser, so even if this could be significantly cleaner (and tested...)
I didn't want to invest any more time on it"""

    all_tags = []
    all_notes = []
    all_tag_edges = []
    all_note_edges = []

    def filter_tags(tag):
        for exclude in graph_format.exclude_tags:
            if exclude in tag:
                return False
        for include in graph_format.include_only_tags:
            if include in tag:
                return True
        return False

    for row in rows:
        title = row["title"]
        md_text = row["md_text"]
        uuid = row["uuid"]
        if len(md_text) < 3:
            logger.warning("Skipping empty note: %s", bear_note_link(uuid))
        try:
            blocks, _ = MARKDOWN_PARSER.parse(md_text)
        except ParseError as exc:
            logger.warning(
                "There is a problem parsing note <<%s>> %s, the error is\n\t%s",
                title,
                bear_note_link(uuid),
                exc,
            )
            continue
        if any(
            [
                exclude.lower() in title.lower()
                for exclude in graph_format.exclude_titles
            ]
        ):
            continue

        def cleanup_tag(tag):
            if tag[-1] in ["#", ",", "!", "."]:
                return tag[0:-1]
            return tag

        captured_tags = set(
            list(
                map(
                    lambda x: cleanup_tag(x.text),
                    filter(lambda x: isinstance(x, TagBlock), blocks),
                )
            )
        )
        captured_links = set(
            list(
                map(
                    lambda x: x.text,
                    filter(lambda x: isinstance(x, NoteLinkBlock), blocks),
                )
            )
        )

        filtered_tags = list(filter(filter_tags, captured_tags))

        if graph_format.prune:
            if len(filtered_tags) == 0:
                continue
        all_notes += [{"title": title, "id": uuid}]
        for tag in filtered_tags:
            all_tag_edges += [{"src": tag, "dst": uuid}]
        all_tags += filtered_tags
        for note in captured_links:
            all_note_edges += [{"src": uuid, "dst": note}]

    for note_edge in all_note_edges:
        note_id = find_note_id(note_edge, all_notes)
        note_edge["dst"] = note_id

    all_note_edges = list(filter(lambda ne: ne["dst"] != "", all_note_edges))
    unique_tags = set(all_tags)
    logger.info(
        "All notes processed, there are %s tags, %s (valid) notes, %s tag edges among them and %s note edges among them",
        len(unique_tags),
        len(all_notes),
        len(all_tag_edges),
        len(all_note_edges),
    )

    return unique_tags, all_notes, all_tag_edges, all_note_edges


def find_note_id(note_edge: Dict[str, str], all_notes: List[Dict[str, str]]) -> str:
    dest_title = note_edge["dst"]
    source_id = note_edge["src"]
    note = filter(lambda x: x["title"] == dest_title, all_notes)
    try:
        return list(note)[0]["id"]
    except IndexError:
        logger.warning(
            "Could not find note titled <<%s>> linked from note %s",
            dest_title,
            bear_note_link(source_id),
        )
        return ""


def run_graphviz(graph_format):
    if graph_format.run_graphviz != "":
        gv_cmd = graph_format.run_graphviz
        fmt = graph_format.output_format
        destination = graph_format.destination
        source_gv = destination + ".gv"
        output_fmt = destination + f".{fmt}"
        command = f"{gv_cmd} -T{fmt} {source_gv} > {output_fmt}"
        logger.info('Running Graphviz command "%s"', command)
        subprocess.run(command, shell=True, check=True)
        logger.info('Run "open %s" to open the generated file', output_fmt)


def process(graph_format, all_tags, all_notes, all_tag_edges, all_note_edges):
    with open(graph_format.destination + ".gv", "w") as dest:
        dest.write("digraph G_component_0 {\n")
        dest.write(f"\t{graph_format}\n")
        dest.write(f"\t\t# Tags section\n")
        if graph_format.show_tag_edges:
            for tag in all_tags:
                url = (
                    ""
                    if graph_format.anonymise
                    else f"bear://x-callback-url/open-tag?name={tag}"
                )
                label = graph_format.label(tag)
                dest.write(f'\t\t"{label}" [{graph_format.tag_format}, URL="{url}"];\n')
        dest.write(f"\t\t# Notes section\n")
        for note in all_notes:
            title = note["title"]
            _id = note["id"]
            url = f"bear://x-callback-url/open-note?id={_id}"
            label = graph_format.label(title)
            dest.write(
                f'\t\t"{_id}" [label="{label}", {graph_format.note_format}, URL="{url}"];\n'
            )
        dest.write(f"\t\t# Tag edge section\n")
        if graph_format.show_tag_edges:
            for edge in all_tag_edges:
                src = graph_format.label(edge["src"])
                dst = edge["dst"]
                dest.write(
                    f'\t\t"{src}" -> "{dst}" [{graph_format.tag_link_format}];\n'
                )
        dest.write(f"\t\t# Note edge section\n")
        if graph_format.show_note_edges:
            for edge in all_note_edges:
                src = edge["src"]
                dst = edge["dst"]
                dest.write(
                    f'\t\t"{src}" -> "{dst}" [{graph_format.note_link_format}];\n'
                )
        dest.write("}")
