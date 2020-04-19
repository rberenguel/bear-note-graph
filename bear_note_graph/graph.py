import logging
from hashlib import sha512
from itertools import cycle

logger = logging.getLogger("bear_note_graph.graph")


def get_color(color, configuration, palettes):
    """Find the colour in the palettes or configuration. If it is not a
palette-enabled colour, just pass through"""
    if "." not in color:
        return color
    palette, color_name = color.split(".")
    if palette in ["note", "link", "graph", "tag"]:
        raise Exception(
            f"Palette name can't be one of the top level configuration names (it is {palette})"
        )
    if palette in configuration.keys():
        palette_dict = configuration[palette]
    elif palette in palettes.keys():
        palette_dict = palettes[palette]
    else:
        raise Exception(f"Palette {palette} is not available")
    if color_name not in palette_dict.keys():
        raise Exception(f"Color {color_name} is not available in palette {palette}")
    return palette_dict[color_name]


class NodeFormat:
    kind: str

    def __init__(self, configuration, palettes):
        self.section = configuration[self.kind]
        self.shape = self.section["shape"]
        self.style = self.section["style"]
        self.free_form = self.section["free_form"]
        fill_color = self.section["fill_color"]
        strike_color = self.section["strike_color"]
        self.fill_color = get_color(fill_color, configuration, palettes)
        self.strike_color = get_color(strike_color, configuration, palettes)

    def __repr__(self):
        shape = self.shape
        style = self.style
        strike_color = self.strike_color
        fill_color = self.fill_color
        free_form = self.free_form
        free_form = ", " + free_form if free_form != "" else free_form
        return f'shape={shape}, style="{style}", color="{strike_color}", fillcolor="{fill_color}" {free_form}'


class TagFormat(NodeFormat):
    kind = "tag"


class NoteFormat(NodeFormat):
    kind = "note"


class LinkFormat:
    kind: str

    def __init__(self, configuration, palettes):
        self.section = configuration[self.kind]
        self.free_form = self.section["free_form"]
        self.arrow_head = self.section["arrowhead"]
        strike_color = self.section["strike_color"]
        self.strike_color = get_color(strike_color, configuration, palettes)

    def __repr__(self):
        color = self.strike_color
        arrow_head = self.arrow_head
        free_form = self.free_form
        free_form = ", " + free_form if free_form != "" else free_form
        return f'color="{color}", arrowhead={arrow_head} {free_form}'


class TagLinkFormat(LinkFormat):
    kind = "tag_link"


class NoteLinkFormat(LinkFormat):
    kind = "note_link"


class GraphFormat:
    def __init__(self, configuration, palettes):
        self.section = configuration["graph"]
        self.anonymise = self.section["anonymise"]
        self.exclude_titles = self.section["exclude_titles"].split(",")
        self.exclude_tags = self.section["exclude_tags"].split(",")
        self.prune = self.section["prune"]
        self.tmp = self.section["tmp"]
        self.destination = self.section["destination"]
        self.show_tag_edges = self.section["show_tag_edges"]
        self.show_note_edges = self.section["show_note_edges"]
        self.run_graphviz = self.section["run_graphviz"]
        self.output_format = self.section["output_format"]
        self.include_only_tags = self.section["include_only_tags"].split(",")
        self.overlap = self.section["overlap"]
        self.max_label_length = self.section["max_label_length"]
        self.sep = self.section["sep"]
        self.splines = self.section["splines"]
        self.free_form = self.section["free_form"]
        bg_color = self.section["bgcolor"]
        self.background_color = get_color(bg_color, configuration, palettes)

        self.tag_format = TagFormat(configuration, palettes)
        self.note_format = NoteFormat(configuration, palettes)
        self.tag_link_format = TagLinkFormat(configuration, palettes)
        self.note_link_format = NoteLinkFormat(configuration, palettes)

    @staticmethod
    def _hashed(item: str) -> str:
        hashed = sha512(item.encode("utf-8")).hexdigest()
        item_cycle = cycle(hashed)
        return "".join(
            [
                next(item_cycle) if letter not in (" ", "#", "/") else letter
                for letter in item
            ]
        )

    def label(self, label):
        max_length = self.max_label_length
        if len(label) > max_length:
            shortened = label[0 : self.max_label_length] + "…"
        else:
            shortened = label
        if self.anonymise:
            return self._hashed(shortened)
        return shortened.replace('"', '\\"')

    def __repr__(self):
        overlap = self.overlap
        sep = self.sep
        splines = self.splines
        bg_color = self.background_color
        free_form = self.free_form
        free_form = ", " + free_form if free_form != "" else free_form
        return f'graph [overlap={overlap}, sep="{sep}", splines={splines}, bgcolor="{bg_color}" {free_form}]'
