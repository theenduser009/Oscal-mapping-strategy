Great — **Cell 1 only.** This is the clean production configuration cell. No mapping logic, no registry logic, no transformation logic yet.

```python
# ============================================================
# Cell 1 — Production Configuration
# NB_ARCHER_OSCAL_MAPPER_V1
# ============================================================

import uuid

from snowflake.snowpark.context import get_active_session

session = get_active_session()


CONFIG = {

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------
    "RUN_ID": str(uuid.uuid4()),

    # --------------------------------------------------------
    # OSCAL model being processed
    # --------------------------------------------------------
    "OSCAL_MODEL": "SSP",

    # --------------------------------------------------------
    # Source
    # --------------------------------------------------------
    "SOURCE_SYSTEM_NAME": "ARCHER",
    "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",

    "RAW_TABLE":
        "RTX_RAW_DEV.ES_ESC_GRC."
        "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",

    # --------------------------------------------------------
    # Structural metadata
    # --------------------------------------------------------
    "REGISTRY_TABLE":
        "RTX_RAW_DEV.ES_ESC_GRC."
        "OSCAL_ELEMENT_REGISTRY",

    # --------------------------------------------------------
    # Curated targets
    # --------------------------------------------------------
    "TARGET_DIM":
        "RTX_ENTERPRISESERVICES_DEV."
        "ES_ESC_GRC_CURATED."
        "DIM_OSCAL_SSP_ELEMENT",

    "TARGET_FACT":
        "RTX_ENTERPRISESERVICES_DEV."
        "ES_ESC_GRC_CURATED."
        "FACT_OSCAL_SSP_DEPENDENCY",

    # --------------------------------------------------------
    # Execution safety
    # Start production notebook in read-only mode
    # --------------------------------------------------------
    "EXECUTE_WRITES": False
}


print("=== OSCAL Mapper Configuration ===")
print("Model       :", CONFIG["OSCAL_MODEL"])
print("Source      :", CONFIG["RAW_TABLE"])
print("Registry    :", CONFIG["REGISTRY_TABLE"])
print("Target DIM  :", CONFIG["TARGET_DIM"])
print("Target FACT :", CONFIG["TARGET_FACT"])
print("Run ID      :", CONFIG["RUN_ID"])
print("Writes      :", CONFIG["EXECUTE_WRITES"])
```

### Why Cell 1 is intentionally boring

It only answers:

```text
What model am I running?
Where is my source?
Where is my registry?
Where do DIM/FACT go?
What is this pipeline run?
Am I allowed to write?
```

Nothing SSP-specific is hardcoded into the **mapper logic**. SSP-specific table names are configuration values, which we can later replace when another model runs.

And I deliberately set:

```python
"EXECUTE_WRITES": False
```

because our first production run should reproduce the known baseline **without touching the tables**:

```text
92,880 nodes
90,715 edges
```

Run **Cell 1 only**. If it runs cleanly, next we build **Cell 2: source + mapping + registry inputs**.
