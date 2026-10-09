import ast
import inspect

from firstcommit import records, repomap

RECORD_NAMES = ["Commit", "Ref", "FileEntry", "Snapshot", "RefKind", "Operation"]


def test_repomap_hands_out_the_very_records_defined_in_the_data_layer() -> None:
    for name in RECORD_NAMES:
        assert getattr(repomap, name) is getattr(records, name), name


def test_the_records_import_nothing_from_the_package() -> None:
    tree = ast.parse(inspect.getsource(records))
    imported = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imported += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not [name for name in imported if name.split(".")[0] == "firstcommit"]
