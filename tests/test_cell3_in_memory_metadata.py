"""Execute the complete Cell Three, including its notebook initialization tail."""
import contextlib
import copy
import io
import runpy
import unittest

import pandas as pd

import test_declarative_routing as base


class NoDatabaseSession:
    def __getattr__(self, name):
        raise AssertionError("Cell Three must not upload compiled metadata: " + name)


class CellThreeInMemoryMetadataTests(unittest.TestCase):
    def execute(self, rows, selected=("SSP", "ASSESSMENT_RESULTS")):
        inputs = {"source-one": rows}
        before = copy.deepcopy(inputs)
        with contextlib.redirect_stdout(io.StringIO()):
            result = runpy.run_path(str(base.CELL3), init_globals={
                "pd": pd, "session": NoDatabaseSession(),
                "CONFIG": {"OSCAL_MODEL": selected[0]},
                "ROUTING_METADATA": {},
                "MAPPING_INPUTS": inputs,
                "REGISTRY_INPUT_ROWS": base.registry(),
                "SOURCE_PROFILES": [base.profile(selected)],
                "MODEL_CONTRACTS": base.contracts(),
                "canonical_mapping_df": "stale dataframe from an earlier session run",
            })
        self.assertEqual(before, inputs)
        self.assertIsNone(result["canonical_mapping_df"])
        self.assertIsInstance(result["canonical_mapping_pdf"], pd.DataFrame)
        self.assertEqual(result["CANONICAL_MAPPING_ROWS"],
                         result["canonical_mapping_pdf"].to_dict("records"))
        return result

    def test_empty_metadata_objects_remain_dicts_in_every_route_without_upload(self):
        result = self.execute([
            base.mapping(),
            base.mapping(field="AR_FIELD", model="ASSESSMENT_RESULTS", root=base.AR),
        ])
        self.assertEqual(2, len(result["MAPPING_CONTEXTS"]))
        for context in result["MAPPING_CONTEXTS"]:
            self.assertEqual("READY", context["routing_report"]["STATUS"])
            row = context["compiled_plan"]["mappings"][0]
            for key in ("VALUE_CONSTRAINTS", "TRANSFORM_PARAMS", "REPRESENTATION_PARAMS"):
                self.assertEqual({}, row[key])
                self.assertIsInstance(row[key], dict)

    def test_nested_constraints_keep_false_zero_and_empty_parameters(self):
        constraints = {"required": False, "null_policy": "omit",
                       "cardinality": {"min": 0, "max": 1},
                       "validation": {"type": "number", "minimum": 0, "maximum": 100}}
        result = self.execute([
            base.mapping(TRANSFORM_ID="direct", VALUE_CONSTRAINTS=constraints),
        ], selected=("SSP",))
        row = result["CANONICAL_MAPPING_ROWS"][0]
        self.assertEqual(constraints, row["VALUE_CONSTRAINTS"])
        self.assertIs(row["VALUE_CONSTRAINTS"]["required"], False)
        self.assertIsInstance(row["VALUE_CONSTRAINTS"]["cardinality"]["min"], int)
        self.assertEqual({}, row["TRANSFORM_PARAMS"])

    def test_zero_selected_rows_do_not_require_dataframe_type_inference(self):
        result = self.execute([
            base.mapping(APPROVAL_STATUS=None, TRANSFORM_ID=None,
                         TRANSFORM_PARAMS=None, REPRESENTATION_PARAMS=None),
        ], selected=("SSP",))
        self.assertEqual([], result["CANONICAL_MAPPING_ROWS"])
        self.assertTrue(result["canonical_mapping_pdf"].empty)
        self.assertEqual(1, result["MAPPING_CONTEXTS"][0]["routing_report"]["DEFERRED_ROWS"])


if __name__ == "__main__":
    unittest.main()
