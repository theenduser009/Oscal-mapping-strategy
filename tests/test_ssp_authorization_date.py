import datetime
import json
import unittest

from test_ssp_mapping_dispatch_contracts import _load_cell_4, _mapping_row
import test_ssp_property_canonical_routing as routing


SC = "system-security-plan.system-characteristics"


def date_row(**changes):
    row = _mapping_row("ATOIATO_DATE", SC, "date-authorized", "Transform")
    row.update(NOTES="Convert timestamp to DateDatatype", STATUS="In Progress")
    row.update(changes)
    return row


class AuthorizationDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell = _load_cell_4()

    def transform(self, value):
        return self.cell["apply_mapping_transform"](date_row(), value, "private-record")

    def test_iso_timestamp_variants_emit_date_only(self):
        for value in (
            "2026-09-10T14:23:45Z", "2026-09-10 14:23:45",
            "2026-09-10T14:23:45.123456789+05:30",
            " 2026-09-10t14:23:45z ", "2026-09-10",
        ):
            with self.subTest(value=value):
                self.assertEqual(self.transform(value), "2026-09-10")

    def test_offset_is_not_converted_across_calendar_boundary(self):
        for value in ("2026-09-10T00:10:00+14:00", "2026-09-10T23:50:00-12:00"):
            self.assertEqual(self.transform(value), "2026-09-10")

    def test_typed_date_and_datetime(self):
        for value in (
            datetime.date(2024, 2, 29), datetime.datetime(2024, 2, 29, 23, 59),
            datetime.datetime(2024, 2, 29, 23, 59, tzinfo=datetime.timezone.utc),
        ):
            self.assertEqual(self.transform(value), "2024-02-29")

    def test_null_like_values_emit_nothing(self):
        for value in (None, "", [], {}):
            self.assertIs(self.transform(value), self.cell["SKIP_VALUE"])
            self.assertIs(self.cell["transform_authorization_date"](value), self.cell["SKIP_VALUE"])

    def test_invalid_or_ambiguous_values_fail_without_exposing_values(self):
        for value in (
            "2025-02-29", "2026-09-31T14:00:00", "2026-09-10T25:00:00Z",
            "2026-09-10T14:00:00+25:00", "2026-09-10T14:00:00Z-extra",
            "2026-09-10T14:23:45+00:60", "2026-09-10T14:23:45-01:99",
            "09/10/2026", "20260910", "2026-W37-4", "2026-09-10garbage",
            " ", "null", 1726000000, 1.25, True,
            {"Value": "private-date"}, ["private-date"],
        ):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaisesRegex(ValueError, "requires a valid ISO") as raised:
                    self.transform(value)
                self.assertNotIn("private-date", str(raised.exception))
                self.assertNotIn("private-record", str(raised.exception))

    def test_only_exact_approved_source_path_type_uses_date_handler(self):
        self.assertEqual(self.cell["_mapping_handler_for_row"](date_row()), "authorization-date")
        for changes in (
            {"SOURCE_FIELD_NAME": "OTHER_DATE"},
            {"OWNER_ELEMENT_PATH": "system-security-plan.metadata"},
            {"OSCAL_FIELD_NAME": "last-modified"},
            {"MAPPING_TYPE": "Direct"}, {"MAPPING_TYPE": "Extension Property"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, "Authorization date mapping contract"):
                    self.cell["_mapping_handler_for_row"](date_row(**changes))

    def test_parent_payload_gets_date_not_new_node_or_property(self):
        instances = self.cell["build_element_instances"](
            {"ATOIATO_DATE": "2026-09-10T23:50:00-12:00"}, "private-record",
            SC, [date_row(), date_row()])
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["instance_key"], "singleton")
        self.assertEqual(instances[0]["payload"], {"date-authorized": "2026-09-10"})

    def test_metadata_timestamps_remain_verbatim(self):
        value = "2026-09-10 14:23:45.123456"
        self.assertEqual(self.cell["transform_published"](value), value)
        self.assertEqual(self.cell["transform_last_modified"](value), value)

    def test_all_null_security_category_contract_still_fails_when_populated(self):
        row = _mapping_row("RECOMMENDED_SECURITY_CATEGORY", SC + ".security-impact-level",
                           "", "Extension Property")
        row.update(NOTES="All Nulls", OSCAL_FIELD_NAME=None)
        self.assertIs(self.cell["apply_mapping_transform"](row, None, "private-record"),
                      self.cell["SKIP_VALUE"])
        with self.assertRaisesRegex(ValueError, "source is not approved"):
            self.cell["apply_mapping_transform"](row, "Low", "private-record")

    @unittest.skipUnless(routing.pd is not None, "requires bundled pandas runtime")
    def test_actual_canonicalization_preserves_reported_notes_and_dispatches(self):
        fixture = routing.PropertyCanonicalRoutingTests()
        result = fixture.canonicalize([date_row()])
        row = result["CANONICAL_MAPPING_ROWS"][0]
        self.assertEqual(row["NOTES"], "Convert timestamp to DateDatatype")
        self.assertEqual(row["OWNER_ELEMENT_PATH"], SC)
        self.assertEqual(self.cell["apply_mapping_transform"](row, "2026-09-10 14:23:45", "r1"),
                         "2026-09-10")


if __name__ == "__main__":
    unittest.main()
