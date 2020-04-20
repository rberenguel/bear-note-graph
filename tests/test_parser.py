import pytest
from bear_note_graph.parser import (
    InlinedCodeBlock,
    BareCodeBlock,
    BareCodeBlockParser,
    LinkBlock,
    TextBlockParser,
    CodeBlockParser,
    OrderedOneOfParser,
    LinkBlockParser,
    TagBlockParser,
    SequenceParser,
    TextBlock,
    CodeBlock,
    TagBlock,
    InlinedCodeBlockParser,
)
from random import sample

CODE = '\ndef hello_world():\n\t print("Hello world")\n'
TAG = "#this/is/a/tag"
TITLE = "This goes somewhere"
BLOCKS = {
    "text_block": "Text text\n text\n\t more text",
    "code": CODE,
    "title": TITLE,
    "code_block": f"\n```python{CODE}```\n",
    "code_block_no_lang": "\n```import org.apache.spark.SparkSession\n```\n",
    "unterminated_code_block": "\n```oh crap\n\n",
    "tag_block": TAG,
    "tag_in_code_block": f"\n```foo\n{TAG}\n```\n",
    "tag_in_inlined_code_block": f"`{TAG}` ",
    "tag_in_link_block": f"[{TITLE}](https://foo.com/{TAG})",
}


def test_text_block():
    text_block = BLOCKS["text_block"]
    unterminated_code_block = BLOCKS["unterminated_code_block"]
    text = f"{text_block}{unterminated_code_block}"
    parsed_text_block, rest = TextBlockParser().parse(text)
    assert parsed_text_block == TextBlock(text_block + "\n")
    assert rest == unterminated_code_block[1:]


def test_tag_block():
    tag_block = BLOCKS["tag_block"]
    unterminated_code_block = BLOCKS["unterminated_code_block"]
    text = f"{tag_block}{unterminated_code_block}"
    parsed_tag_block, rest = TagBlockParser().parse(text)
    assert parsed_tag_block == TagBlock(tag_block)
    assert rest == unterminated_code_block


def test_link_block():
    link_block = BLOCKS["tag_in_link_block"]
    text_block = BLOCKS["text_block"]
    tag_block = BLOCKS["tag_block"]
    title = BLOCKS["title"]
    text = f"{text_block} {link_block} {text_block}"
    text_or_link = OrderedOneOfParser([TextBlockParser(), LinkBlockParser()])
    sequenced = SequenceParser([text_or_link])
    blocks, rest = sequenced.parse(text)
    assert blocks[0] == TextBlock(text_block + " ")
    assert blocks[1] == LinkBlock(text=title, link=f"https://foo.com/{tag_block}")
    assert blocks[2] == TextBlock(" " + text_block)


def test_parse_inlined_code_block():
    text_block = BLOCKS["text_block"]
    inlined_code_block = BLOCKS["tag_in_inlined_code_block"]
    code = BLOCKS["tag_block"]
    text = f"{inlined_code_block}{text_block}"
    block, rest = InlinedCodeBlockParser().parse(text)
    assert block == InlinedCodeBlock(f"{code}")
    assert rest == " " + text_block


def test_problematic_code_block():
    text = """``` 
A:B:C~E:F~G:H~~I::J~K~L
``` 

There are"""

    block, rest = BareCodeBlockParser().parse(text)
    assert block == BareCodeBlock("A:B:C~E:F~G:H~~I::J~K~L\n")
    assert rest == " \n\nThere are"


def test_parse_code_block():
    text_block = BLOCKS["text_block"]
    code_block = BLOCKS["code_block"][1:]
    code = BLOCKS["code"]
    text = f"{code_block}{text_block}"
    block, rest = CodeBlockParser().parse(text)
    assert block == CodeBlock(f"{code}", "python")
    assert rest == text_block

    text_block = BLOCKS["text_block"]
    code_block = BLOCKS["tag_in_code_block"][1:]
    code = BLOCKS["tag_block"]
    text = f"{code_block}{text_block}"
    block, rest = CodeBlockParser().parse(text)
    assert block == CodeBlock(f"\n{code}\n", "foo")
    assert rest == text_block


def test_parse_text_and_code_block():
    text_block = BLOCKS["text_block"]
    code_block = BLOCKS["code_block"]
    second_text_block = "".join(sample(BLOCKS["text_block"], 10))  # This can
    # cause an
    # spurious
    # failure if
    # we hit
    # badly on a
    # new line,
    # possibly
    code = BLOCKS["code"]
    text = f"{text_block}{code_block}{second_text_block}"
    text_or_code = OrderedOneOfParser([TextBlockParser(), CodeBlockParser()])
    sequenced = SequenceParser([text_or_code])
    blocks, rest = sequenced.parse(text)
    assert blocks[0] == TextBlock(text_block + "\n")
    assert blocks[1] == CodeBlock(f"{code}", "python")
    assert blocks[2] == TextBlock(second_text_block)
    assert rest is None


def test_parse_text_and_tag_code_block():
    text_block = BLOCKS["text_block"]
    code_block = BLOCKS["code_block"]
    tag_block = BLOCKS["tag_block"]
    tag_in_code = BLOCKS["tag_in_code_block"]
    second_text_block = "".join(sample(BLOCKS["text_block"], 10))
    code = BLOCKS["code"]
    text = f"{text_block}\n{tag_block}{code_block}{second_text_block}{tag_in_code}"
    print(text)
    text_or_code = OrderedOneOfParser(
        [TextBlockParser(), CodeBlockParser(), TagBlockParser()]
    )
    sequenced = SequenceParser([text_or_code])
    blocks, rest = sequenced.parse(text)
    assert blocks[0] == TextBlock(text_block + "\n")
    assert blocks[1] == TagBlock(tag_block)
    assert blocks[2] == TextBlock("\n")
    assert blocks[3] == CodeBlock(f"{code}", "python")
    assert blocks[4] == TextBlock(" " + second_text_block + "\n")
    assert blocks[5] == CodeBlock(f"\n{tag_block}\n", "foo")
    assert rest is None


def test_parse_text_and_tag_code_block():
    text_block = BLOCKS["text_block"]
    code_block = BLOCKS["code_block"]
    tag_block = BLOCKS["tag_block"]
    tag_in_code = BLOCKS["tag_in_code_block"]
    tag_in_inlined_code_block = BLOCKS["tag_in_inlined_code_block"]
    second_text_block = "".join(sample(BLOCKS["text_block"], 10))
    code = BLOCKS["code"]
    text = f"{text_block}\n{tag_block}{code_block}{tag_in_inlined_code_block}{second_text_block}{tag_in_code}"
    print(text)
    text_or_code = OrderedOneOfParser(
        [
            TextBlockParser(),
            CodeBlockParser(),
            InlinedCodeBlockParser(),
            TagBlockParser(),
        ]
    )
    sequenced = SequenceParser([text_or_code])
    blocks, rest = sequenced.parse(text)
    assert blocks[0] == TextBlock(text_block + "\n")
    assert blocks[1] == TagBlock(tag_block)
    assert blocks[2] == TextBlock("\n")
    assert blocks[3] == CodeBlock(f"{code}", "python")
    assert blocks[4] == InlinedCodeBlock(f"{tag_block}")
    assert blocks[5] == TextBlock(" " + second_text_block + "\n")
    assert blocks[6] == CodeBlock(f"\n{tag_block}\n", "foo")
    assert rest is None
