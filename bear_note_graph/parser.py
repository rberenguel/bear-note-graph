import logging
import re
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import List, Match, Optional, Pattern, Tuple

logger = logging.getLogger("bear_note_graph.parser")


@dataclass
class Block:
    text: str


@dataclass
class CodeBlock(Block):
    """Holder for a code block"""

    language: Optional[str]
    pattern: Pattern = field(
        repr=False,
        default=re.compile(r"```(\S+)([^`]*)```\n?(.*)", re.MULTILINE | re.DOTALL),
    )


@dataclass
class BareCodeBlock(Block):
    """Holder for a code block with no language. The generic one does not match if language is empty,weird"""

    pattern: Pattern = field(
        repr=False,
        default=re.compile(r"```\s*([^`]*)```\n?(.*)", re.MULTILINE | re.DOTALL),
    )


@dataclass
class LinkBlock(Block):
    """Holder for a link block"""

    link: Optional[str]
    pattern: Pattern = field(
        repr=False,
        default=re.compile(r"\[([^]]*)\]\(([^)]*)\)(.*)", re.MULTILINE | re.DOTALL),
    )


@dataclass
class NoteLinkBlock(Block):
    """Holder for a link block"""

    pattern: Pattern = field(
        repr=False,
        default=re.compile(r"\[\[([^]]*)\]\](.*)", re.MULTILINE | re.DOTALL),
    )


@dataclass
class BracketBlock(Block):
    """Holder for an image block"""

    pattern: Pattern = field(
        repr=False, default=re.compile(r"\[([^]]*)\](.*)", re.MULTILINE | re.DOTALL)
    )


@dataclass
class InlinedCodeBlock(Block):
    """Holder for an inlined code block"""

    pattern: Pattern = field(
        repr=False, default=re.compile(r"`([^`\n]+)`(.*)", re.MULTILINE | re.DOTALL)
    )


@dataclass
class TextBlock(Block):
    """Holder for _no other kind of block_ so it will have a pattern that matches
anything that is not matched by others"""

    pattern: Pattern = field(
        repr=False, default=re.compile(r"([^`#[]+)(.*)", re.MULTILINE | re.DOTALL)
    )


@dataclass
class FallbackTextBlock(Block):
    """If we could not capture "specials" with the proper parsers, capture the possible problems here"""

    pattern: Pattern = field(
        repr=False, default=re.compile(r"(`|#|[|]|\[)(.*)", re.MULTILINE | re.DOTALL)
    )


@dataclass
class HeadingBlock(Block):
    """Heading block"""

    text: str
    pattern: Pattern = field(
        repr=False, default=re.compile(r"^#+ ([^\n]+)(.*)", re.MULTILINE | re.DOTALL)
    )


@dataclass
class TaskBlock(Block):
    """Bear task block"""

    text: str
    pattern: Pattern = field(
        repr=False, default=re.compile(r"\[.\]([^\n]+)(.*)", re.MULTILINE | re.DOTALL)
    )


@dataclass
class TagBlock(Block):
    """Holder for tag, a tag starts with a hash and has no spaces after the hash. Has to be outside a code block, link context or inlined code block"""

    text: str
    pattern: Pattern = field(
        repr=False,
        default=re.compile(r"^(#[^#][\S]+)[.,(){}!?]?(.*)", re.MULTILINE | re.DOTALL),
    )


class ParseError(Exception):
    pass


class Parser:
    """General parser stuff. It can hold an optional list of parsers, to then have
multiple parsers (sequential, one-off) with the same interface, parse"""

    def __init__(self, parsers: Optional[List["Parser"]] = None):
        self.parsers = parsers

    @abstractmethod
    def parse(self, text) -> Tuple[Optional[Block], Optional[str]]:
        pass


class RegexParser(Parser):
    pattern: Pattern

    def parse(self, text) -> Tuple[Optional[Block], Optional[str]]:
        if text is None:
            logger.debug("Text is None in Parser")
            return None, None
        matching = self.pattern.match(text)
        if matching is None:
            logger.debug(
                "There are no matches for text <<%s>> in %s, with pattern %s",
                text,
                self.__class__,
                self.pattern.pattern,
            )
            return None, text
        logger.debug("Matching: %s, Groups: %s", matching, matching.groups())
        return self._map(matching)

    @staticmethod
    @abstractmethod
    def _map(matching):
        pass


