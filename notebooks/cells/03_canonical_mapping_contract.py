# %% Cell 3 - Canonical mapping contract

EXPECTED_MAPPING_COLUMNS = [
    "SOURCE_FIELD_NAME",
    "OSCAL_MODEL",
    "OSCAL_ELEMENT_PATH",
    "OSCAL_FIELD_NAME",
    "MAPPING_TYPE",
    "TRANSFORMATION_LOGIC",
    "STATUS",
]

MAPPING_COLUMN_ALIASES = {
    "ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME",
    "SOURCE_FIELD": "SOURCE_FIELD_NAME",
    "MODEL": "OSCAL_MODEL",
    "OSCAL_PATH": "OSCAL_ELEMENT_PATH",
    "ELEMENT_PATH": "OSCAL_ELEMENT_PATH",
    "TARGET_FIELD_NAME": "OSCAL_FIELD_NAME",
    "OSCAL_TARGET_FIELD": "OSCAL_FIELD_NAME",
    "TRANSFORM_LOGIC": "TRANSFORMATION_LOGIC",
    "MAPPING_STATUS": "STATUS",
}

canonical_mapping_pdf = mapping_artifact_pdf.copy()
canonical_mapping_pdf.rename(columns=MAPPING_COLUMN_ALIASES, inplace=True)

for column_name in EXPECTED_MAPPING_COLUMNS:
    if column_name not in canonical_mapping_pdf.columns:
        canonical_mapping_pdf[column_name] = None

for column_name in EXPECTED_MAPPING_COLUMNS:
    canonical_mapping_pdf[column_name] = canonical_mapping_pdf[
        column_name
    ].map(lambda value: value.strip() if isinstance(value, str) else value)

canonical_mapping_pdf = canonical_mapping_pdf[
    canonical_mapping_pdf["SOURCE_FIELD_NAME"].notna()
    & canonical_mapping_pdf["OSCAL_ELEMENT_PATH"].notna()
].copy()

# Mapping CSV model labels have not been consistent (for example, "SSP"
# versus "System Security Plan").  The registry is the authoritative model
# boundary, so assign each mapping to its deepest active registry owner rather
# than filtering on the display label in the CSV.
active_registry_paths = []
for registry_row in element_registry_df.collect():
    registry_values = {
        str(key).upper(): value
        for key, value in registry_row.as_dict(recursive=True).items()
    }
    registry_model = registry_values.get(
        "OSCAL_MODEL_KEY",
        registry_values.get("OSCAL_MODEL"),
    )
    if (
        registry_model is not None
        and str(registry_model).strip().upper()
        != CONFIG["OSCAL_MODEL"].upper()
    ):
        continue

    registry_active = registry_values.get("IS_ACTIVE")
    if registry_active is not None and str(registry_active).strip().upper() in {
        "FALSE",
        "F",
        "NO",
        "N",
        "0",
    }:
        continue

    registry_path = (
        registry_values.get("NODE_PATH")
        or registry_values.get("OSCAL_ELEMENT_PATH")
        or registry_values.get("ELEMENT_PATH")
        or registry_values.get("JSON_PATH")
    )
    if registry_path:
        active_registry_paths.append(str(registry_path).strip())

active_registry_paths = sorted(
    set(active_registry_paths),
    key=lambda path: (path.count("."), len(path)),
    reverse=True,
)

if not active_registry_paths:
    raise ValueError(
        "Cell 3 found no active registry paths for model "
        f"{CONFIG['OSCAL_MODEL']}"
    )


def _mapping_owner_path(mapping_path):
    mapping_path = str(mapping_path).strip()
    for registry_path in active_registry_paths:
        if mapping_path == registry_path or mapping_path.startswith(
            registry_path + "."
        ):
            return registry_path
    return None


canonical_mapping_pdf["OWNER_ELEMENT_PATH"] = canonical_mapping_pdf[
    "OSCAL_ELEMENT_PATH"
].map(_mapping_owner_path)
canonical_mapping_pdf = canonical_mapping_pdf[
    canonical_mapping_pdf["OWNER_ELEMENT_PATH"].notna()
].copy()

if canonical_mapping_pdf.empty:
    raise ValueError(
        "Cell 3 found mapping rows, but none belong to an active registry "
        f"path for model {CONFIG['OSCAL_MODEL']}"
    )

canonical_mapping_pdf["FIELD_RELATIVE_PATH"] = canonical_mapping_pdf.apply(
    lambda row: str(row["OSCAL_ELEMENT_PATH"])[
        len(str(row["OWNER_ELEMENT_PATH"])):
    ].lstrip("."),
    axis=1,
)

# When the CSV does not provide a separate target-field column, derive it
# from the portion of OSCAL_ELEMENT_PATH below the owning registry node.
missing_target_field = canonical_mapping_pdf["OSCAL_FIELD_NAME"].isna() | (
    canonical_mapping_pdf["OSCAL_FIELD_NAME"].fillna("").str.strip() == ""
)
canonical_mapping_pdf.loc[
    missing_target_field,
    "OSCAL_FIELD_NAME",
] = canonical_mapping_pdf.loc[
    missing_target_field,
    "FIELD_RELATIVE_PATH",
].map(
    lambda path: (
        str(path).split(".")[-1].replace("[]", "")
        if str(path).strip()
        else None
    )
)

canonical_mapping_pdf["OSCAL_MODEL"] = CONFIG["OSCAL_MODEL"].upper()
canonical_mapping_pdf["MAPPING_TYPE"] = (
    canonical_mapping_pdf["MAPPING_TYPE"].fillna("Direct").str.strip()
)
canonical_mapping_pdf["STATUS"] = canonical_mapping_pdf["STATUS"].fillna(
    "In Progress"
)

canonical_mapping_pdf.sort_values(
    ["OWNER_ELEMENT_PATH", "OSCAL_ELEMENT_PATH", "SOURCE_FIELD_NAME"],
    inplace=True,
    kind="stable",
)
canonical_mapping_pdf.reset_index(drop=True, inplace=True)

canonical_mapping_df = session.create_dataframe(canonical_mapping_pdf)

CANONICAL_MAPPING_ROWS = canonical_mapping_pdf.to_dict(orient="records")
MAPPINGS_BY_ELEMENT_PATH = {}
for mapping_row in CANONICAL_MAPPING_ROWS:
    owner_path = str(mapping_row["OWNER_ELEMENT_PATH"]).strip()
    MAPPINGS_BY_ELEMENT_PATH.setdefault(owner_path, []).append(mapping_row)

print("Canonical SSP mapping rows:", len(CANONICAL_MAPPING_ROWS))
print("Active SSP registry paths:", len(active_registry_paths))
print("Mapped registry owner paths:", len(MAPPINGS_BY_ELEMENT_PATH))
