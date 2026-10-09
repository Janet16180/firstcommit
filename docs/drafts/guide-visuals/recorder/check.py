"""Check every terminal and editor on the storyboard is, character for character, recorded output."""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class Pres(HTMLParser):
    """Collect the text of every <pre>, its class and its block lines."""

    def __init__(self) -> None:
        super().__init__()
        self.pres: list[tuple[str, str]] = []
        self.depth = 0
        self.kind = ""
        self.text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start a <pre>, or a new line at a decoder's line span."""
        if tag == "pre":
            self.depth, self.kind, self.text = 1, dict(attrs).get("class") or "", ""
        elif self.depth and tag == "span" and "dl" in (dict(attrs).get("class") or "").split():
            self.text += "\n"

    def handle_endtag(self, tag: str) -> None:
        """Keep a finished <pre>."""
        if tag == "pre":
            self.pres.append((self.kind, self.text))
            self.depth = 0

    def handle_data(self, data: str) -> None:
        """Add text inside a <pre>."""
        if self.depth:
            self.text += data


runs = Path(sys.argv[1])
scenes = {path.stem: path.read_text() for path in runs.glob("*.txt")}
recorded = "".join(scenes.values())
parser = Pres()
parser.feed(Path(sys.argv[2]).read_text())
bad = 0
for kind, text in parser.pres:
    if "editor" in kind:
        ok = text.removeprefix(".git/MERGE_MSG") + "\n" == scenes["merge-editor"]
    else:
        body = text.lstrip("\n") + "\n"
        ok = all(
            any(chunk in scene for scene in scenes.values())
            for chunk in re.split(r"(?=^\$ )", body, flags=re.M)
            if chunk
        )
    bad += not ok
    print("ok " if ok else "BAD", kind, repr(text[:50]))
sys.exit(1 if bad else 0)
