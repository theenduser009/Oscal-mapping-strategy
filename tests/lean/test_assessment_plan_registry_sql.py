"""Test actual registry decision SQL locally, not Snowflake scripting or MERGE."""
import re
import sqlite3
import unittest
from lean_support import ROOT

MODEL = "SECURITY_ASSESSMENT_PLAN"


def registry_row(path="assessment-plan", **overrides):
    return {"OSCAL_MODEL_KEY": MODEL, "NODE_PATH": path, "IS_ACTIVE": True,
            "OPERATOR": None, "UUID_POLICY": None, "REQUIRED_MEMBERS": None,
            "INSTANCE_KEY_RULE": None, "ITEM_PATH": None, **overrides}


def canonical_rows():
    return [registry_row(OPERATOR="object", UUID_POLICY="node"),
            registry_row("assessment-plan.tasks[]", OPERATOR="record", UUID_POLICY="node",
                         INSTANCE_KEY_RULE="SOURCE_RECORD_ID"),
            registry_row("assessment-plan.tasks[].props[]", OPERATOR="properties", UUID_POLICY="omit",
                         INSTANCE_KEY_RULE="SOURCE_FIELD_NAME", ITEM_PATH="$")]


class AssessmentPlanRegistrySqlTests(unittest.TestCase):
    def setUp(self):
        sql = (ROOT / "sql/registry/ENABLE_ASSESSMENT_PLAN_METADATA.sql").read_text(encoding="utf-8")
        table = "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY"
        self.preflight = sql[sql.index("  WITH expected"):sql.index("  IF (COALESCE(conflicts")].strip().rstrip(";")
        self.duplicates = re.search(r"  SELECT COUNT\(\*\) INTO :conflicts FROM \(.*?\n  \);", sql, re.S)[0]
        self.retirement = re.search(r"  UPDATE " + re.escape(table) + r".*?;", sql, re.S)[0]
        for name in ("preflight", "duplicates", "retirement"):
            setattr(self, name, getattr(self, name).replace("SELECT * FROM VALUES", "VALUES")
                    .replace(" INTO :conflicts", "").replace(table, "registry"))
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.create_function("EQUAL_NULL", 2, lambda left, right: left == right)
        class CountIf:
            def __init__(self): self.count = 0
            def step(self, value): self.count += bool(value)
            def finalize(self): return self.count
        self.db.create_aggregate("COUNT_IF", 1, CountIf)
        self.columns = tuple(registry_row())
        self.db.execute("CREATE TABLE registry (" + ",".join(self.columns) + ")")

    def load(self, rows):
        self.db.execute("DELETE FROM registry")
        self.db.executemany("INSERT INTO registry VALUES (" + ",".join("?" for _ in self.columns) + ")",
                            [tuple(row[column] for column in self.columns) for row in rows])

    def test_actual_preflight_and_duplicate_predicates(self):
        cases = [
            ("empty", [], False),
            ("canonical", canonical_rows(), False),
            ("legacy unconfigured", [registry_row("security-assessment-plan"),
                                     registry_row("security-assessment-plan.tasks[]")], False),
            ("canonical unconfigured", [registry_row()], False),
            ("trimmed foreign owner", [registry_row(" assessment-plan ", OSCAL_MODEL_KEY="OTHER")], True),
            ("trimmed duplicate", [registry_row(), registry_row(" assessment-plan ")], True),
            ("conflicting identity without operator", [registry_row("assessment-plan.tasks[]", INSTANCE_KEY_RULE="VALUE")], True),
            ("conflicting item path without operator", [registry_row("assessment-plan.tasks[]", ITEM_PATH="$")], True),
            ("configured remarks", [registry_row("assessment-plan.tasks[].remarks", OPERATOR="object")], True),
            ("unknown active SAP path", [registry_row("assessment-plan.extra")], True),
            ("unknown inactive SAP path", [registry_row("assessment-plan.extra", IS_ACTIVE=False)], False),
            ("configured legacy path", [registry_row("security-assessment-plan.tasks[]", OPERATOR="record")], True),
            ("null active path", [registry_row(None)], True),
        ]
        for label, rows, blocked in cases:
            with self.subTest(case=label):
                self.load(rows)
                conflicts = self.db.execute(self.preflight).fetchone()[0] or 0
                duplicates = self.db.execute(self.duplicates).fetchone()[0]
                self.assertEqual(blocked, bool(conflicts or duplicates))

    def test_actual_retirement_preserves_canonical_and_other_owner_rows(self):
        legacy = [registry_row("security-assessment-plan"), registry_row("security-assessment-plan.tasks[]"),
                  registry_row(" assessment-plan.tasks[].remarks ")]
        other = [registry_row("security-assessment-plan.tasks[]", OSCAL_MODEL_KEY="OTHER"),
                 registry_row("unrelated", OSCAL_MODEL_KEY="OTHER")]
        self.load(legacy + canonical_rows() + other)
        self.db.execute(self.retirement)
        actual = set(self.db.execute("SELECT OSCAL_MODEL_KEY, NODE_PATH, IS_ACTIVE FROM registry"))
        expected = {(row["OSCAL_MODEL_KEY"], row["NODE_PATH"], False) for row in legacy}
        expected.update((row["OSCAL_MODEL_KEY"], row["NODE_PATH"], True) for row in canonical_rows() + other)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
