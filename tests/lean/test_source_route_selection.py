"""Cell 1 explicit source/model route selection; no database I/O."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CELL = ROOT / "notebooks" / "cells" / "01_initialization_and_configuration.py"


class NoDatabaseIO:
    def __getattr__(self, name):
        raise AssertionError("Cell 1 route selection must not perform database I/O")


def _namespace(source_keys, models):
    tree = ast.parse(CELL.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("snowflake"):
            continue
        if isinstance(node, ast.Import) and any(item.name.startswith("snowflake") for item in node.names):
            continue
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "SELECTED_SOURCE_KEYS" in names:
                node.value = ast.Name(id="_sources", ctx=ast.Load())
            if "SELECTED_MODELS" in names:
                node.value = ast.Name(id="_models", ctx=ast.Load())
        body.append(node)
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    ns = {
        "_sources": source_keys,
        "_models": models,
        "get_active_session": lambda: NoDatabaseIO(),
        "__file__": str(CELL),
    }
    exec(compile(module, str(CELL), "exec"), ns)
    return ns


class SourceRouteSelectionTests(unittest.TestCase):
    def test_source_one_assessment_results_isolated(self):
        ns = _namespace(("source-one",), ("ASSESSMENT_RESULTS",))
        self.assertEqual(
            [("source-one", ("ASSESSMENT_RESULTS",))],
            [(p["SOURCE_KEY"], p["MODEL_KEYS"]) for p in ns["SOURCE_PROFILES"]],
        )

    def test_source_two_assessment_results_isolated(self):
        ns = _namespace(("source-two-source",), ("ASSESSMENT_RESULTS",))
        self.assertEqual(
            [("source-two-source", ("ASSESSMENT_RESULTS",))],
            [(p["SOURCE_KEY"], p["MODEL_KEYS"]) for p in ns["SOURCE_PROFILES"]],
        )

    def test_invalid_source_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "configured sources"):
            _namespace(("missing-source",), ("ASSESSMENT_RESULTS",))

    def test_unbound_source_model_pair_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "no configured route"):
            _namespace(("source-one",), ("CATALOG",))


if __name__ == "__main__":
    unittest.main()
