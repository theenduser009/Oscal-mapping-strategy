# Read-only SSP metadata.last-modified source and output audit
#
# Run this once after Mapper Cells 1 through 7 in the same Snowflake notebook
# session. It examines the two spreadsheet-defined source candidates that
# converge on system-security-plan.metadata.last-modified. It reports only
# aggregate counts; it never prints timestamps, payloads, source record IDs,
# or other source values, and it creates no database objects or writes.
#
# Candidate A: ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED
# Candidate B: LAST_UPDATED
#
# Candidate labels are stable diagnostic labels only. Their order is not an
# approved precedence rule. Naive timestamps are never assigned the notebook,
# server, or local-machine timezone.

from collections import Counter
import datetime
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TARGET_OWNER_PATH = "system-security-plan.metadata"
TARGET_FIELD_NAME = "last-modified"
TARGET_OSCAL_PATH = TARGET_OWNER_PATH + "." + TARGET_FIELD_NAME
EXPECTED_OSCAL_VERSION = "1.2.3"
EXPECTED_LOADED_ARTIFACT_ROWS = 608

CANDIDATE_SOURCE_FIELDS = (
    "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED",
    "LAST_UPDATED",
)
CANDIDATE_LABELS = ("CANDIDATE_A", "CANDIDATE_B")

required_objects = {
    "CONFIG": globals().get("CONFIG"),
    "source_df": globals().get("source_df"),
    "mapping_df": globals().get("mapping_df"),
    "mapping_artifact_pdf": globals().get("mapping_artifact_pdf"),
    "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "run_result": globals().get("run_result"),
    "_parse_source_json": globals().get("_parse_source_json"),
    "resolve_json_path": globals().get("resolve_json_path"),
    "_target_field_name": globals().get("_target_field_name"),
    "col": globals().get("col"),
    "lit": globals().get("lit"),
}
missing_objects = [
    name for name, value in required_objects.items() if value is None
]
if missing_objects:
    raise RuntimeError(
        "Run Mapper Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_objects)
    )
if str(CONFIG.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
    raise RuntimeError("This audit requires CONFIG['OSCAL_MODEL'] = 'SSP'.")
if str(CONFIG.get("OSCAL_VERSION", "")).strip() != EXPECTED_OSCAL_VERSION:
    raise RuntimeError(
        "This repository checkpoint requires OSCAL version "
        + EXPECTED_OSCAL_VERSION
        + "."
    )
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError("Set EXECUTE_WRITES = False before running this audit.")
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
if not run_result.get("pre_write_validation_passed", False):
    raise RuntimeError("Cell 7 pre-write validation must pass first.")
if run_result.get("writes_executed", True):
    raise RuntimeError("This audit requires a read-only Cell 7 run.")


_RFC3339_AWARE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_UTC_Z_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)
_DATE_ONLY_PATTERN = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}|\d{8}|\d{4}-W\d{2}-\d|"
    r"\d{1,2}/\d{1,2}/\d{4})$"
)
_HIGH_PRECISION_FRACTION_PATTERN = re.compile(r"\.\d{7,}")
_FULL_ISO_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,6})?(?:Z|z|[+-]\d{2}:?\d{2})?$"
)
_COMMON_DATETIME_FORMATS = (
    "%m/%d/%Y %H:%M:%S.%f",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %I:%M:%S.%f %p",
    "%m/%d/%Y %I:%M:%S %p",
    "%Y/%m/%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
)


def _audit_clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _audit_normalize_path(value):
    text = _audit_clean(value).lower().replace("[*]", "[]")
    if text.startswith("$."):
        text = text[2:]
    text = re.sub(r"\s*\.\s*", ".", text)
    text = re.sub(r"\s+", "", text)
    return text.strip(".")


def _audit_to_python(value):
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if hasattr(value, "as_list"):
        return value.as_list()
    return value


def _audit_meaningful(value):
    value = _audit_to_python(value)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_audit_meaningful(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_audit_meaningful(item) for item in value)
    return True


