# Read-only schema capture for the two approved SSP pilot targets.
# Copy into ONE new Snowflake Python cell and run. No edits or prior pilot needed.
# Executes DESC TABLE only: no source/payload values, staging, DML or transaction.
from snowflake.snowpark.context import get_active_session
import json

_ssp_schema_session = get_active_session()
for _ssp_schema_table in (
    "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT",
    "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY",
):
    _ssp_schema_columns = []
    for _ssp_schema_row in _ssp_schema_session.sql("DESC TABLE " + _ssp_schema_table).collect():
        _ssp_schema_meta = {str(k).lower(): v for k, v in _ssp_schema_row.as_dict().items()}
        _ssp_schema_columns.append({
            "COLUMN": _ssp_schema_meta.get("name"),
            "TYPE": _ssp_schema_meta.get("type"),
            "KIND": _ssp_schema_meta.get("kind"),
            "NULLABLE": _ssp_schema_meta.get("null?"),
            "HAS_DEFAULT": _ssp_schema_meta.get("default") is not None,
        })
    print(json.dumps({"TABLE": _ssp_schema_table, "COLUMNS": _ssp_schema_columns},
                     indent=2, default=str))
