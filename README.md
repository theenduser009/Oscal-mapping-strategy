Yes — let's do it as a one-time generic extension, not another scattered patch.

Cell 4 — add this above transform_mapping_value()

# ================================================================
# Generic Transform configuration
# ================================================================

RESPONSIBLE_PARTY_ROLE_MAP = {
    "INFORMATION_OWNER_IO": "information-owner",
    "INFORMATION_SYSTEM_OWNER_ISO": "system-owner",
    "AUTHORIZING_OFFICIAL_AO": "authorizing-official",
    "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO": "system-security-officer",
    "PRIVACY_OFFICER_PO": "privacy-officer",
}


def _extract_archer_user_ids(value):
    """
    Archer User/Group field ->
    list of UserList[].Id values
    """

    if value is None:
        return []

    if not isinstance(value, dict):
        return []

    user_list = value.get("UserList") or []

    ids = []

    for user in user_list:

        if not isinstance(user, dict):
            continue

        user_id = user.get("Id")

        if user_id is not None:
            ids.append(str(user_id))

    return ids


def transform_responsible_party(
    value,
    mapping
):
    """
    Generic responsible-party transformation.
    TBD source fields are deliberately untouched.
    """

    source_field = str(
        mapping.get("SOURCE_FIELD_NAME") or ""
    ).strip()

    role_id = RESPONSIBLE_PARTY_ROLE_MAP.get(
        source_field
    )

    # Not one of the architect-approved Transform rows
    if role_id is None:
        return value

    user_ids = _extract_archer_user_ids(value)

    if not user_ids:
        return None

    # One responsible-party object.
    # Keep Archer IDs deterministically as party identities for now.
    return {
        "role-id": role_id,
        "party-ids": user_ids
    }


def apply_transform(
    value,
    mapping
):
    """
    Central dispatcher for Mapping_Type = Transform.
    Future transforms plug in here instead of changing
    build_element_payload().
    """

    target_path = str(
        mapping.get("OSCAL_ELEMENT_PATH") or ""
    ).strip().lower()

    # Responsible parties
    if target_path.endswith(
        "metadata.responsible-parties[]"
    ):
        return transform_responsible_party(
            value,
            mapping
        )

    # Unknown Transform:
    # preserve source value until a rule is implemented
    return value

Then update transform_mapping_value()

At the top of that function, after you calculate mapping_type, add:

if mapping_type == "transform":
    return apply_transform(
        value,
        mapping
    )

So the beginning should look like:

def transform_mapping_value(
    value,
    mapping
):

    mapping_type = str(
        mapping.get("MAPPING_TYPE") or ""
    ).strip().lower()

    # Generic Transform dispatcher
    if mapping_type == "transform":
        return apply_transform(
            value,
            mapping
        )

    # Plain Direct
    if mapping_type == "direct":
        return value

    # Reference stays untouched for now
    if mapping_type == "reference":
        return value

    # Direct/Transform continues below
    if mapping_type != "direct/transform":
        return value

    # ... keep your existing FIPS code below unchanged ...

Do not change build_element_payload() again.

This gives us the stable architecture:

Mapping CSV
    ↓
MAPPING_TYPE
    ↓
transform_mapping_value()
    ↓
apply_transform()
    ↓
specific reusable handler

For future POA&M, Assessment Results, timestamps, enums, etc., we extend apply_transform() instead of rewriting the mapper.

One deliberate point: I used party-ids for this first controlled implementation rather than pretending we've already solved OSCAL party-uuids. First we prove the five approved source fields resolve to the correct roles/users. Then we can make the identity representation OSCAL-final without disturbing the generic architecture.