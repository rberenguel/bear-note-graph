import pytest
import bear_note_graph.parser as parser
from bear_note_graph.graph import GraphFormat
from bear_note_graph.settings import DEFAULT_CONFIGURATION, PALETTES
from bear_note_graph.generate import generate_graph_from_rows, find_note_id, lock_title


def test_lone_bracket():
    """
    Test for issue #2: https://github.com/rberenguel/bear-note-graph/issues/2
    """
    markdown = """ # Note
 [

with a bracket
    """
    parsed, rest = parser.MARKDOWN_PARSER.parse(markdown)
    assert parsed == [
        parser.TextBlock(text=" "),
        parser.HeadingBlock(text="Note"),
        parser.TextBlock(text="\n "),
        parser.FallbackTextBlock(text="["),
        parser.TextBlock(text="\n\nwith a bracket\n    "),
    ]
    assert rest is None


def test_find_note_links(caplog):
    """Test for issue #3: https://github.com/rberenguel/bear-note-graph/issues/3"""
    all_notes = [{"title": "foo", "uuid": "42"}, {"title": "bar", "uuid": "43"}]
    note_id = find_note_id({"src": "44", "dst": "baz"}, all_notes)
    assert (
        "Could not find note titled <<baz>> linked from note bear://x-callback-url/open-note?id=44"
        in caplog.text
    )
    assert note_id == ""


def test_find_locked_note_links(caplog):
    """Test for issue #4+: https://github.com/rberenguel/bear-note-graph/issues/4"""
    all_notes = [
        {"title": "foo", "uuid": "42"},
        {"title": lock_title("bar"), "uuid": "43"},
    ]
    note_id = find_note_id({"src": "44", "dst": "bar"}, all_notes)
    assert note_id == "43"


def test_note_with_no_text(caplog):
    """Test for issue #4: https://github.com/rberenguel/bear-note-graph/issues/4"""
    valid_note = {
        "title": "note title",
        "md_text": "some text and a #tag",
        "uuid": "42",
    }
    locked_note = {"title": "locked note title", "uuid": "43", "encrypted": "1"}

    rows = [valid_note, locked_note]
    gf = GraphFormat(DEFAULT_CONFIGURATION, PALETTES)
    all_tags, all_notes, all_tag_edges, all_note_edges = generate_graph_from_rows(
        gf, rows
    )
    assert len(all_notes) == 2
    assert {"title": lock_title("locked note title"), "uuid": "43"} in all_notes


def test_note_exclusion(caplog):
    """Test for issue #4+: https://github.com/rberenguel/bear-note-graph/issues/4"""
    valid_note = {
        "title": "> note title",
        "md_text": "some text and a #tag",
        "uuid": "42",
    }
    locked_note = {"title": "locked note title", "uuid": "43", "encrypted": "1"}

    rows = [valid_note, locked_note]
    gf = GraphFormat(DEFAULT_CONFIGURATION, PALETTES)
    all_tags, all_notes, all_tag_edges, all_note_edges = generate_graph_from_rows(
        gf, rows
    )
    assert len(all_notes) == 1
    assert {"title": "> note title", "uuid": "42"} not in all_notes


def test_graph_generation(caplog):
    """Test with some problematic notes, useful to test specific errors"""
    valid_note = {
        "title": "note title",
        "md_text": "some text and a #tag",
        "uuid": "42",
    }
    empty_note = {"title": "empty note title", "md_text": "", "uuid": "43"}
    another_valid_note = {"title": "title", "md_text": "[[note title]]", "uuid": "44"}
    no_link = {"title": "title nowhere", "md_text": "[[ ]] goes nowhere", "uuid": "45"}
    rows = [valid_note, empty_note, another_valid_note, no_link]
    gf = GraphFormat(DEFAULT_CONFIGURATION, PALETTES)
    all_tags, all_notes, all_tag_edges, all_note_edges = generate_graph_from_rows(
        gf, rows
    )
    assert "#tag" in all_tags
    assert len(all_notes) == 4  # The empty note is still a note
    assert len(set(map(str, all_notes))) == 4
    assert "Skipping empty note: bear://x-callback-url/open-note?id=43" in caplog.text
    assert {"src": "#tag", "dst": "42"} in all_tag_edges
    assert {"src": "44", "dst": "42"} in all_note_edges
    assert len(all_note_edges) == 1
    assert (
        "Could not find note titled << >> linked from note bear://x-callback-url/open-note?id=45"
        in caplog.text
    )
