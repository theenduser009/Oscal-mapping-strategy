Yes — this is a great branch to work on. Your result shows only the control-implementation root is currently registered, so this is exactly where we can extend the SSP graph properly from the NIST structure instead of guessing.

According to the NIST SSP model, control-implementation has three direct children: a required description, optional set-parameters[], and required implemented-requirements[]. The important branch for us is implemented-requirements[], because each instance represents one control such as AC-1, AC-2, etc. 

system-security-plan
└── control-implementation
    ├── description
    ├── set-parameters[]
    └── implemented-requirements[]
         ├── set-parameters[]
         ├── responsible-roles[]
         ├── statements[]
         │    └── by-components[]
         └── by-components[]

NIST specifically says an implemented-requirement describes how the system satisfies an individual control. It can contain statements, and both the implemented requirement itself and its statements can contain by-component structures describing which system component implements that control/statement. 

So I would not add everything yet. First let's determine whether Archer actually gives us data that can populate this branch.

Run this against your mapping CSV:

from snowflake.snowpark.functions import col

(
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        .like("system-security-plan.control-implementation%")
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE",
        "TRANSFORMATION_LOGIC"
    )
    .sort("OSCAL_ELEMENT_PATH")
    .show(100)
)

This is the immediate next step.

We want to answer:

Do we already have Archer mappings for:
control-implementation
→ implemented-requirements[]
→ statements[]
→ by-components[] ?

If those mappings exist, we register the NIST nodes and run the mapper.

If they don't, do not add registry rows blindly yet — we'll inspect the Archer fields and decide which source data maps to each NIST structure.

Send me that output next. This branch is promising because it gives us a real deep hierarchy to test the node/edge mapper against.