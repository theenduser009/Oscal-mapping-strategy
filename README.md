Perfect. ✅ metadata parent is fully validated.

Your numbers line up exactly:

Metadata nodes:             2,813
Distinct NODE_KEYs:         2,813
Null NODE_KEYs:                 0
SSP → metadata edges:       2,813

So now:

system-security-plan
└── metadata                  ✅
    ├── document-ids[]
    └── responsible-parties[]

Next: document-ids[]

Because this is a collection with INSTANCE_KEY_RULE = VALUE, before counting graph nodes I want to see what mappings/payload are actually producing those values.

Run this:

import json

node_path = "system-security-plan.metadata.document-ids[]"

mappings = get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    CONFIG["OSCAL_MODEL"]
)

print("NODE:", node_path)
print("OWNED MAPPINGS:", len(mappings))

for m in mappings:
    print(
        m["SOURCE_FIELD_NAME"],
        "->",
        m["OSCAL_ELEMENT_PATH"],
        "| relative:",
        m["FIELD_RELATIVE_PATH"]
    )

payload = build_element_payload(
    test_record,
    mappings
)

print("\nPAYLOAD:")
print(json.dumps(payload, indent=2, default=str))

Don't change anything yet. I specifically want to inspect what document-ids[] contains and why VALUE is being used as its key before we declare its graph correct.