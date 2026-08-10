"""Assertions for the HTMX fragment/swap contract (architecture invariant AD-7).

The list container has stable id ``#todo-list``; each item fragment is a single
root element with id ``todo-<id>``. Mutation routes must return fragments the
client can swap consistently. These helpers keep that contract checkable from
integration tests without pulling in a browser.
"""

from __future__ import annotations

from html.parser import HTMLParser


class _RootCounter(HTMLParser):
    """Counts top-level (depth-0) elements and captures the first one's id."""

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.root_count = 0
        self.first_root_id: str | None = None
        # void elements have no closing tag and must not affect depth
        self._void = {"br", "hr", "img", "input", "meta", "link", "source"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.depth == 0:
            self.root_count += 1
            if self.first_root_id is None:
                self.first_root_id = dict(attrs).get("id")
        if tag not in self._void:
            self.depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.depth == 0:
            self.root_count += 1
            if self.first_root_id is None:
                self.first_root_id = dict(attrs).get("id")

    def handle_endtag(self, tag: str) -> None:
        if tag not in self._void and self.depth > 0:
            self.depth -= 1


def assert_single_item_fragment(html: str, todo_id: int) -> None:
    """A mutation route returned exactly one root element with id ``todo-<id>``."""
    parser = _RootCounter()
    parser.feed(html)
    assert parser.root_count == 1, (
        f"Expected a single root element in the item fragment, "
        f"found {parser.root_count}. Violates AD-7."
    )
    expected = f"todo-{todo_id}"
    assert parser.first_root_id == expected, (
        f"Expected fragment root id '{expected}', got '{parser.first_root_id}'. "
        f"Violates AD-7 (client swap target)."
    )


def assert_list_container(html: str) -> None:
    """The rendered page/list fragment contains the stable ``#todo-list`` container."""
    assert 'id="todo-list"' in html or "id='todo-list'" in html, (
        "Expected the stable list container id 'todo-list' in the response. "
        "Violates AD-7."
    )
