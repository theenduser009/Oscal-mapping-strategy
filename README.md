# ====================================================================
# FIPS-199 value normalization for Direct/Transform mappings
# ====================================================================

FIPS_199_VALUE_MAP = {
    "80654": "low",
    "80655": "moderate",
    "80656": "high",
}

def transform_mapping_value(
    value,
    mapping
):
    mapping_type = str(
        mapping.get("MAPPING_TYPE") or ""
    ).strip()

    # Plain Direct: unchanged
    if mapping_type.lower() == "direct":
        return value

    # Only handle Direct/Transform here
    if mapping_type.lower() != "direct/transform":
        return value

    # Archer often gives these as one-item arrays
    if isinstance(value, list):

        transformed = []

        for item in value:
            mapped = FIPS_199_VALUE_MAP.get(
                str(item).strip()
            )

            if mapped is not None:
                transformed.append(mapped)

        if not transformed:
            return None

        # OSCAL security-objective-* is scalar
        if len(transformed) == 1:
            return transformed[0]

        return transformed

    mapped = FIPS_199_VALUE_MAP.get(
        str(value).strip()
    )

    return mapped