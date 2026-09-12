"""One-time registry migration contract tests; synthetic/static, never Snowflake.

These checks prove seed semantics and guarded scope, not live SQL acceptance.
The frozen structural settings remain an independent pre-migration oracle.
"""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql"
ORACLE_PATH = ROOT / "tests/fixtures/mapper_contract_pre_registry.json"
TABLE = "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY"
OLD = ("OSCAL_MODEL_KEY", "NODE_PATH", "ELEMENT_TYPE", "PARENT_NODE_PATH",
       "IS_COLLECTION", "INSTANCE_KEY_RULE", "PROCESS_ORDER", "IS_ACTIVE", "ITEM_PATH")
NEW = ("OPERATOR", "UUID_POLICY", "REQUIRED_MEMBERS")
LEGACY_EXTRA = (
    "MAPPER_METADATA_VERSION", "MAPPER_ENABLED", "PARENT_INSTANCE_RULE",
    "EMPTY_POLICY", "LIST_INSTANCE_RULE", "PROPERTY_NAME_RULE", "ASSEMBLY_POLICY",
    "DEFAULT_SINGLETON_POLICY", "REQUIRED_RULE_IDS", "ROLES_PATH", "PARTIES_PATH",
    "PARTY_TYPE", "PARTY_UUID_PARTS", "PARTY_UUID_SOURCE_KEY", "REPORT_TARGET_PATH",
)


def read_seed(sql):
    section = sql.split("-- BEGIN EXPLICIT SEED:", 1)[1].split("-- END EXPLICIT SEED", 1)[0]
    pattern = (r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*"
               r"'([^']+)'\s*,\s*(NULL|'(?:''|[^'])*')\s*,\s*'([^']+)'\s*\)")
    result = {}
    for model, path, operator, uuid_policy, members, expected in re.findall(pattern, section):
        result[model, path] = ({
            "OPERATOR": operator,
            "UUID_POLICY": uuid_policy,
            "REQUIRED_MEMBERS": None if members == "NULL" else members[1:-1].replace("''", "'"),
        }, json.loads(expected))
    return result


def synthetic_registry(oracle):
    rows = []
    collection_identity = {
        "system-security-plan.metadata.roles[]": ("SOURCE_FIELD_NAME", "$"),
        "system-security-plan.metadata.parties[]": ("ID", "UserList[]"),
        "system-security-plan.metadata.responsible-parties[]": ("SOURCE_FIELD_NAME+ID", "UserList[]"),
        "system-security-plan.metadata.document-ids[]": ("VALUE", "$"),
    }
    for model, contract in oracle["MODELS"].items():
        paths = set(contract["ELEMENTS"])
        for path in tuple(paths):
            while "." in path:
                path = path.rsplit(".", 1)[0]
                paths.add(path)
        # Realistic unselected collection + nested singleton + ordinary singleton.
        paths.update({contract["ROOT_PATH"] + ".unapproved[]",
                      contract["ROOT_PATH"] + ".unapproved[].child",
                      contract["ROOT_PATH"] + ".unmapped-singleton"})
        for path in sorted(paths):
            expected = dict(contract["ELEMENTS"].get(path, {}).get("parameters", {}).get("registry_contract", {}))
            if path in collection_identity:
                expected["instance_key_rule"], expected["item_path"] = collection_identity[path]
            elif path.endswith("[]"):
                # Synthetic out-of-scope rows still satisfy the original registry's
                # structural rule that every active collection has stable identity.
                expected.setdefault("instance_key_rule", "VALUE")
                expected.setdefault("item_path", "$")
            rows.append({
                "OSCAL_MODEL_KEY": model, "NODE_PATH": path,
                "PARENT_NODE_PATH": expected.get("parent_path", path.rsplit(".", 1)[0] if "." in path else None),
                "ELEMENT_TYPE": path.rsplit(".", 1)[-1].replace("[]", ""),
                "IS_COLLECTION": expected.get("is_collection", path.endswith("[]")),
                "INSTANCE_KEY_RULE": expected.get("instance_key_rule"),
                "ITEM_PATH": expected.get("item_path"), "PROCESS_ORDER": path.count(".") + 1,
                "IS_ACTIVE": True,
            })
    rows.append(dict(zip(OLD, ("OTHER", "other", "other", None, False, None, 1, True, None))))
    return rows


