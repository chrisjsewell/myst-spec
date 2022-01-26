"""Create an MDAST syntax tree, via markdown-it parsing."""
import inspect
from typing import Callable, Dict, List, Optional

from markdown_it import MarkdownIt
from markdown_it.common.utils import unescapeAll
from markdown_it.token import Token

from .common import MdastNode


def parse(src: str) -> MdastNode:
    """Convert a CommonMark string to the Mdast AST format."""
    env = {}
    # note: store_labels/inline_definitions are not part of markdown-it JS,
    # they were added to markdown-it-py to allow AST building
    tokens = MarkdownIt(
        "commonmark", {"store_labels": True, "inline_definitions": True}
    ).parse(src, env)
    root_node = MditToMdastTransform()(tokens)
    # add definition lookup
    # TODO map to actual nodes?
    if "references" in env:
        defs = {
            k: {"url": v["href"], "title": v["title"]}
            for k, v in env["references"].items()
        }
        root_node.setdefault("data", {})["definitions"] = defs
    return root_node


class MditToMdastTransform:
    """Convert a sequence of Markdown-It tokens to an mdast syntax tree."""

    def __init__(self) -> None:
        # create transform lookup from class methods
        self._transforms: Dict[str, Callable[[Token], dict]] = {
            k[10:]: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if k.startswith("transform_")
        }

    def __call__(
        self, tokens: List[Token], parent: Optional[MdastNode] = None
    ) -> MdastNode:

        if parent is None:
            parent = MdastNode({"type": "root", "children": []}, None)

        # make reversed copy, so we can pop from end
        reversed_tokens = list(reversed(tokens))
        while reversed_tokens:
            token = reversed_tokens.pop()

            # some special logic, to make sure we collapse runs of text/softbreaks
            if token.type == "text" and reversed_tokens:
                token = token.copy()
                while reversed_tokens:
                    next_token = reversed_tokens[-1]
                    if next_token.type == "text":
                        token.content += next_token.content
                        reversed_tokens.pop()
                    elif next_token.type == "softbreak":
                        # note mdast does not specifically capture softbreaks as nodes:
                        # https://github.com/syntax-tree/mdast/issues/30
                        token.content += "\n"
                        reversed_tokens.pop()
                    else:
                        break

            # add terminal nodes
            if not token.nesting:
                self._add_child(parent, token)
                continue
            if token.nesting != 1:
                raise ValueError(f"Invalid token nesting {token.nesting} != 1")

            # add nested children
            nested_tokens = [token]
            nesting = 1
            while reversed_tokens and nesting:
                token = reversed_tokens.pop()
                nested_tokens.append(token)
                nesting += token.nesting
            if nesting:
                raise ValueError(f"unclosed tokens starting {nested_tokens[0]}")

            self._add_child(parent, nested_tokens[0], nested_tokens[1:-1])

        return parent

    def _add_child(
        self, parent: MdastNode, token: Token, children: Optional[List[Token]] = None
    ):
        if token.type not in self._transforms:
            raise ValueError(f"No transform for token type {token.type!r}")
        child_node = MdastNode(self._transforms[token.type](token), parent)
        # TODO position of inline nodes
        if token.map:
            # note, markdown-it does not supply column information, so we just supply a dummy value
            child_node["position"] = {
                "start": {"line": token.map[0] + 1, "column": 1},
                "end": {"line": token.map[1] + 1, "column": 1},
            }
        # bypass inline
        if children and len(children) == 1 and children[0].type == "inline":
            children = children[0].children
        # set list as not spread, if it contains a hidden paragraph (i.e. is tight)
        if (
            token.type == "paragraph_open"
            and token.hidden
            and child_node.parent.parent["type"] == "list"
        ):
            child_node.parent.parent["spread"] = False
        if (
            children
            and token.type != "image"  # image children are converted to 'alt' string
        ):
            self(children, child_node)
        parent.setdefault("children", []).append(child_node)

    def transform_paragraph_open(self, token: Token) -> dict:
        return {
            "type": "paragraph",
        }

    def transform_text(self, token: Token) -> dict:
        return {
            "type": "text",
            "value": token.content,
        }

    def transform_heading_open(self, token: Token) -> dict:
        return {
            "type": "heading",
            "depth": int(token.tag[1]),
            "data": {
                "markup": token.markup,
            },
        }

    def transform_hr(self, token: Token) -> dict:
        return {
            "type": "thematicBreak",
            "data": {
                "markup": token.markup,
            },
        }

    def transform_blockquote_open(self, token: Token) -> dict:
        return {
            "type": "blockquote",
            "data": {
                "markup": token.markup,
            },
        }

    def transform_bullet_list_open(self, token: Token) -> dict:
        return {
            "type": "list",
            "ordered": False,
            "spread": True,  # overridden if item contains hidden paragraph
            "data": {
                "markup": token.markup,
            },
        }

    def transform_ordered_list_open(self, token: Token) -> dict:
        node = {
            "type": "list",
            "ordered": True,
            "spread": True,  # overridden if item contains hidden paragraph
            "data": {
                "markup": token.markup,
            },
        }
        if "start" in token.attrs:
            node["start"] = int(token.attrs["start"])
        return node

    def transform_list_item_open(self, token: Token) -> dict:
        return {
            "type": "listItem",
            "ordered": False,
            # TODO spread
            "data": {
                "markup": token.markup,
            },
        }

    def transform_html_inline(self, token: Token) -> dict:
        return {
            "type": "html",
            "value": token.content,
        }

    def transform_html_block(self, token: Token) -> dict:
        return {
            "type": "html",
            "value": token.content,
        }

    def transform_fence(self, token: Token) -> dict:
        node = {
            "type": "code",
            "value": token.content,
            "data": {
                "markup": token.markup,
            },
        }
        lang_info = unescapeAll(token.info).split(maxsplit=1)
        if lang_info:
            node["lang"] = lang_info.pop(0)
        if lang_info:
            node["meta"] = lang_info.pop(0)
        return node

    def transform_code_block(self, token: Token) -> dict:
        return {
            "type": "code",
            "value": token.content,
        }

    def transform_definition(self, token: Token) -> dict:
        return {
            "type": "definition",
            "identifier": token.meta["id"],
            "label": token.meta["label"],
            "url": token.meta["url"],
            "title": token.meta["title"],
        }

    def transform_em_open(self, token: Token) -> dict:
        return {
            "type": "emphasis",
            "data": {
                "markup": token.markup,
            },
        }

    def transform_strong_open(self, token: Token) -> dict:
        return {
            "type": "strong",
            "data": {
                "markup": token.markup,
            },
        }

    def transform_code_inline(self, token: Token) -> dict:
        return {
            "type": "inlineCode",
            "value": token.content,
            "data": {
                "markup": token.markup,
            },
        }

    def transform_hardbreak(self, token: Token) -> dict:
        return {"type": "break"}

    def transform_softbreak(self, token: Token) -> dict:
        return {"type": "text", "value": "\n"}

    def transform_link_open(self, token: Token) -> dict:
        if token.meta and "label" in token.meta:
            return {
                "type": "linkReference",
                "referenceType": "full",
                "identifier": token.meta["label"],
                # TODO "label" should be the non-normalized label
            }
        # TODO capture if it was an autolink?
        node = {
            "type": "link",
            "url": token.attrs["href"],
        }
        if "title" in token.attrs:
            node["title"] = token.attrs["title"]
        return node

    def renderInlineAsText(self, tokens: List[Token]) -> str:
        """Special kludge for image `alt` attributes to conform CommonMark spec."""
        result = ""
        for token in tokens or []:
            if token.type == "text":
                result += token.content
            else:
                result += self.renderInlineAsText(token.children or [])
        return result

    def transform_image(self, token: Token) -> dict:
        alt = self.renderInlineAsText(token.children or [])
        if token.meta and "label" in token.meta:
            return {
                "type": "imageReference",
                "alt": alt,
                "referenceType": "full",
                "identifier": token.meta["label"],
                # TODO "label" should be the non-normalized label
            }
        node = {
            "type": "image",
            "url": token.attrs["src"],
            "alt": alt,
        }
        if "title" in token.attrs:
            node["title"] = token.attrs["title"]
        return node
