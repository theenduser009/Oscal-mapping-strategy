Yes — this is the better approach. Instead of asking “what branches happen to be in our registry?”, we should use the official NIST OSCAL SSP structure as the master tree, then compare our registry/mapping against it.

The current NIST OSCAL reference lists v1.2.3 as the latest release. At the SSP root, system-security-plan has these major branches: metadata, import-profile, system-characteristics, system-implementation, control-implementation, and optional back-matter. 

Conceptually:

system-security-plan
│
├── metadata
│
├── import-profile
│
├── system-characteristics
│
├── system-implementation
│
├── control-implementation
│
└── back-matter

NIST describes them roughly like this: system-characteristics holds the system description, information types, impact levels, boundaries and related characteristics; system-implementation describes how the system is implemented, including components/users/inventory; and control-implementation describes how controls are satisfied. 

Where I want us to work next

We already spent time under:

system-security-plan
└── system-implementation
    └── components[]

and hit the Archer cross-table-reference problem.

We also checked:

system-security-plan
└── system-characteristics

but our registry currently stops at the children we saw.

So rather than inventing another branch, let’s interrogate the official NIST SSP hierarchy branch-by-branch and build our registry from that.

The strongest next candidate is:

system-security-plan
└── control-implementation

because this is a major SSP branch, and NIST defines it specifically as the section describing how the system satisfies controls. It goes deeper into structures such as implemented requirements and component-level implementation information. 

Before touching the mapper, run this against our registry:

SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    ITEM_PATH,
    PROCESS_ORDER,
    IS_ACTIVE
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH ILIKE 'system-security-plan.control-implementation%'
ORDER BY PROCESS_ORDER, NODE_PATH;

Why this is the next check

We're answering one very specific question:

> How much of the official NIST control-implementation hierarchy have we actually registered?



If it returns only the root, we expand the registry using the NIST SSP model.

If it returns several levels, we inspect those levels and find the first missing NIST child.

If it returns nothing, then we've discovered a major SSP branch we haven't modeled yet.

Send me only that query result next. Then I'll line it up against the NIST SSP tree and tell you the exact next registry nodes to add — no mapper modification yet.