# RUN NOW — Source One SSP responsible-party mapping compile check
# Date: 2026-09-21
# READ ONLY. Run after replacing ARCHER_OSCAL_MAPPINGS.csv and rerunning Cells 1-3 with SSP selected.
#
# Expected:
# - the four newly approved role fields compile to responsible-parties[]
# - each uses the existing direct transform and source-preserving role id/title
# - ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER remains deferred / not compiled

EXPECTED = {
    "SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO": (
        "direct",
        "system-security-plan.metadata.responsible-parties[]",
        "senior-information-systems-security-officer",
        "Senior Information Systems Security Officer",
    ),
    "INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE": (
        "direct",
        "system-security-plan.metadata.responsible-parties[]",
        "information-system-security-engineer",
        "Information System Security Engineer",
    ),
    "INFORMATION_SYSTEM_ADMINISTRATOR_ISA": (
        "direct",
        "system-security-plan.metadata.responsible-parties[]",
        "information-system-administrator",
        "Information System Administrator",
    ),
    "AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR": (
        "direct",
        "system-security-plan.metadata.responsible-parties[]",
        "authorizing-official-designated-representative",
        "Authorizing Official Designated Representative",
    ),
}

context = next(
    (
        c for c in MAPPING_CONTEXTS
        if c["source_key"] == "source-one"
        and c["config"]["OSCAL_MODEL"] == "SSP"
    ),
    None,
)
if context is None:
    raise ValueError("Source One SSP context is not loaded; select SSP and rerun Cells 1-3.")

rows = {row["SOURCE_FIELD_NAME"]: row for row in context["mapping_rows"]}

print("SOURCE_ONE_SSP_RESPONSIBLE_PARTY_COMPILE_CHECK")
print("ROUTE_STATUS:", context["routing_report"]["STATUS"])
print("SELECTED_ROWS_TOTAL:", context["routing_report"]["SELECTED_ROWS"])

for field, (transform, path, role_id, role_title) in EXPECTED.items():
    row = rows.get(field)
    if row is None:
        raise ValueError(field + " is not compiled")
    actual = (
        row["TRANSFORM_ID"],
        row["CANONICAL_ELEMENT_PATH"],
        row["REPRESENTATION_PARAMS"].get("role_id"),
        row["REPRESENTATION_PARAMS"].get("role_title"),
    )
    expected = (transform, path, role_id, role_title)
    if actual != expected:
        raise ValueError(field + " compiled differently: " + repr(actual))
    print(field, "|", actual[0], "|", actual[1], "|", actual[2])

if "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER" in rows:
    raise ValueError("CONFIRMED_IN_ARCHER must remain deferred until source value semantics exist")

print("ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER | DEFERRED | NOT_COMPILED")
print("RESULT: SSP_RESPONSIBLE_PARTY_MAPPINGS_READY_FOR_PREVIEW")
