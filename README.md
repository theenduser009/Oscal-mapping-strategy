Yes! This is a good result. We finally have actual Archer data successfully becoming an OSCAL system-characteristics payload.

For source record 565189, your mapper produced:

system-name                 = OpenVMS Server
system-name-short           = Application
description                 = OpenVMS primary function...
date-authorized             = 2017-07-19
security-sensitivity-level  = DPARs

So the basic mechanism is working:

Archer field → CSV mapping → registry ownership → OSCAL payload.

There is one thing I want to flag, but not fix yet:

"INFORMATION_SYSTEM_TYPE": [
    80643
]

Because its CSV path terminates at system-characteristics and is marked Extension Property, your generic builder preserves the Archer field name. That may ultimately need to become an OSCAL prop, but we shouldn't change generic mapper logic based on one field yet.

Next: test all 5 children together

Run this read-only cell. This will tell us exactly what each child node produces for the same record 565189:

# ================================================================
# READ ONLY - system-characteristics child payload validation
# ================================================================

child_paths = [
    "system-security-plan.system-characteristics.authorization-boundary",
    "system-security-plan.system-characteristics.security-impact-level",
    "system-security-plan.system-characteristics.status",
    "system-security-plan.system-characteristics.system-ids[]",
    "system-security-plan.system-characteristics.props[]"
]

print("SOURCE_RECORD_ID:", test_record["SOURCE_RECORD_ID"])

for node_path in child_paths:

    mappings = get_mappings_for_node(
        canonical_mapping_df,
        element_registry_df,
        node_path,
        CONFIG["OSCAL_MODEL"]
    )

    payload = build_element_payload(
        test_record,
        mappings
    )

    print("\n" + "=" * 90)
    print("NODE:", node_path)
    print("OWNED MAPPINGS:", len(mappings))
    print("PAYLOAD:")
    print(json.dumps(payload, indent=2, default=str))

Don't change the registry, CSV, or mapper yet.

This result will be especially useful because we can see whether security-impact-level, status, system-ids[], props[], and authorization-boundary are actually populated. Then we'll fix only what the evidence shows is wrong.