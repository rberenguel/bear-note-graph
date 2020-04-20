# Bear-note-graph 🐻🐍

[![PyPI version](https://badge.fury.io/py/bear-note-graph.svg)](https://badge.fury.io/py/bear-note-graph)

_Note_: Still WIP, not as thoroughly tested as I would have liked

This is a simple CLI to generate a [Graphviz](https://www.graphviz.org/doc/info/attrs.html)-powered graph of your notes in [Bear](https://bear.app/).

## Example

This is an example in PNG format, with the flag `--anonymise`, which you can use in case you want to show your own graph but avoid showing the titles of your notes `¯\﹍(ツ)﹍/¯`

<a href="https://github.com/rberenguel/bear-note-graph/raw/master/resources/bear_graph.png" target="_blank"><img src="https://raw.githubusercontent.com/rberenguel/bear-note-graph/master/resources/bear_graph.png" alt="Example graph" width="800"></a>

If you use the default output (PDF) you will get clickable links to notes and tags (BUT ONLY ON iOS, Preview for Mac does not open app links). I recommend you copy your graph to iCloud if you want clicking. You can see an example of the PDF <a href="resources/bear_graph.pdf" target="_blank">here</a> (although it is anonymised as well).

## Installation

You need an environment with at least Python 3.7, and

```bash
pip install bear-note-graph
```

## Installing graphviz

To generate the graph, the `sfdp` command from Graphviz needs to be available, and for some settings (like, if you want to change overlap modes) you may need to reinstall to add `gts`. For this, you should have [homebrew](https://brew.sh) available.

```bash
brew uninstall graphviz --ignore-dependencies
brew install gts
brew install graphviz
```

## Usage

```
usage: bear-note-graph [-h] [--config [config]] [--dump-config]
                       [--dump-palette] [--anonymise] [--only-tags]
                       [--only-notes] [--debug]

bear-note-graph generates a Graphviz graph of your Bear notes

optional arguments:
  -h, --help         show this help message and exit
  --config [config]  Configuration file to use. Use --dump-config-file to get
                     a sample
  --dump-config      Print the default configuration file and exit
  --dump-palette     Print the default palette file and exit
  --anonymise        Mangle the tags and link names preserving 'look'
  --only-tags        Show only tag links
  --only-notes       Show only note links
  --debug            Set logging to debug level
```

You just need to run `bear-note-graph` after installing, by default everything will be output in `/tmp/`.

## Configuration file

This is straight from the defaults

```yaml
graph:
  anonymise: False                         # Make the output anonymous
  max_label_length: 50                     # Max length to show of the notes/tags
  include_only_tags: ""                    # Generate graph only for these tags (comma separated)
  exclude_titles: "readings,> "            # Skip all notes with titles containing this (comma separated)
  exclude_tags: "journal,@"                # Skip all tags containing this (comma separated)
  show_tag_edges: True                     # Whether to show tags and the linking between tags and notes
  show_note_edges: True                    # Whether to show note edges
  prune: False                             # Remove all notes with no tags (useful for include_only)
  overlap: False                           # Overlap mode for nodes in the graph
  sep: "+90,90"                            # Margins around nodes
  splines: True                            # Whether to use splines for the arrows
  bgcolor: "solarized-dark.base02"         # Background colour for the graph
  free_form: "K=0.9"                       # Any additional parameters to Graphviz
  tmp: "/tmp"                              # Temporary folder for the copy of the Bear SQLite database
  destination: "/tmp/bear_graph"           # Default destination for the Graphviz result
  output_format: "pdf"                     # Format of the output graphviz (only useful if run_graphviz is set)
  run_graphviz: "sfdp"                     # Algorithm to run automatically sfdp or neato recommended

tag:
  shape: "folder"                          # Shape
  style: "rounded,filled"                  # Style
  fill_color: "solarized-dark.yellow"      # Fill
  strike_color: "solarized-dark.orange"    # Stroke
  free_form: ""

note:
  shape: "note"
  style: "filled"
  fill_color: "solarized-dark.cyan"
  strike_color: "solarized-dark.blue"
  free_form: ""

tag_link:
  strike_color: "solarized-dark.magenta"
  arrowhead: "none"                        # Arrowhead
  free_form: "penwidth=\"2.5\""            # You can add any additional parameters

note_link:
  strike_color: "solarized-dark.green"
  arrowhead: "normal"
  free_form: "penwidth=\"2.5\""

custom_palette_here:                       # You can inline palettes here
  screaming_color: "#AAAAAA"               # You can inline palettes here
```

Most of the configuration parameters are for Graphviz, so check them in their [documentation](https://www.graphviz.org/doc/info/attrs.html).

## The Markdown parsing

In case you are curious, I wrote a custom [Markdown parser](bear_note_graph/parser). Because, why not, and I wanted to play with parser combinators. It is not as thoroughly tested as I would like, and it also has issues with blank spaces around the nodes, but for the purpose I wanted it, it works.

## The anonymisation

This is just so I can show my own graph without showing the tags or note titles. It's based on a relatively good hashing algorithm, and does some tweaking to make it look "realistic". 