def _audit_payload(value):
    try:
        value = _audit_to_python(value)
        if value is None:
            return {}, False
        if isinstance(value, dict):
            return value, False
        if isinstance(value, str):
            parsed = json.loads(value)
            return (parsed, False) if isinstance(parsed, dict) else ({}, True)
        return {}, True
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}, True


def _audit_value_fingerprint(value):
    value = _audit_to_python(value)

    def _json_default(item):
        if isinstance(item, (datetime.datetime, datetime.date)):
            # Cell 5 serializes non-JSON-native values with default=str.
            return str(item)
        return str(item)

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )


def _audit_parse_datetime_text(text):
    candidate = text.strip()
    if not candidate:
        return None

    if _FULL_ISO_DATETIME_PATTERN.fullmatch(candidate):
        parse_candidate = candidate
        if parse_candidate.endswith(("Z", "z")):
            parse_candidate = parse_candidate[:-1] + "+00:00"
        try:
            return datetime.datetime.fromisoformat(parse_candidate)
        except ValueError:
            return None

    for date_format in _COMMON_DATETIME_FORMATS:
        try:
            return datetime.datetime.strptime(candidate, date_format)
        except ValueError:
            continue
    return None


def _audit_datetime_probe(value):
    value = _audit_to_python(value)
    strict_rfc3339 = False
    utc_z_canonical = False

    if isinstance(value, bool):
        return {
            "CLASS": "NON_TIMESTAMP_SCALAR",
            "DATETIME": None,
            "UTC_KEY": None,
            "STRICT_RFC3339": False,
            "UTC_Z_CANONICAL": False,
        }
    if isinstance(value, datetime.datetime):
        parsed = value
    elif isinstance(value, datetime.date):
        return {
            "CLASS": "DATE_ONLY",
            "DATETIME": None,
            "UTC_KEY": None,
            "STRICT_RFC3339": False,
            "UTC_Z_CANONICAL": False,
        }
    elif isinstance(value, str):
        text = value.strip()
        if _DATE_ONLY_PATTERN.fullmatch(text):
            return {
                "CLASS": "DATE_ONLY",
                "DATETIME": None,
                "UTC_KEY": None,
                "STRICT_RFC3339": False,
                "UTC_Z_CANONICAL": False,
            }
        if _HIGH_PRECISION_FRACTION_PATTERN.search(text):
            # datetime only retains microseconds. Never truncate a seventh or
            # later digit and report distinct instants as equally equal.
            return {
                "CLASS": "HIGH_PRECISION_UNSUPPORTED",
                "DATETIME": None,
                "UTC_KEY": None,
                "STRICT_RFC3339": False,
                "UTC_Z_CANONICAL": False,
            }
        strict_rfc3339 = bool(_RFC3339_AWARE_PATTERN.fullmatch(text))
        utc_z_canonical = bool(_UTC_Z_PATTERN.fullmatch(text))
        parsed = _audit_parse_datetime_text(text)
        if parsed is None:
            return {
                "CLASS": "UNRECOGNIZED",
                "DATETIME": None,
                "UTC_KEY": None,
                "STRICT_RFC3339": False,
                "UTC_Z_CANONICAL": False,
            }
    elif isinstance(value, (dict, list, tuple, set)):
        return {
            "CLASS": "NON_SCALAR",
            "DATETIME": None,
            "UTC_KEY": None,
            "STRICT_RFC3339": False,
            "UTC_Z_CANONICAL": False,
        }
    else:
        # Numeric epochs and other implicit conversions are intentionally not
        # guessed. They require an explicit, approved artifact rule.
        return {
            "CLASS": "NON_TIMESTAMP_SCALAR",
            "DATETIME": None,
            "UTC_KEY": None,
            "STRICT_RFC3339": False,
            "UTC_Z_CANONICAL": False,
        }

    timezone_aware = (
        parsed.tzinfo is not None and parsed.utcoffset() is not None
    )
    if not timezone_aware:
        return {
            "CLASS": "PARSEABLE_NAIVE",
            "DATETIME": parsed,
            "UTC_KEY": None,
            "STRICT_RFC3339": False,
            "UTC_Z_CANONICAL": False,
        }

    utc_value = parsed.astimezone(datetime.timezone.utc)
    return {
        "CLASS": "PARSEABLE_AWARE",
        "DATETIME": parsed,
        "UTC_KEY": utc_value.isoformat(timespec="microseconds"),
        "STRICT_RFC3339": strict_rfc3339,
        "UTC_Z_CANONICAL": utc_z_canonical,
    }


