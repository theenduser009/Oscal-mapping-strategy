"""Static/source-contract and JSON transport regressions, not Snowflake execution.

The prior Python simulation bypassed dynamic SQL bind types. These tests model
only that boundary; they do not establish live Snowflake Scripting acceptance.
"""
import json
from pathlib import Path
import re
import unittest


SQL_PATH = Path(__file__).resolve().parents[1] / "sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql"
TEMPLATES = {"conflict_sql", "baseline_sql", "update_sql", "verify_sql"}
DECODED_INPUT = r"FLATTEN\s*\(\s*INPUT\s*=>\s*PARSE_JSON\s*\(\s*\?\s*\)\s*\)"


def dynamic_templates(sql):
    pattern = r"\b(\w+_sql)\s+VARCHAR\s+DEFAULT\s+'((?:[^']|'')*)'\s*;"
    return {name: value.replace("''", "'")
            for name, value in re.findall(pattern, sql, re.I)}


def simulate_flatten_binding(template, bound_text):
    """Model the reported VARCHAR-vs-array boundary, not SQL execution."""
    if not isinstance(bound_text, str):
        raise TypeError("simulation requires the actual string transport type")
    value = (json.loads(bound_text) if re.search(DECODED_INPUT, template, re.I)
             else bound_text)
    if not isinstance(value, list):
        raise TypeError("FLATTEN input in this array fixture is not an array")
    return value


class RegistryMetadataBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.templates = dynamic_templates(cls.sql)
        cls.body = cls.sql.split("\nBEGIN\n", 1)[1]

    def test_all_four_dynamic_inputs_explicitly_parse_one_placeholder(self):
        self.assertEqual(set(self.templates), TEMPLATES)
        for name, template in self.templates.items():
            with self.subTest(template=name):
                self.assertEqual(template.count("?"), 1)
                self.assertEqual(len(re.findall(DECODED_INPUT, template, re.I)), 1)
                self.assertNotRegex(template, r"FLATTEN\s*\(\s*INPUT\s*=>\s*\?")

    def test_all_six_calls_bind_corresponding_serialized_variable(self):
        calls = re.findall(
            r"EXECUTE\s+IMMEDIATE\s+:(\w+_sql)\s+USING\s*\(\s*(\w+)\s*\)",
            self.body, re.I)
        self.assertEqual(calls, [
            ("conflict_sql", "desired_json"), ("baseline_sql", "baseline_json"),
            ("conflict_sql", "desired_json"), ("update_sql", "desired_json"),
            ("verify_sql", "desired_json"), ("baseline_sql", "baseline_json"),
        ])
        self.assertNotRegex(self.body, r"USING\s*\(\s*(?:desired|baseline)\s*\)")

    def test_serialize_once_after_snapshots_before_first_preflight(self):
        first_query = self.body.index("EXECUTE IMMEDIATE :conflict_sql")
        baseline_end = self.body.index(";", self.body.index("INTO :baseline"))
        desired_end = self.body.index(";", self.body.index("INTO :desired"))
        for array in ("desired", "baseline"):
            with self.subTest(array=array):
                self.assertRegex(self.sql, rf"\b{array}_json\s+VARCHAR\s*;")
                pattern = (rf"\b{array}_json\s*:=\s*TO_JSON\s*\(\s*"
                           rf"TO_VARIANT\s*\(\s*{array}\s*\)\s*\)\s*;")
                matches = list(re.finditer(pattern, self.body, re.I))
                self.assertEqual(len(matches), 1)
                self.assertGreater(matches[0].start(), max(baseline_end, desired_end))
                self.assertLess(matches[0].end(), first_query)
                self.assertEqual(len(re.findall(rf"\b{array}_json\s*:=", self.body)), 1)

    def test_static_queries_and_array_size_keep_native_arrays(self):
        for array, expected_count in (("column_specs", 3), ("seed", 2), ("desired", 2)):
            with self.subTest(array=array):
                self.assertRegex(self.sql, rf"\b{array}\s+ARRAY\b")
                self.assertEqual(len(re.findall(
                    rf"FLATTEN\s*\(\s*INPUT\s*=>\s*:{array}\s*\)",
                    self.body, re.I)), expected_count)
        self.assertRegex(self.sql, r"\bbaseline\s+ARRAY\s*;")
        self.assertEqual(len(re.findall(r"ARRAY_SIZE\(desired\)", self.body)), 2)
        self.assertNotRegex(self.body, r"ARRAY_SIZE\(\w+_json\)")
        self.assertNotRegex(self.body, r"\b(?:desired|baseline)\s*:=\s*TO_(?:JSON|VARCHAR)")

    def test_first_conflict_failure_precedes_schema_and_update_effects(self):
        first_query = self.body.index("EXECUTE IMMEDIATE :conflict_sql")
        conflict_guard = self.body.index("RAISE metadata_conflict", first_query)
        ddl = self.body.index("EXECUTE IMMEDIATE :statement")
        begin = self.body.index("BEGIN TRANSACTION")
        update = self.body.index("EXECUTE IMMEDIATE :update_sql")
        self.assertLess(first_query, conflict_guard)
        self.assertLess(conflict_guard, ddl)
        self.assertLess(ddl, begin)
        self.assertLess(begin, update)
        self.assertNotRegex(self.body[:first_query], r"EXECUTE\s+IMMEDIATE")
        self.assertNotRegex(self.body[:first_query], r"(?mi)^\s*(?:ALTER|UPDATE|INSERT|DELETE|TRUNCATE)\s")

    def test_reported_string_boundary_fails_without_parse_json(self):
        wire = json.dumps([{"META": {"MAPPER_ENABLED": True}}])
        with self.assertRaisesRegex(TypeError, "not an array"):
            simulate_flatten_binding("SELECT * FROM TABLE(FLATTEN(INPUT=>?))", wire)
        for name, template in self.templates.items():
            with self.subTest(template=name):
                self.assertEqual(simulate_flatten_binding(template, wire), json.loads(wire))

    def test_json_transport_preserves_null_boolean_number_and_nested_list(self):
        fixture = [{"MODEL": "synthetic", "PATH": "root.collection[]", "META": {
            "NULL_VALUE": None, "ENABLED": True, "DISABLED": False,
            "ZERO": 0, "VERSION": 1, "NUMBER": 1.25,
            "TEXT": "quote '\" and slash \\ and newline\n",
            "RULES": "first|second", "LIST": [None, False, 0, {"name": "value"}],
        }}]
        wire = json.dumps(fixture, ensure_ascii=False, allow_nan=False)
        for name, template in self.templates.items():
            with self.subTest(template=name):
                restored = simulate_flatten_binding(template, wire)
                self.assertEqual(restored, fixture)
                meta = restored[0]["META"]
                self.assertIsNone(meta["NULL_VALUE"])
                self.assertIs(meta["ENABLED"], True)
                self.assertIs(meta["DISABLED"], False)
                self.assertIs(type(meta["ZERO"]), int)
                self.assertIs(type(meta["NUMBER"]), float)
                self.assertIs(type(meta["LIST"]), list)

    def test_json_transport_preserves_empty_array_and_duplicate_baseline_rows(self):
        duplicate = {"NODE_PATH": "synthetic.root", "ITEM_PATH": None, "PROCESS_ORDER": 0}
        for fixture in ([], [duplicate, duplicate]):
            with self.subTest(rows=len(fixture)):
                restored = simulate_flatten_binding(self.templates["baseline_sql"], json.dumps(fixture))
                self.assertEqual(restored, fixture)
                self.assertEqual(len(restored), len(fixture))


if __name__ == "__main__":
    unittest.main()
