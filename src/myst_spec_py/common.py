from typing import Callable, Iterator, List, Optional


class MdastNode(dict):
    """A dictionary which can also have a parent."""

    def __init__(self, mapping: dict, parent: Optional["MdastNode"] = None):
        super().__init__(mapping)
        self._parent = parent

    @property
    def type(self) -> str:
        """The type of this node."""
        return self["type"]

    @property
    def parent(self) -> "MdastNode":
        """The parent node, or a parent with type 'null'."""
        if self._parent is None:
            return MdastNode({"type": "null"})
        return self._parent

    @property
    def root(self) -> "MdastNode":
        """The root node, or a root with type 'null'."""
        if self._parent is None:
            return self
        return self._parent.root

    @property
    def children(self) -> List["MdastNode"]:
        """The children of this node, or an empty list."""
        return self.get("children", [])

    @property
    def index(self) -> int:
        """The index of this node in its parent's children."""
        return self.parent.children.index(self)

    @property
    def previous_sibling(self) -> Optional["MdastNode"]:
        """The previous sibling."""
        if self.index == 0:
            return None
        return self.parent.children[self.index - 1]

    @property
    def next_sibling(self) -> Optional["MdastNode"]:
        """The next sibling."""
        try:
            return self.parent.children[self.index + 1]
        except IndexError:
            return None

    def walk(
        self,
        enter_callback: Optional[Callable[["MdastNode"], None]] = None,
        exit_callback: Optional[Callable[["MdastNode"], None]] = None,
    ) -> Iterator["MdastNode"]:
        """Walk the tree, calling an optional callback on each enter/exit."""
        if enter_callback is not None:
            enter_callback(self)
        for child in self.children:
            yield from child.walk(enter_callback, exit_callback)
        if exit_callback is not None:
            exit_callback(self)
