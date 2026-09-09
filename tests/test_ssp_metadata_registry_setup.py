import ast
from pathlib import Path
import unittest


SETUP_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "setup"
    / "SETUP_SSP_METADATA_ROLE_PARTY_REGISTRY.py"
)


class MetadataRegistrySetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SETUP_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_element_type_is_a_required_registry_column(self):
        assignment = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "REQUIRED_REGISTRY_COLUMNS"
                for target in node.targets
            )
        )
        required_columns = ast.literal_eval(assignment.value)
        self.assertIn("ELEMENT_TYPE", required_columns)
        self.assertIn("IS_COLLECTION", required_columns)

    def test_collection_element_types_are_derived_from_node_paths(self):
        function = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_element_type"
        )
        namespace = {}
        exec(compile(ast.Module([function], []), str(SETUP_PATH), "exec"), namespace)
        self.assertEqual(
            namespace["_element_type"](
                "system-security-plan.metadata.roles[]"
            ),
            "roles",
        )
        self.assertEqual(
            namespace["_element_type"](
                "system-security-plan.metadata.parties[]"
            ),
            "parties",
        )

    def test_insert_only_merge_writes_element_type(self):
        self.assertIn(
            '"ELEMENT_TYPE": _element_type(path)',
            self.source,
        )
        self.assertIn('"IS_COLLECTION": True', self.source)
        self.assertIn(
            "    ELEMENT_TYPE,\n    IS_COLLECTION,\n    PROCESS_ORDER,",
            self.source,
        )
        self.assertIn(
            "    source.ELEMENT_TYPE,\n    source.IS_COLLECTION,\n"
            "    source.PROCESS_ORDER,",
            self.source,
        )

    def test_unknown_required_columns_fail_before_model_read(self):
        entrypoint = self.source.index(
            "_assert_safe_identifier(REGISTRY_TABLE)"
        )
        schema_guard = self.source.index(
            "_assert_supported_not_null_columns()",
            entrypoint,
        )
        first_model_read = self.source.index(
            "current_model_rows = _read_model_rows()",
            entrypoint,
        )
        self.assertLess(schema_guard, first_model_read)
        self.assertIn(
            "Registry has unsupported required insert columns:",
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
