import html
import inspect
from typing import Callable, Dict

from .common import MdastNode


def render(root: MdastNode) -> str:
    """Convert MDAST to CommonMark compliant HTML."""
    return MdastToHtmlTransform()(root)


def escape_html(raw: str) -> str:
    return html.escape(raw).replace("&#x27;", "'")


class MdastToHtmlTransform:
    """Convert an Mdast syntax tree to HTML"""

    def __init__(self) -> None:

        # create enter/exit lookup from class methods
        self._enter: Dict[str, Callable[[MdastNode], dict]] = {
            k[6:]: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if k.startswith("enter_")
        }
        self._exit: Dict[str, Callable[[MdastNode], dict]] = {
            k[5:]: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)
            if k.startswith("exit_")
        }

    def __call__(
        self, root: MdastNode, skip_missing_enter=False, skip_missing_exit=True
    ) -> str:
        self._string = ""
        self._skip_missing_enter = skip_missing_enter
        self._skip_missing_exit = skip_missing_exit
        for _ in root.walk(self._callback_enter_node, self._callback_exit_node):
            pass
        return self._string

    def _callback_enter_node(self, node: MdastNode) -> None:
        if node.type not in self._enter:
            if not self._skip_missing_enter:
                raise ValueError(f"No enter method for node type {node.type!r}")
        else:
            self._string += self._enter[node.type](node)

        # add a newline after opening a block that contains other blocks,
        # unless the next child is a hidden paragraph, or an empty list item
        if (
            node.type
            in {
                "blockquote",
                "code",
                "list",
                "listItem",
            }
            and not (node.type == "listItem" and not node.children)
            and not (node.children and self._hidden_paragraph(node.children[0]))
        ):
            self._string += "\n"

    def _callback_exit_node(self, node: MdastNode) -> None:
        if node.type not in self._exit:
            if not self._skip_missing_exit:
                raise ValueError(f"No exit method for node type {node.type!r}")
        else:
            self._string += self._exit[node.type](node)

            # Insert a newline between hidden paragraph and subsequent block-level node
            if self._hidden_paragraph(node) and node.next_sibling:
                self._string += "\n"

            # add a newline after a block-level closure
            elif (
                node.type
                in {
                    "blockquote",
                    "code",
                    "heading",
                    "html",
                    "list",
                    "listItem",
                    "paragraph",
                }
                and not self._hidden_paragraph(node)
            ):
                self._string += "\n"

    def enter_root(self, node: MdastNode) -> str:
        return ""

    def _hidden_paragraph(self, node: MdastNode) -> bool:
        """Whether to hide paragraph, if it is in a tight list"""
        return (
            node.type == "paragraph"
            and node.parent.parent.type == "list"
            and not node.parent.parent.get("spread", False)
        )

    def enter_paragraph(self, node: MdastNode) -> str:
        if self._hidden_paragraph(node):
            return ""
        return "<p>"

    def exit_paragraph(self, node: MdastNode) -> str:
        if self._hidden_paragraph(node):
            return ""
        return "</p>"

    def enter_text(self, node: MdastNode) -> str:
        return escape_html(node["value"])

    def enter_break(self, node: MdastNode) -> str:
        return "<br />\n"

    def enter_html(self, node: MdastNode) -> str:
        return node["value"]

    def enter_heading(self, node: MdastNode) -> str:
        return f"<h{node['depth']}>"

    def exit_heading(self, node: MdastNode) -> str:
        return f"</h{node['depth']}>"

    def enter_list(self, node: MdastNode) -> str:
        if node.get("ordered"):
            if "start" in node:
                return f"<ol start=\"{node['start']}\">"
            return "<ol>"
        return "<ul>"

    def exit_list(self, node: MdastNode) -> str:
        if node.get("ordered"):
            return "</ol>"
        return "</ul>"

    def enter_listItem(self, node: MdastNode) -> str:
        return "<li>"

    def exit_listItem(self, node: MdastNode) -> str:
        return "</li>"

    def enter_inlineCode(self, node: MdastNode) -> str:
        return f"<code>{escape_html(node['value'])}</code>"

    def enter_code(self, node: MdastNode) -> str:
        content = escape_html(node["value"])
        lang = node.get("lang")
        if lang:
            return f'<pre><code class="language-{lang}">{content}</code></pre>'
        return f"<pre><code>{content}</code></pre>"

    def enter_blockquote(self, node: MdastNode) -> str:
        return "<blockquote>"

    def exit_blockquote(self, node: MdastNode) -> str:
        return "</blockquote>"

    def enter_definition(self, node: MdastNode) -> str:
        return ""

    def enter_thematicBreak(self, node: MdastNode) -> str:
        return "<hr />\n"

    def enter_emphasis(self, node: MdastNode) -> str:
        return "<em>"

    def exit_emphasis(self, node: MdastNode) -> str:
        return "</em>"

    def enter_strong(self, node: MdastNode) -> str:
        return "<strong>"

    def exit_strong(self, node: MdastNode) -> str:
        return "</strong>"

    def enter_link(self, node: MdastNode) -> str:
        url = escape_html(node["url"])
        if node.get("title"):
            title = escape_html(node["title"])
            return f'<a href="{url}" title="{title}">'
        return f'<a href="{url}">'

    def exit_link(self, node: MdastNode) -> str:
        return "</a>"

    def enter_linkReference(self, node: MdastNode) -> str:
        definitions = node.root.get("data", {}).get("definitions", {})
        if node["identifier"] not in definitions:
            raise ValueError(f"No definition for reference {node['identifier']!r}")
        data = definitions[node["identifier"]]
        url = escape_html(data["url"])
        if data.get("title"):
            title = escape_html(data["title"])
            return f'<a href="{url}" title="{title}">'
        return f'<a href="{url}">'

    def exit_linkReference(self, node: MdastNode) -> str:
        return "</a>"

    def enter_image(self, node: MdastNode) -> str:
        url = escape_html(node["url"])
        alt = escape_html(node["alt"])
        if node.get("title"):
            title = escape_html(node["title"])
            return f'<img src="{url}" alt="{alt}" title="{title}" />'
        return f'<img src="{url}" alt="{alt}" />'

    def enter_imageReference(self, node: MdastNode) -> str:
        definitions = node.root.get("data", {}).get("definitions", {})
        if node["identifier"] not in definitions:
            raise ValueError(f"No definition for reference {node['identifier']!r}")
        data = definitions[node["identifier"]]
        url = escape_html(data["url"])
        alt = escape_html(node["alt"])
        if data.get("title"):
            title = escape_html(data["title"])
            return f'<img src="{url}" alt="{alt}" title="{title}" />'
        return f'<img src="{url}" alt="{alt}" />'
