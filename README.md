Yes — much simpler. Replace one whole function only in Cell 4:

Find:

def build_element_payload(
    source_record,
    mappings,
    source_json_field="CURATED_JSON"
):

Replace that entire function with this:

def build_element_payload(
    source_record,
    mappings,
    source_json_field="CURATED_JSON"
):

    source_obj = _parse_source_json(
        source_record
    )

    payload = {}

    # Tracks which OSCAL target paths already received a real value
    written_paths = set()

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        if not source_field:
            continue

        mapping_type = str(
            mapping.get("MAPPING_TYPE") or ""
        ).strip().lower()

        value = resolve_json_path(
            source_obj,
            source_field
        )

        value = transform_mapping_value(
            value,
            mapping
        )

        relative_path = mapping.get(
            "FIELD_RELATIVE_PATH"
        )

        relative_path = (
            str(relative_path).strip()
            if relative_path is not None
            else ""
        )

        # ============================================================
        # Mapping ends at current node
        # ============================================================

        if not relative_path:

            # Direct/Transform:
            # preserve explicit NULL
            if (
                mapping_type == "direct/transform"
                and value is None
            ):
                if source_field not in payload:
                    payload[source_field] = None

                continue

            # Other empty values are skipped
            if value in (
                None,
                "",
                [],
                {}
            ):
                continue

            payload[source_field] = value

            continue

        # ============================================================
        # Nested OSCAL target
        # ============================================================

        # Direct/Transform NULL:
        # keep target key as NULL, but don't overwrite a real value
        if (
            mapping_type == "direct/transform"
            and value is None
        ):

            if relative_path not in written_paths:

                set_nested_path(
                    payload,
                    relative_path.split("."),
                    None
                )

            continue

        # Normal empty values are skipped
        if value in (
            None,
            "",
            [],
            {}
        ):
            continue

        # Real value always wins
        set_nested_path(
            payload,
            relative_path.split("."),
            value
        )

        written_paths.add(
            relative_path
        )

    return payload

That’s it.

Do not change transform_mapping_value() again.

Then run only:

Cell 4
Cell 5

After that, rerun your payload test. We want the three OSCAL security-objective keys to exist consistently, with null when no source value exists.