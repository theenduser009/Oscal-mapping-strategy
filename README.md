Excellent — this is the result we needed. 33 mappings exist for system-characteristics, and now the structure is much clearer.

The important thing is: we should not create 33 registry nodes. Many of those mappings are leaf values owned by a smaller number of structural OSCAL nodes.

From your screenshot, the meaningful structure is roughly:

system-security-plan
└── system-characteristics
    ├── authorization-boundary
    │   └── description
    ├── props[]
    ├── security-impact-level
    │   ├── security-objective-availability
    │   ├── security-objective-confidentiality
    │   └── security-objective-integrity
    ├── status
    │   ├── state
    │   └── remarks
    └── system-ids[]
        └── id

Your existing registry already has the major structural nodes:

authorization-boundary, props[], security-impact-level, status, and system-ids[].

So don't add anything yet.

Next validation

We need to answer one question before touching the registry:

> Does the current mapper correctly assign all 33 mappings to those existing registry nodes?



Run this read-only cell:

branch = "system-security-plan.system-characteristics"

registry_paths = [
    r["NODE_PATH"]
    for r in element_registry_df
        .filter(col("NODE_PATH").like(branch + "%"))
        .select("NODE_PATH")
        .collect()
]

mapping_rows = (
    canonical_mapping_df
    .filter(col("OSCAL_ELEMENT_PATH").like(branch + "%"))
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH"
    )
    .collect()
)

print("=== OWNERSHIP CHECK ===")

for m in mapping_rows:

    mapping_path = m["OSCAL_ELEMENT_PATH"]

    candidates = [
        p for p in registry_paths
        if mapping_path == p
        or mapping_path.startswith(p + ".")
    ]

    owner = (
        max(candidates, key=len)
        if candidates
        else "NO OWNER"
    )

    print(
        f"{m['SOURCE_FIELD_NAME']} "
        f"--> {owner}"
    )

What I expect

For example:

AUTHORIZATION_BOUNDARY_DESCRIPTION
--> ...system-characteristics.authorization-boundary

CNSS_AVAILABILITY_RATING
--> ...security-impact-level

OPERATIONAL_STATUS
--> ...status

SAP_ID
--> ...system-ids[]

CRITICAL_INFRASTRUCTURE
--> ...props[]

And fields mapped directly to:

...system-characteristics.description
...system-characteristics.system-name
...system-characteristics

should be owned by the system-characteristics node itself.

The key result we're looking for is NO OWNER.

If there are zero NO OWNER mappings, we do not need more registry nodes for these leaf fields. Then our next move is to inspect the actual generated system-characteristics payload from one Archer record.

Send me that output. We're finally testing the mapper's ownership logic rather than guessing at the OSCAL tree.