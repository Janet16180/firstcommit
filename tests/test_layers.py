"""
The package's layers, read from its source: who may import whom (DESIGN.md section 7).

interface (cli, web) -> orchestration (game) -> core -> data (save, chapters) -> termlab.
"""

import ast
import re
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

import firstcommit

PACKAGE = Path(firstcommit.__file__).parent
LAYERS = {"data": 0, "core": 1, "orchestration": 2, "interface": 3}
INTERFACE_MAY_USE = {
    "firstcommit.game": None,
    "firstcommit.markup": None,
    "firstcommit.chapters": None,
    "firstcommit.gitcmd": {"isolation", "shell_environment"},
    "firstcommit.save": {"home", "SaveError"},
}
"""Package modules an interface may import, with the names it may use from each (None: any)."""
RUNTIME_WORDS = re.compile(r"docker|qemu|wsl", re.IGNORECASE)


def module_name(path: Path) -> str:
    """
    Name the module of a source file.

    Parameters
    ----------
    path : Path
        A ``.py`` file under the package.

    Returns
    -------
    str
        Its dotted name, such as ``firstcommit.web.routes`` (a package is named by its ``__init__``).
    """
    parts = ["firstcommit", *path.relative_to(PACKAGE).with_suffix("").parts]
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


SOURCES = {module_name(path): path for path in sorted(PACKAGE.rglob("*.py"))}


def layer(module: str) -> str:
    """
    Give a package module's layer.

    Parameters
    ----------
    module : str
        A dotted module name in the package.

    Returns
    -------
    str
        A key of `LAYERS`.
    """
    short = module.removeprefix("firstcommit").removeprefix(".")
    if short in ("cli", "__main__", "web") or short.startswith("web."):
        kind = "interface"
    elif short == "game":
        kind = "orchestration"
    elif short in ("save", "chapters", ""):
        kind = "data"
    else:
        kind = "core"
    return kind


def resolve(importer: str, node: ast.ImportFrom) -> str:
    """
    Turn the module of a ``from ... import`` into an absolute name.

    Parameters
    ----------
    importer : str
        The importing module.
    node : ast.ImportFrom
        The statement.

    Returns
    -------
    str
        The absolute module name it imports from.
    """
    if node.level == 0:
        return node.module or ""
    package = importer if SOURCES[importer].name == "__init__.py" else importer.rsplit(".", 1)[0]
    base = package.rsplit(".", node.level - 1)[0] if node.level > 1 else package
    return f"{base}.{node.module}" if node.module else base


def imports(module: str) -> Iterator[tuple[str, str | None]]:
    """
    List what a module imports, at any depth (function-level imports included).

    Parameters
    ----------
    module : str
        A package module.

    Yields
    ------
    tuple[str, str | None]
        ``(module, name)``: the module imported, and the name taken from it (None for the whole
        module). The package's ``__init__`` files define nothing, so a name imported from a
        package is a module: ``from firstcommit import save`` yields ``("firstcommit.save", None)``.
    """
    for node in ast.walk(ast.parse(SOURCES[module].read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, None
        elif isinstance(node, ast.ImportFrom):
            source = resolve(module, node)
            from_package = source in SOURCES and SOURCES[source].name == "__init__.py"
            for alias in node.names:
                yield (f"{source}.{alias.name}", None) if from_package else (source, alias.name)


def names_used(module: str, imported: str) -> set[str] | None:
    """
    Find the names a module uses from a package module it imports.

    Parameters
    ----------
    module : str
        The importing module.
    imported : str
        The imported package module.

    Returns
    -------
    set[str] | None
        The names taken with ``from ... import`` or read as attributes of the module's local
        name; None if the module is imported in a way this cannot follow (``import a.b``).
    """
    tree = ast.parse(SOURCES[module].read_text())
    local = imported.rsplit(".", 1)[-1]
    found: set[str] = set()
    followable = True
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and resolve(module, node) == imported:
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import) and any(alias.name == imported for alias in node.names):
            followable = False
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == local:
            found.add(node.attr)
    return found if followable else None


def package_imports(module: str) -> set[str]:
    """
    List the package modules a module imports.

    Parameters
    ----------
    module : str
        A package module.

    Returns
    -------
    set[str]
        Dotted names under ``firstcommit``.
    """
    return {name for name, _ in imports(module) if name == "firstcommit" or name.startswith("firstcommit.")}


INTERFACES = [module for module in SOURCES if layer(module) == "interface"]
LEVELS = [module for module in SOURCES if module.startswith("firstcommit.levels.") and not module.rsplit(".", 1)[-1].startswith("_")]


def test_the_import_reader_sees_the_known_imports() -> None:
    assert {"firstcommit.runner", "firstcommit.save", "firstcommit.score", "firstcommit.markup"} <= package_imports("firstcommit.game")
    assert "firstcommit.web.routes" in package_imports("firstcommit.cli")
    assert names_used("firstcommit.cli", "firstcommit.save") == {"home", "SaveError"}


@pytest.mark.parametrize("module", INTERFACES)
def test_an_interface_uses_only_the_game_the_text_parser_the_chapters_and_two_helpers(module: str) -> None:
    for imported in package_imports(module):
        if layer(imported) == "interface":
            continue
        assert imported in INTERFACE_MAY_USE, f"{module} imports {imported}"
        allowed = INTERFACE_MAY_USE[imported]
        used = names_used(module, imported)
        assert allowed is None or (used is not None and used <= allowed), f"{module} uses {used} from {imported}"


@pytest.mark.parametrize("module", SOURCES)
def test_no_module_imports_a_layer_above_its_own(module: str) -> None:
    upward = sorted(imported for imported in package_imports(module) if LAYERS[layer(imported)] > LAYERS[layer(module)])
    assert not upward, f"{module} ({layer(module)}) imports {upward}"


@pytest.mark.parametrize("module", [module for module in SOURCES if layer(module) in ("core", "data")])
def test_core_and_data_modules_never_import_an_interface(module: str) -> None:
    assert not [imported for imported in package_imports(module) if layer(imported) == "interface"]


@pytest.mark.parametrize("module", LEVELS)
def test_a_level_imports_only_kit_its_chapter_helpers_and_the_standard_library(module: str) -> None:
    chapter = module.rsplit(".", 1)[-1].split("_", 1)[0]
    for imported, _ in imports(module):
        helper = imported.startswith(f"firstcommit.levels._{chapter}")
        assert imported == "firstcommit.kit" or helper or imported.split(".")[0] in sys.stdlib_module_names, f"{module} imports {imported}"


@pytest.mark.parametrize("module", SOURCES)
def test_the_package_needs_only_the_standard_library_and_termlab(module: str) -> None:
    for imported, _ in imports(module):
        assert imported.split(".")[0] in {*sys.stdlib_module_names, "termlab", "firstcommit"}, f"{module} imports {imported}"


def runtime_neutral_files() -> list[Path]:
    """
    List the package files that must not know where the game runs: all but level and card content.

    Returns
    -------
    list[Path]
        Every file under the package outside ``levels/`` and ``content/`` (and caches).
    """
    skipped = {"levels", "content", "__pycache__"}
    return [path for path in sorted(PACKAGE.rglob("*")) if path.is_file() and not skipped & set(path.relative_to(PACKAGE).parts)]


@pytest.mark.parametrize("path", runtime_neutral_files(), ids=lambda path: str(path.relative_to(PACKAGE)))
def test_the_package_never_names_the_runtime_it_runs_on(path: Path) -> None:
    found = RUNTIME_WORDS.findall(path.read_text(errors="replace"))
    assert not found, f"{path.name} names {sorted(set(found))}"