def _audit_mapping_type(value):
    token = re.sub(
        r"[^a-z0-9]+", "_", _audit_clean(value).lower()
    ).strip("_")
    return "TRANSFORM" if "transform" in token else token.upper()


def _run_last_modified_audit():
    artifact_row_count = len(mapping_artifact_pdf)
    snowpark_mapping_row_count = mapping_df.count()
    if (
        artifact_row_count != snowpark_mapping_row_count
        or artifact_row_count != EXPECTED_LOADED_ARTIFACT_ROWS
    ):
        raise RuntimeError(
            "Mapping artifact baseline drifted. Expected the audited "
            f"{EXPECTED_LOADED_ARTIFACT_ROWS}-row baseline; found "
            f"Pandas={artifact_row_count} and "
            f"Snowpark={snowpark_mapping_row_count}. Rerun the mapping-"
            "artifact progress audit before this target diagnostic."
        )

    expected_sources = set(CANDIDATE_SOURCE_FIELDS)
    candidate_rows = []
    all_target_rows = []
    for mapping_row in CANONICAL_MAPPING_ROWS:
        owner_path = _audit_normalize_path(
            mapping_row.get("OWNER_ELEMENT_PATH")
        )
        target_field = _audit_normalize_path(
            _target_field_name(mapping_row)
        )
        if owner_path != TARGET_OWNER_PATH or target_field != TARGET_FIELD_NAME:
            continue
        all_target_rows.append(mapping_row)

        source_field = _audit_clean(
            mapping_row.get("SOURCE_FIELD_NAME")
        ).upper()
        mapping_status = _audit_clean(mapping_row.get("STATUS")).lower()
        if (
            source_field
            and _audit_mapping_type(mapping_row.get("MAPPING_TYPE"))
            == "TRANSFORM"
            and "tbd" not in mapping_status
            and "more information" not in mapping_status
        ):
            candidate_rows.append(mapping_row)

    candidate_sources = [
        _audit_clean(row.get("SOURCE_FIELD_NAME")).upper()
        for row in candidate_rows
    ]
    if (
        len(all_target_rows) != 2
        or len(candidate_rows) != 2
        or len(set(candidate_sources)) != 2
        or set(candidate_sources) != expected_sources
    ):
        raise RuntimeError(
            "metadata.last-modified mapping contract drifted. Expected "
            "exactly two unique, executable Transform candidates; found "
            f"{len(all_target_rows)} target rows and "
            f"{len(set(candidate_sources))} eligible sources."
        )

    candidate_mapping_counts = Counter(candidate_sources)
    if any(
        candidate_mapping_counts[field_name] != 1
        for field_name in CANDIDATE_SOURCE_FIELDS
    ):
        raise RuntimeError(
            "metadata.last-modified contains duplicate candidate mappings."
        )

    source_values = {
        field_name: {} for field_name in CANDIDATE_SOURCE_FIELDS
    }
    source_ids = []
    blank_source_ids = 0
    source_parse_errors = 0
    source_resolution_errors = 0

    for source_row in source_df.select(
        "SOURCE_RECORD_ID", "CURATED_JSON"
    ).to_local_iterator():
        source_record_id = _audit_clean(source_row["SOURCE_RECORD_ID"])
        if not source_record_id:
            blank_source_ids += 1
            continue
        source_ids.append(source_record_id)
        try:
            source_object = _parse_source_json(source_row)
        except (TypeError, ValueError, json.JSONDecodeError):
            source_parse_errors += 1
            continue

        for field_name in CANDIDATE_SOURCE_FIELDS:
            try:
                source_value = resolve_json_path(source_object, field_name)
            except (AttributeError, KeyError, TypeError, ValueError):
                source_resolution_errors += 1
                continue
            if _audit_meaningful(source_value):
                source_values[field_name][source_record_id] = source_value

    source_id_set = set(source_ids)
    duplicate_source_ids = len(source_ids) - len(source_id_set)
    if (
        not source_ids
        or blank_source_ids
        or duplicate_source_ids
        or source_parse_errors
        or source_resolution_errors
    ):
        raise RuntimeError(
            "Source identity or parsing failed: "
            f"rows={len(source_ids)}, blank_ids={blank_source_ids}, "
            f"duplicate_ids={duplicate_source_ids}, "
            f"parse_errors={source_parse_errors}, "
            f"resolution_errors={source_resolution_errors}."
        )

    candidate_stats = {
        field_name: Counter() for field_name in CANDIDATE_SOURCE_FIELDS
    }
    candidate_probes = {
        field_name: {} for field_name in CANDIDATE_SOURCE_FIELDS
    }
    for field_name in CANDIDATE_SOURCE_FIELDS:
        for source_record_id, source_value in source_values[field_name].items():
            probe = _audit_datetime_probe(source_value)
            candidate_probes[field_name][source_record_id] = probe
            stats = candidate_stats[field_name]
            stats["POPULATED_RECORDS"] += 1
            stats[probe["CLASS"]] += 1
            if probe["STRICT_RFC3339"]:
                stats["STRICT_RFC3339"] += 1
            if probe["UTC_Z_CANONICAL"]:
                stats["UTC_Z_CANONICAL"] += 1

    candidate_a, candidate_b = CANDIDATE_SOURCE_FIELDS
    candidate_a_ids = set(source_values[candidate_a])
    candidate_b_ids = set(source_values[candidate_b])
    both_ids = candidate_a_ids & candidate_b_ids
    only_a_ids = candidate_a_ids - candidate_b_ids
    only_b_ids = candidate_b_ids - candidate_a_ids
    neither_ids = source_id_set - (candidate_a_ids | candidate_b_ids)

    overlap_stats = Counter(
        {
            "NEITHER_POPULATED": len(neither_ids),
            "ONLY_CANDIDATE_A": len(only_a_ids),
            "ONLY_CANDIDATE_B": len(only_b_ids),
            "BOTH_POPULATED": len(both_ids),
        }
    )
    for source_record_id in both_ids:
        value_a = source_values[candidate_a][source_record_id]
        value_b = source_values[candidate_b][source_record_id]
        probe_a = candidate_probes[candidate_a][source_record_id]
        probe_b = candidate_probes[candidate_b][source_record_id]

        raw_equal = (
            _audit_value_fingerprint(value_a)
            == _audit_value_fingerprint(value_b)
        )
        overlap_stats[
            "RAW_EQUAL" if raw_equal else "RAW_DIFFERENT"
        ] += 1

        if (
            probe_a["CLASS"] == "PARSEABLE_AWARE"
            and probe_b["CLASS"] == "PARSEABLE_AWARE"
        ):
            if probe_a["UTC_KEY"] == probe_b["UTC_KEY"]:
                overlap_stats["NORMALIZED_EQUAL"] += 1
            else:
                overlap_stats["NORMALIZED_DIFFERENT"] += 1
                if probe_a["DATETIME"].astimezone(
                    datetime.timezone.utc
                ) > probe_b["DATETIME"].astimezone(datetime.timezone.utc):
                    overlap_stats["CANDIDATE_A_LATER"] += 1
                else:
                    overlap_stats["CANDIDATE_B_LATER"] += 1
        else:
            overlap_stats["NORMALIZED_COMPARISON_BLOCKED"] += 1
            if not raw_equal:
                overlap_stats[
                    "DIFFERENT_AND_COMPARISON_BLOCKED"
                ] += 1

    metadata_payloads = {}
    metadata_node_counts = Counter()
    malformed_metadata_payloads = 0
    metadata_instance_key_errors = 0
    for node_row in (
        final_nodes_df.select(
            "SOURCE_RECORD_ID", "ELEMENT_PATH", "INSTANCE_KEY", "METADATA_JSON"
        )
        .filter(col("ELEMENT_PATH") == lit(TARGET_OWNER_PATH))
        .to_local_iterator()
    ):
        source_record_id = _audit_clean(node_row["SOURCE_RECORD_ID"])
        metadata_node_counts[source_record_id] += 1
        if _audit_clean(node_row["INSTANCE_KEY"]).lower() != "singleton":
            metadata_instance_key_errors += 1
        payload, malformed = _audit_payload(node_row["METADATA_JSON"])
        if malformed:
            malformed_metadata_payloads += 1
            continue
        metadata_payloads[source_record_id] = payload

    duplicate_metadata_records = sum(
        count - 1 for count in metadata_node_counts.values() if count > 1
    )
    metadata_id_set = set(metadata_node_counts)
    missing_metadata_records = len(source_id_set - metadata_id_set)
    extra_metadata_records = len(metadata_id_set - source_id_set)
    if (
        malformed_metadata_payloads
        or metadata_instance_key_errors
        or duplicate_metadata_records
        or missing_metadata_records
        or extra_metadata_records
    ):
        raise RuntimeError(
            "Generated metadata identity or payload validation failed: "
            f"malformed_payloads={malformed_metadata_payloads}, "
            f"instance_key_errors={metadata_instance_key_errors}, "
            f"duplicate_nodes={duplicate_metadata_records}, "
            f"missing_records={missing_metadata_records}, "
            f"extra_records={extra_metadata_records}."
        )

    output_stats = Counter()
    for source_record_id in source_ids:
        output_value = metadata_payloads[source_record_id].get(
            TARGET_FIELD_NAME
        )
        if not _audit_meaningful(output_value):
            output_stats["MISSING"] += 1
            continue

        output_stats["POPULATED"] += 1
        output_probe = _audit_datetime_probe(output_value)
        output_stats[output_probe["CLASS"]] += 1
        if output_probe["STRICT_RFC3339"]:
            output_stats["STRICT_RFC3339"] += 1
        if output_probe["UTC_Z_CANONICAL"]:
            output_stats["UTC_Z_CANONICAL"] += 1

        has_a = source_record_id in source_values[candidate_a]
        has_b = source_record_id in source_values[candidate_b]
        raw_match_a = has_a and (
            _audit_value_fingerprint(output_value)
            == _audit_value_fingerprint(
                source_values[candidate_a][source_record_id]
            )
        )
        raw_match_b = has_b and (
            _audit_value_fingerprint(output_value)
            == _audit_value_fingerprint(
                source_values[candidate_b][source_record_id]
            )
        )
        if raw_match_a and raw_match_b:
            output_stats["RAW_MATCH_BOTH"] += 1
        elif raw_match_a:
            output_stats["RAW_MATCH_CANDIDATE_A_ONLY"] += 1
        elif raw_match_b:
            output_stats["RAW_MATCH_CANDIDATE_B_ONLY"] += 1
        else:
            output_stats["RAW_MATCH_NEITHER"] += 1

        if output_probe["CLASS"] == "PARSEABLE_AWARE":
            normalized_matches = []
            for field_name in CANDIDATE_SOURCE_FIELDS:
                candidate_probe = candidate_probes[field_name].get(
                    source_record_id
                )
                if (
                    candidate_probe
                    and candidate_probe["CLASS"] == "PARSEABLE_AWARE"
                    and candidate_probe["UTC_KEY"] == output_probe["UTC_KEY"]
                ):
                    normalized_matches.append(field_name)
            if len(normalized_matches) == 2:
                output_stats["NORMALIZED_MATCH_BOTH"] += 1
            elif normalized_matches == [candidate_a]:
                output_stats[
                    "NORMALIZED_MATCH_CANDIDATE_A_ONLY"
                ] += 1
            elif normalized_matches == [candidate_b]:
                output_stats[
                    "NORMALIZED_MATCH_CANDIDATE_B_ONLY"
                ] += 1
            else:
                output_stats["NORMALIZED_MATCH_NEITHER"] += 1

    source_problem_count = sum(
        stats[class_name]
        for stats in candidate_stats.values()
        for class_name in (
            "DATE_ONLY",
            "NON_SCALAR",
            "NON_TIMESTAMP_SCALAR",
            "HIGH_PRECISION_UNSUPPORTED",
            "UNRECOGNIZED",
        )
    )
    naive_source_count = sum(
        stats["PARSEABLE_NAIVE"] for stats in candidate_stats.values()
    )

    configured_precedence = CONFIG.get("LAST_MODIFIED_SOURCE_PRECEDENCE")
    precedence_setting_present = bool(configured_precedence)
    if isinstance(configured_precedence, (list, tuple)):
        normalized_precedence = tuple(
            _audit_clean(item).upper() for item in configured_precedence
        )
    else:
        normalized_precedence = ()
    precedence_configured = bool(
        len(normalized_precedence) == len(CANDIDATE_SOURCE_FIELDS)
        and len(set(normalized_precedence)) == len(CANDIDATE_SOURCE_FIELDS)
        and set(normalized_precedence) == expected_sources
    )
    precedence_setting_invalid = bool(
        precedence_setting_present and not precedence_configured
    )

    configured_source_timezone = _audit_clean(
        CONFIG.get("LAST_MODIFIED_SOURCE_TIMEZONE")
    )
    source_timezone_setting_present = bool(configured_source_timezone)
    source_timezone_configured = False
    if source_timezone_setting_present:
        if configured_source_timezone.upper() == "UTC":
            source_timezone_configured = True
        else:
            try:
                ZoneInfo(configured_source_timezone)
                source_timezone_configured = True
            except (ZoneInfoNotFoundError, ValueError):
                source_timezone_configured = False
    source_timezone_setting_invalid = bool(
        source_timezone_setting_present and not source_timezone_configured
    )

    named_transform_helper_present = callable(
        globals().get("transform_last_modified")
    )

    precedence_decision_required = bool(
        overlap_stats["NORMALIZED_DIFFERENT"]
        and not precedence_configured
    )
    comparison_policy_required = bool(
        overlap_stats["DIFFERENT_AND_COMPARISON_BLOCKED"]
    )
    # A timezone name alone does not decide how DST folds/gaps or historical
    # local-time ambiguity must be handled. Any naive timestamp therefore
    # remains an explicit policy decision in this pre-implementation audit.
    timezone_decision_required = bool(naive_source_count)
    source_format_review_required = bool(source_problem_count)
    source_completeness_required = bool(
        overlap_stats["NEITHER_POPULATED"]
    )
    decision_required = any(
        (
            precedence_setting_invalid,
            source_timezone_setting_invalid,
            precedence_decision_required,
            comparison_policy_required,
            timezone_decision_required,
            source_format_review_required,
        )
    )
    if decision_required:
        result_label = "DECISION REQUIRED"
    elif source_completeness_required:
        result_label = (
            "TRANSFORM IMPLEMENTATION READY; SOURCE COMPLETENESS REQUIRED"
        )
    else:
        result_label = "TRANSFORM IMPLEMENTATION READY"

    print("=" * 78)
    print("SSP METADATA.LAST-MODIFIED READINESS AUDIT")
    print("=" * 78)
    print("Target OSCAL path:", TARGET_OSCAL_PATH)
    print("Loaded mapping artifact rows:", artifact_row_count)
    print("Candidate mappings found:", len(candidate_rows))
    print("Expected two-candidate contract matched: True")
    print("Candidate order is approved precedence: False")
    print("Source records:", len(source_ids))
    print("Source identities unique and metadata-reconciled: True")
    print("Generated metadata nodes:", len(metadata_id_set))

    for candidate_label, field_name in zip(
        CANDIDATE_LABELS, CANDIDATE_SOURCE_FIELDS
    ):
        stats = candidate_stats[field_name]
        print("-" * 78)
        print(
            candidate_label,
            "mapping rows:",
            candidate_mapping_counts[field_name],
        )
        print(candidate_label, "populated records:", stats["POPULATED_RECORDS"])
        print(candidate_label, "strict RFC3339 + timezone:", stats["STRICT_RFC3339"])
        print(candidate_label, "parseable timezone-aware:", stats["PARSEABLE_AWARE"])
        print(
            candidate_label,
            "parseable but timezone-naive:",
            stats["PARSEABLE_NAIVE"],
        )
        print(candidate_label, "date-only:", stats["DATE_ONLY"])
        print(candidate_label, "non-scalar:", stats["NON_SCALAR"])
        print(
            candidate_label,
            "high precision requiring explicit support:",
            stats["HIGH_PRECISION_UNSUPPORTED"],
        )
        print(
            candidate_label,
            "non-timestamp scalar:",
            stats["NON_TIMESTAMP_SCALAR"],
        )
        print(candidate_label, "unrecognized:", stats["UNRECOGNIZED"])

    print("-" * 78)
    print("Records with neither candidate:", overlap_stats["NEITHER_POPULATED"])
    print("Records with only Candidate A:", overlap_stats["ONLY_CANDIDATE_A"])
    print("Records with only Candidate B:", overlap_stats["ONLY_CANDIDATE_B"])
    print("Records with both candidates:", overlap_stats["BOTH_POPULATED"])
    print("Both candidates raw-equal:", overlap_stats["RAW_EQUAL"])
    print("Both candidates raw-different:", overlap_stats["RAW_DIFFERENT"])
    print("Both candidates normalized-equal:", overlap_stats["NORMALIZED_EQUAL"])
    print(
        "Both candidates normalized-different:",
        overlap_stats["NORMALIZED_DIFFERENT"],
    )
    print("Candidate A later:", overlap_stats["CANDIDATE_A_LATER"])
    print("Candidate B later:", overlap_stats["CANDIDATE_B_LATER"])
    print(
        "Normalized comparison blocked:",
        overlap_stats["NORMALIZED_COMPARISON_BLOCKED"],
    )
    print(
        "Raw-different and comparison blocked:",
        overlap_stats["DIFFERENT_AND_COMPARISON_BLOCKED"],
    )

    print("-" * 78)
    print("Generated last-modified populated:", output_stats["POPULATED"])
    print("Generated last-modified missing:", output_stats["MISSING"])
    print(
        "Generated strict RFC3339 + timezone:",
        output_stats["STRICT_RFC3339"],
    )
    print("Generated canonical UTC Z:", output_stats["UTC_Z_CANONICAL"])
    print(
        "Generated parseable but timezone-naive:",
        output_stats["PARSEABLE_NAIVE"],
    )
    print("Generated date-only:", output_stats["DATE_ONLY"])
    print("Generated non-scalar:", output_stats["NON_SCALAR"])
    print(
        "Generated high precision requiring explicit support:",
        output_stats["HIGH_PRECISION_UNSUPPORTED"],
    )
    print(
        "Generated non-timestamp scalar:",
        output_stats["NON_TIMESTAMP_SCALAR"],
    )
    print("Generated unrecognized:", output_stats["UNRECOGNIZED"])
    print("Generated raw match both:", output_stats["RAW_MATCH_BOTH"])
    print(
        "Generated raw match Candidate A only:",
        output_stats["RAW_MATCH_CANDIDATE_A_ONLY"],
    )
    print(
        "Generated raw match Candidate B only:",
        output_stats["RAW_MATCH_CANDIDATE_B_ONLY"],
    )
    print("Generated raw match neither:", output_stats["RAW_MATCH_NEITHER"])
    print(
        "Generated normalized match both:",
        output_stats["NORMALIZED_MATCH_BOTH"],
    )
    print(
        "Generated normalized match Candidate A only:",
        output_stats["NORMALIZED_MATCH_CANDIDATE_A_ONLY"],
    )
    print(
        "Generated normalized match Candidate B only:",
        output_stats["NORMALIZED_MATCH_CANDIDATE_B_ONLY"],
    )
    print(
        "Generated normalized match neither:",
        output_stats["NORMALIZED_MATCH_NEITHER"],
    )

    print("-" * 78)
    print(
        "Source precedence setting present:",
        precedence_setting_present,
    )
    print("Source precedence setting valid:", precedence_configured)
    print(
        "Source precedence setting invalid:",
        precedence_setting_invalid,
    )
    print(
        "Source timezone setting present:",
        source_timezone_setting_present,
    )
    print("Source timezone setting valid:", source_timezone_configured)
    print(
        "Source timezone setting invalid:",
        source_timezone_setting_invalid,
    )
    print(
        "Named timestamp transform helper present:",
        named_transform_helper_present,
    )
    print("Precedence decision required:", precedence_decision_required)
    print("Comparison/format policy required:", comparison_policy_required)
    print("Timezone decision required:", timezone_decision_required)
    print("Source format review required:", source_format_review_required)
    print("Source completeness required:", source_completeness_required)
    print("Existing output normalization required:", bool(
        output_stats["POPULATED"] != len(source_ids)
        or output_stats["UTC_Z_CANONICAL"] != len(source_ids)
    ))
    print("Diagnostic performed writes: False")
    print("Whole-SSP conformance established: False")
    print("RESULT:", result_label)
    print(
        "NEXT: record aggregate output; never choose mapping order, latest "
        "timestamp, or a timezone implicitly."
    )

    # This result contains aggregate counts and flags only. Record identities,
    # timestamps, source objects, and payloads remain function-local and are
    # released when the audit returns.
    return {
        "TARGET_OSCAL_PATH": TARGET_OSCAL_PATH,
        "SOURCE_RECORDS": len(source_ids),
        "CANDIDATE_A": dict(candidate_stats[candidate_a]),
        "CANDIDATE_B": dict(candidate_stats[candidate_b]),
        "OVERLAP": dict(overlap_stats),
        "OUTPUT": dict(output_stats),
        "PRECEDENCE_SETTING_PRESENT": precedence_setting_present,
        "PRECEDENCE_CONFIGURED": precedence_configured,
        "PRECEDENCE_SETTING_INVALID": precedence_setting_invalid,
        "SOURCE_TIMEZONE_SETTING_PRESENT": source_timezone_setting_present,
        "SOURCE_TIMEZONE_CONFIGURED": source_timezone_configured,
        "SOURCE_TIMEZONE_SETTING_INVALID": source_timezone_setting_invalid,
        "NAMED_TRANSFORM_HELPER_PRESENT": named_transform_helper_present,
        "PRECEDENCE_DECISION_REQUIRED": precedence_decision_required,
        "COMPARISON_POLICY_REQUIRED": comparison_policy_required,
        "TIMEZONE_DECISION_REQUIRED": timezone_decision_required,
        "SOURCE_FORMAT_REVIEW_REQUIRED": source_format_review_required,
        "SOURCE_COMPLETENESS_REQUIRED": source_completeness_required,
        "RESULT": re.sub(r"[^A-Z0-9]+", "_", result_label).strip("_"),
        "WRITES_EXECUTED": False,
        "WHOLE_SSP_CONFORMANCE_ESTABLISHED": False,
    }


last_modified_audit_result = _run_last_modified_audit()