def expected_metadata(row, seed):
    key = row["OSCAL_MODEL_KEY"], row["NODE_PATH"]
    if key in seed:
        return copy.deepcopy(seed[key][0])
    meta = dict.fromkeys(NEW)
    if key[0] == "SSP" and not row["IS_COLLECTION"] and "[]" not in key[1]:
        meta.update(OPERATOR="object", UUID_POLICY="omit")
    return meta


def simulate_guarded_update(rows, seed):
    """Independent reference model of the SQL's scope/conflict/rerun contract."""
    changed = copy.deepcopy(rows)
    for row in rows:
        if row["OSCAL_MODEL_KEY"] in {"SSP", "ASSESSMENT_RESULTS"} and row["IS_ACTIVE"]:
            if not isinstance(row["NODE_PATH"], str) or not row["NODE_PATH"].strip():
                raise ValueError("blank active path")
    keys = [(r["OSCAL_MODEL_KEY"], r["NODE_PATH"]) for r in rows
            if r["OSCAL_MODEL_KEY"] in {"SSP", "ASSESSMENT_RESULTS"}]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate path")
    active = {(r["OSCAL_MODEL_KEY"], r["NODE_PATH"]): r for r in rows if r["IS_ACTIVE"]}
    for key, (_, expected) in seed.items():
        if key not in active:
            raise ValueError("missing path")
        actual = active[key]
        columns = {"parent_path": "PARENT_NODE_PATH", "is_collection": "IS_COLLECTION",
                   "instance_key_rule": "INSTANCE_KEY_RULE", "item_path": "ITEM_PATH"}
        if any(actual[columns[name]] != value for name, value in expected.items()):
            raise ValueError("identity conflict")
    changes = 0
    for (model, path), row in active.items():
        if model not in {"SSP", "ASSESSMENT_RESULTS"} or expected_metadata(row, seed)["OPERATOR"] is None:
            continue
        root = "system-security-plan" if model == "SSP" else "assessment-results"
        parent = (row.get("PARENT_NODE_PATH") or "").strip() or None
        if row["IS_COLLECTION"] != path.endswith("[]"):
            raise ValueError("collection path conflict")
        if path != root and not path.startswith(root + "."):
            raise ValueError("root path conflict")
        if path == root:
            if parent is not None:
                raise ValueError("root parent conflict")
        elif (parent is None or (model, parent) not in active
              or expected_metadata(active[model, parent], seed)["OPERATOR"] is None
              or not path.startswith(parent + ".")):
            raise ValueError("parent path conflict")
    for row in changed:
        if row["OSCAL_MODEL_KEY"] not in {"SSP", "ASSESSMENT_RESULTS"} or not row["IS_ACTIVE"]:
            continue
        expected = expected_metadata(row, seed)
        if any(row.get(k) is not None and row[k] != value for k, value in expected.items()):
            raise ValueError("metadata conflict")
        if any(row.get(k) != value for k, value in expected.items()):
            changes += 1
            row.update(expected)
    return changed, changes


class RegistryMetadataMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.seed = read_seed(cls.sql)
        cls.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))

    def test_seed_exactly_preserves_fifteen_explicit_accepted_elements(self):
        expected = {(model, path) for model, contract in self.oracle["MODELS"].items()
                    for path in contract["ELEMENTS"]}
        self.assertEqual(len(self.seed), 15)
        self.assertEqual(set(self.seed), expected)
        for (model, path), (meta, _) in self.seed.items():
            with self.subTest(model=model, path=path):
                element = self.oracle["MODELS"][model]["ELEMENTS"][path]
                p = element.get("parameters", {})
                self.assertEqual(set(meta), set(NEW))
                self.assertEqual(meta["OPERATOR"], element["operator"])
                self.assertEqual(meta["UUID_POLICY"], "instance" if p.get("uuid_from_instance")
                                 else "node" if p.get("include_uuid") else "omit")
                self.assertEqual(meta["REQUIRED_MEMBERS"], "|".join(p["required_members"]) if p.get("required_members") else None)

    def test_original_registry_contract_checks_are_not_changed(self):
        for (model, path), (_, expected) in self.seed.items():
            old = self.oracle["MODELS"][model]["ELEMENTS"][path].get("parameters", {}).get("registry_contract", {})
            for name, value in old.items():
                self.assertEqual(expected[name], value, (model, path, name))
            self.assertEqual(expected["parent_path"], path.rsplit(".", 1)[0] if "." in path else None)
            self.assertEqual(expected["is_collection"], path.endswith("[]"))

    def test_actual_mapping_csv_compiles_against_sql_seed_metadata(self):
        import test_registry_release as release
        registry, _ = simulate_guarded_update(synthetic_registry(self.oracle), self.seed)
        harness = release.RegistryReleaseTests()
        harness.setUp()
        contexts = harness.compile(registry=registry)
        self.assertEqual({"SSP": 47, "ASSESSMENT_RESULTS": 17},
                         {ctx["config"]["OSCAL_MODEL"]: len(ctx["mapping_rows"]) for ctx in contexts})
        for context in contexts:
            self.assertEqual(context["routing_report"]["STATUS"], "READY", context["routing_report"])

    def test_only_three_non_derivable_runtime_fields_are_seeded(self):
        self.assertEqual(set(NEW), {"OPERATOR", "UUID_POLICY", "REQUIRED_MEMBERS"})
        for column in LEGACY_EXTRA:
            with self.subTest(legacy_column=column):
                self.assertNotIn('"' + column + '"', self.sql)
        self.assertIn("d.x:META:OPERATOR::VARCHAR IS NOT NULL", self.sql)
        members = self.seed[
            "SSP", "system-security-plan.system-characteristics.security-impact-level"
        ][0]["REQUIRED_MEMBERS"]
        self.assertEqual(members.split("|"), [
            "security-objective-confidentiality",
            "security-objective-integrity",
            "security-objective-availability",
        ])

    def test_party_identity_is_preserved_by_original_registry_contract(self):
        group = self.oracle["MODELS"]["SSP"]["REFERENCE_GROUPS"][0]
        roles = self.seed["SSP", group["roles_path"]]
        parties = self.seed["SSP", group["parties_path"]]
        assignments = self.seed["SSP", group["assignments_path"]]
        self.assertEqual(roles[0]["OPERATOR"], "roles")
        self.assertEqual(parties[0]["OPERATOR"], "parties")
        self.assertEqual(assignments[0]["OPERATOR"], "assignments")
        self.assertEqual(parties[1]["instance_key_rule"], "ID")
        self.assertEqual(assignments[1]["instance_key_rule"], "SOURCE_FIELD_NAME+ID")
        self.assertEqual(parties[1]["item_path"], "UserList[]")
        self.assertEqual(assignments[1]["item_path"], "UserList[]")

    def test_synthetic_activation_matches_old_default_and_ar_whitelist(self):
        rows = synthetic_registry(self.oracle)
        updated, count = simulate_guarded_update(rows, self.seed)
        self.assertGreater(count, 15)
        ar_enabled = {r["NODE_PATH"] for r in updated
                      if r["OSCAL_MODEL_KEY"] == "ASSESSMENT_RESULTS" and r.get("OPERATOR")}
        self.assertEqual(ar_enabled, set(self.oracle["MODELS"]["ASSESSMENT_RESULTS"]["ELEMENT_PATHS"]))
        for row in updated:
            path = row["NODE_PATH"]
            if "unapproved" in path:
                self.assertIsNone(row.get("OPERATOR"))
            if path == "system-security-plan.unmapped-singleton":
                self.assertEqual(row["OPERATOR"], "object")
                self.assertEqual(row["UUID_POLICY"], "omit")
        self.assertIn("AND POSITION('[]' IN r.NODE_PATH)=0", self.sql)
        self.assertIn("AND NOT r.IS_COLLECTION", self.sql)

    def test_exact_rerun_has_zero_updates_and_preserves_originals_other_models(self):
        rows = synthetic_registry(self.oracle)
        original = copy.deepcopy(rows)
        once, first_count = simulate_guarded_update(rows, self.seed)
        twice, second_count = simulate_guarded_update(once, self.seed)
        self.assertGreater(first_count, 0)
        self.assertEqual(second_count, 0)
        self.assertEqual(twice, once)
        self.assertEqual([{k: r[k] for k in OLD} for r in twice], original)
        self.assertEqual(twice[-1], original[-1])

    def test_conflicting_existing_metadata_fails_without_mutation(self):
        rows = synthetic_registry(self.oracle)
        rows[0]["OPERATOR"] = "not-an-approved-operator"
        before = copy.deepcopy(rows)
        with self.assertRaisesRegex(ValueError, "metadata conflict"):
            simulate_guarded_update(rows, self.seed)
        self.assertEqual(rows, before)
        self.assertIn("NOT COALESCE(IS_NULL_VALUE(GET(r.present,k.key)),TRUE)", self.sql)
        self.assertIn("GET(r.present,k.key) IS DISTINCT FROM k.value", self.sql)

    def test_missing_duplicate_inactive_and_changed_identity_fail_closed(self):
        original = synthetic_registry(self.oracle)
        target = next(r for r in original if r["NODE_PATH"] == "assessment-results.results[]")
        for kind in ("missing", "duplicate", "inactive", "identity"):
            with self.subTest(kind=kind):
                rows = copy.deepcopy(original)
                index = next(i for i, r in enumerate(rows) if r == target)
                if kind == "missing":
                    rows.pop(index)
                elif kind == "duplicate":
                    rows.append(copy.deepcopy(rows[index]))
                elif kind == "inactive":
                    rows[index]["IS_ACTIVE"] = False
                else:
                    rows[index]["INSTANCE_KEY_RULE"] = "SOURCE_FIELD_NAME"
                before = copy.deepcopy(rows)
                with self.assertRaises(ValueError):
                    simulate_guarded_update(rows, self.seed)
                self.assertEqual(rows, before)

    def test_only_new_columns_are_updated_and_only_fixed_registry_is_targeted(self):
        # Unescape dynamic SQL literals before examining UPDATE's SET assignments.
        update = re.search(r"update_sql VARCHAR DEFAULT '((?:''|[^'])*)';", self.sql).group(1).replace("''", "'")
        assigned = re.findall(r'"([A-Z_]+)"\s*=', update.split("FROM ", 1)[0])
        self.assertEqual(set(assigned), set(NEW))
        self.assertFalse(set(assigned) & set(OLD))
        self.assertTrue(update.startswith("UPDATE " + TABLE + " SET"))
        self.assertIn("AND IS_ACTIVE", update)
        self.assertIn("IS DISTINCT FROM", update)
        for column in NEW:
            self.assertIn('("' + column + '" IS NULL OR "' + column + '" IS NOT DISTINCT FROM', update)
        executable = "\n".join(line for line in self.sql.splitlines() if not line.lstrip().startswith("--"))
        self.assertNotRegex(executable, r"(?i)\b(?:DELETE|TRUNCATE|INSERT|MERGE|CREATE|DROP)\s+")
        self.assertNotRegex(executable, r"(?i)\b(?:DIM_OSCAL|FACT_OSCAL|RTX_ENTERPRISESERVICES)")

    def test_nullable_seed_values_are_written_as_sql_null_not_text_null(self):
        update = re.search(r"update_sql VARCHAR DEFAULT '((?:''|[^'])*)';", self.sql).group(1).replace("''", "'")
        for column in NEW:
            with self.subTest(column=column):
                self.assertIn("IFF(IS_NULL_VALUE(d.meta:" + column + "),NULL,d.meta:" + column, update)

    def test_schema_active_transaction_and_conflicts_precede_ddl(self):
        self.assertNotRegex(self.sql, r"(?i)\bFOR\s+ROW\s+IN\b")
        ddl = self.sql.index("  -- DDL PHASE:")
        self.assertLess(self.sql.index("SELECT CURRENT_TRANSACTION()"), ddl)
        self.assertLess(self.sql.index("IF (tx IS NOT NULL) THEN RAISE already_active"), ddl)
        self.assertLess(self.sql.index("IF (n<>0) THEN RAISE schema_error"), ddl)
        self.assertLess(self.sql.index("IF (n<>0) THEN RAISE path_error"), ddl)
        self.assertLess(self.sql.index("IF (n<>0) THEN RAISE metadata_conflict"), ddl)
        self.assertIn("ADD COLUMN IF NOT EXISTS", self.sql)
        self.assertIn("IS_NULLABLE<>'YES'", self.sql)


    def test_sql_seed_decodes_through_actual_registry_compiler(self):
        import test_metadata_driven_contract as metadata
        import test_registry_release as release
        ns = metadata.namespace()
        registry, _ = simulate_guarded_update(synthetic_registry(self.oracle), self.seed)
        models = copy.deepcopy(self.oracle["MODELS"])
        for contract in models.values():
            for key in ("ROOT_PATH", "ELEMENTS", "ELEMENT_PATHS", "REFERENCE_GROUPS",
                        "DEFAULT_ELEMENT", "REQUIRED_RULE_IDS"):
                contract.pop(key, None)
            contract.get("REPORT", {}).pop("TARGET_PATH", None)
            contract["REGISTRY_METADATA_VERSION"] = 1
        profiles = copy.deepcopy(self.oracle["SOURCES"])
        for profile in profiles:
            profile["MODEL_KEYS"] = tuple(profile["MODEL_BINDINGS"])
        before = copy.deepcopy(registry)
        decoded = ns["decode_registry_model_contracts"](
            registry, profiles, models, {"source-one": release.mapping_rows()})
        self.assertEqual(registry, before)
        self.assertEqual(set(decoded["ASSESSMENT_RESULTS"]["ELEMENTS"]),
                         set(self.oracle["MODELS"]["ASSESSMENT_RESULTS"]["ELEMENT_PATHS"]))
        for model, old in self.oracle["MODELS"].items():
            self.assertEqual(decoded[model]["ROOT_PATH"], old["ROOT_PATH"])
            for path, element in old["ELEMENTS"].items():
                with self.subTest(model=model, path=path):
                    actual = decoded[model]["ELEMENTS"][path]
                    self.assertEqual(actual["operator"], element["operator"])
                    for key, value in element.get("parameters", {}).items():
                        if key in {"controlled_fields", "registry_contract"}:
                            continue  # Required support rows replace controlled fields; old keys are preflighted.
                        self.assertEqual(actual["parameters"][key], value)
        self.assertEqual(decoded["SSP"]["REFERENCE_GROUPS"],
                         self.oracle["MODELS"]["SSP"]["REFERENCE_GROUPS"])
        self.assertNotIn("REQUIRED_RULE_IDS", decoded["SSP"])
        self.assertNotIn("REQUIRED_RULE_IDS", decoded["ASSESSMENT_RESULTS"])

    def test_update_transaction_contains_no_ddl_and_rechecks_baseline(self):
        phase = self.sql.split("  BEGIN TRANSACTION;", 1)[1].split("  COMMIT;", 1)[0]
        self.assertNotRegex(phase, r"(?i)\b(?:ALTER|CREATE|DROP)\s+")
        self.assertEqual(phase.count("EXECUTE IMMEDIATE :baseline_sql USING (baseline_json)"), 2)
        self.assertLess(phase.index("EXECUTE IMMEDIATE :conflict_sql"),
                        phase.index("EXECUTE IMMEDIATE :update_sql"))
        self.assertIn("EXECUTE IMMEDIATE :verify_sql USING (desired_json)", phase)
        self.assertIn("IF (commit_attempted) THEN RAISE commit_unknown", self.sql)
        self.assertIn("EXCEPTION WHEN OTHER THEN RAISE rollback_unknown", self.sql)
        self.assertIn("DDL_ROLLBACK_AVAILABLE',FALSE", self.sql)
        self.assertIn("added columns cannot be rolled back", self.sql)

    def test_null_and_blank_active_paths_fail_before_ddl_without_mutation(self):
        preddl = self.sql.split("  -- DDL PHASE:", 1)[0]
        self.assertIn("AND NULLIF(TRIM(NODE_PATH),'') IS NULL", preddl)
        for model in ("SSP", "ASSESSMENT_RESULTS"):
            for value in (None, "", "   "):
                with self.subTest(model=model, value=value):
                    rows = synthetic_registry(self.oracle)
                    extra = copy.deepcopy(next(row for row in rows if row["OSCAL_MODEL_KEY"] == model))
                    extra.update(NODE_PATH=value)
                    rows.append(extra)
                    before = copy.deepcopy(rows)
                    with self.assertRaisesRegex(ValueError, "blank active path"):
                        simulate_guarded_update(rows, self.seed)
                    self.assertEqual(rows, before)

    def test_unseeded_self_nonancestor_and_missing_parent_fail_before_ddl(self):
        preddl = " ".join(self.sql.split("  -- DDL PHASE:", 1)[0].split())
        self.assertIn("STARTSWITH(d.x:PATH::VARCHAR, NULLIF(TRIM(r.PARENT_NODE_PATH),'') || '.')", preddl)
        path = "system-security-plan.system-implementation"
        self.assertNotIn(("SSP", path), self.seed)
        for parent in (path, "system-security-plan.metadata", None, "system-security-plan.missing"):
            with self.subTest(parent=parent):
                rows = synthetic_registry(self.oracle)
                next(row for row in rows if row["NODE_PATH"] == path)["PARENT_NODE_PATH"] = parent
                before = copy.deepcopy(rows)
                with self.assertRaisesRegex(ValueError, "parent path conflict"):
                    simulate_guarded_update(rows, self.seed)
                self.assertEqual(rows, before)

    def test_malformed_roots_and_cross_model_root_are_rejected(self):
        preddl = " ".join(self.sql.split("  -- DDL PHASE:", 1)[0].split())
        self.assertIn("IFF(value:MODEL::VARCHAR='SSP','system-security-plan','assessment-results') root_path", preddl)
        self.assertIn("d.x:PATH::VARCHAR IS DISTINCT FROM d.root_path", preddl)
        self.assertIn("STARTSWITH(d.x:PATH::VARCHAR,d.root_path || '.')", preddl)
        for model in ("SSP", "ASSESSMENT_RESULTS"):
            root = self.oracle["MODELS"][model]["ROOT_PATH"]
            for column, value in (("PARENT_NODE_PATH", root), ("IS_COLLECTION", True)):
                with self.subTest(model=model, column=column):
                    rows = synthetic_registry(self.oracle)
                    next(row for row in rows if row["NODE_PATH"] == root)[column] = value
                    with self.assertRaisesRegex(ValueError, "identity conflict"):
                        simulate_guarded_update(rows, self.seed)
        rows = synthetic_registry(self.oracle)
        extra = copy.deepcopy(next(row for row in rows if row["NODE_PATH"] == "system-security-plan"))
        extra["NODE_PATH"] = "assessment-results"
        rows.append(extra)
        with self.assertRaisesRegex(ValueError, "root path conflict"):
            simulate_guarded_update(rows, self.seed)

    def test_update_result_count_is_validated_before_verification_and_commit(self):
        # Source-contract plus scalar simulation: never executes an UPDATE.
        phase = self.sql.split("  BEGIN TRANSACTION;", 1)[1].split("  COMMIT;", 1)[0]
        compact = " ".join(phase.split())
        self.assertIn("result_rows := (EXECUTE IMMEDIATE :update_sql USING (desired_json));", phase)
        self.assertIn('changed_rows := migration_row."number of rows updated";', phase)
        self.assertNotIn("changed_rows := SQLROWCOUNT", phase)
        self.assertIn("n := 0; changed_rows := NULL; FOR migration_row IN result_rows DO n := n + 1;", compact)
        guard = "IF (n<>1 OR changed_rows IS NULL OR changed_rows<0 OR changed_rows>ARRAY_SIZE(desired)) THEN RAISE verification_error; END IF;"
        self.assertIn(guard, compact)
        self.assertLess(compact.index(guard), compact.index("EXECUTE IMMEDIATE :verify_sql"))
        for result, rejected in (([], True), ([None], True), ([-1], True), ([23], True),
                                 ([0], False), ([22], False), ([1, 1], True)):
            with self.subTest(result=result):
                n, changed_rows = len(result), result[-1] if result else None
                self.assertEqual(rejected, n != 1 or changed_rows is None
                                 or changed_rows < 0 or changed_rows > 22)


if __name__ == "__main__":
    unittest.main()