class CodeBlockParser(RegexParser, CodeBlock):
    """Parser for a code block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[CodeBlock], Optional[str]]:
        code_block = matching.group(2)
        language = matching.group(1)
        rest = matching.group(3)
        if rest == "":
            rest = None
        return CodeBlock(text=code_block, language=language), rest


class BareCodeBlockParser(RegexParser, BareCodeBlock):
    """Parser for a code block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[BareCodeBlock], Optional[str]]:
        code_block = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return BareCodeBlock(text=code_block), rest


class LinkBlockParser(RegexParser, LinkBlock):
    """Parser for a link block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[LinkBlock], Optional[str]]:
        title = matching.group(1)
        link = matching.group(2)
        rest = matching.group(3)
        if rest == "":
            rest = None
        return LinkBlock(text=title, link=link), rest


class NoteLinkBlockParser(RegexParser, NoteLinkBlock):
    """Parser for a link block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[NoteLinkBlock], Optional[str]]:
        title = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return NoteLinkBlock(text=title), rest


class BracketBlockParser(RegexParser, BracketBlock):
    """Parser for an image block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[BracketBlock], Optional[str]]:
        link = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return BracketBlock(text=link), rest


class InlinedCodeBlockParser(RegexParser, InlinedCodeBlock):
    """Parser for a code block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[InlinedCodeBlock], Optional[str]]:
        code_block = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return InlinedCodeBlock(text=code_block), rest


class TaskBlockParser(RegexParser, TaskBlock):
    """Parser for a code block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[TaskBlock], Optional[str]]:
        code_block = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return TaskBlock(text=code_block), rest


class HeadingBlockParser(RegexParser, HeadingBlock):
    """Parser for a code block"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[HeadingBlock], Optional[str]]:
        heading = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return HeadingBlock(text=heading), rest


class TextBlockParser(RegexParser, TextBlock):
    """Parser for anything that is not a code block nor a tag, nor... Keep in mind though that tags appears only (technically) in specific contexts, and this ordering needs to be handled when processing items in order"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[TextBlock], Optional[str]]:
        text_block = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return TextBlock(text=text_block), rest


class FallbackTextBlockParser(RegexParser, FallbackTextBlock):
    """Parser for broken code blocks, backticks, etc"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[FallbackTextBlock], Optional[str]]:
        text_block = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return FallbackTextBlock(text=text_block), rest


class TagBlockParser(RegexParser, TagBlock):
    """Parser for a tag"""

    @staticmethod
    def _map(matching: Match) -> Tuple[Optional[TagBlock], Optional[str]]:
        tag_block = matching.group(1)
        rest = matching.group(2)
        if rest == "":
            rest = None
        return TagBlock(text=tag_block), rest


class OrderedOneOfParser(Parser):
    """One of a list of parsers"""

    def parse(self, text):
        parsers = self.parsers
        if parsers is None:
            raise ParseError("We can't have an OrderedOneOfParser with no parsers")
        for parser in parsers:
            block, rest = parser.parse(text)
            if block is None:
                continue
            return block, rest
        return None, text


class SequenceParser(Parser):
    """Given a parser, try to use it until exhaustion of input or impossibility to parse"""

    def parse(self, text):
        parsers = self.parsers
        if parsers is None:
            raise ParseError("We can't sequence if there are no parsers")
        if len(parsers) > 1:
            raise ParseError(
                "We only sequence one parser, create an OrderedOneOfParser first"
            )
        parser = parsers[0]
        block, rest = parser.parse(text)
        ret = []
        if block is not None:
            ret = [block]
        while rest is not None:
            old_rest = rest
            block, rest = parser.parse(rest)
            if rest == old_rest:
                err = f"No parser can process <<{rest}>>"
                raise ParseError(err)
            if block is not None:
                ret += [block]

        return ret, rest

    def _map(self):
        pass


ONE_OF_MARKDOWN_NODE = OrderedOneOfParser(
    [
        HeadingBlockParser(),
        TagBlockParser(),
        TextBlockParser(),
        CodeBlockParser(),
        BareCodeBlockParser(),
        TaskBlockParser(),
        InlinedCodeBlockParser(),
        NoteLinkBlockParser(),
        LinkBlockParser(),
        BracketBlockParser(),
        FallbackTextBlockParser(),
    ]
)

MARKDOWN_PARSER = SequenceParser([ONE_OF_MARKDOWN_NODE])
