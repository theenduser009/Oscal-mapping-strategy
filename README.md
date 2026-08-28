Perfect — this is the confirmation we wanted.

There are no NO OWNER rows in that output. So the current registry is sufficient to own all 33 system-characteristics mappings.

That means we should not add more registry nodes right now.

The ownership is behaving exactly as expected:

SAP_ID
→ system-ids[]

AUTHORIZATION_BOUNDARY_DESCRIPTION
→ authorization-boundary

OPERATIONAL_STATUS / AUTHORIZATION_DECISION / AUTHORIZATION_COMMENTS
→ status

CNSS_* / *_CONTROL_CATEGORY_*
→ security-impact-level

CRITICAL_INFRASTRUCTURE / INFORMATION_CLASSIFICATION / PACKAGE_TYPE...
→ props[]

MISSION_PURPOSE / INFORMATION_SYSTEM_TYPE / AUTHORIZATION_PACKAGE_NAME / ACRONYM
→ system-characteristics

Now the next question is more important:

> Does the mapper actually build a correct system-characteristics payload from real Archer data?



Let's test one real record only, read-only.

Run this next:

# ================================================================
# READ ONLY - inspect generated system-characteristics payload
# ================================================================

system_characteristics_path = (
    "system-security-plan.system-characteristics"
)

# Pick one source row
test_record = next(source_df.to_local_iterator())

print("SOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])

# Get mappings owned directly by system-characteristics
sc_mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    system_characteristics_path,
    CONFIG["OSCAL_MODEL"]
)

print("Owned mappings:", len(sc_mappings))

for m in sc_mappings:
    print(
        m["SOURCE_FIELD_NAME"],
        "->",
        m["OSCAL_ELEMENT_PATH"],
        "| relative:",
        m["FIELD_RELATIVE_PATH"]
    )

# Build payload
sc_payload = build_element_payload(
    test_record,
    sc_mappings
)

print("\n=== SYSTEM CHARACTERISTICS PAYLOAD ===")
print(json.dumps(sc_payload, indent=2, default=str))

What we want to see is something along the lines of:

{
  "description": "...",
  "system-name": "...",
  "short-name": "...",
  ...
}

or whatever values exist for that selected Archer record.

If that payload looks good, then we test the child nodes next:

authorization-boundary → status → security-impact-level → system-ids[] → props[].

That will tell us whether this whole SSP branch is genuinely ready before we even think about EXECUTE_WRITES=True.