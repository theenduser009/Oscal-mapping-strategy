# Assessment Results CSV execution-metadata correction

Date: **2026-09-13**

The canonical mapping CSV now enables the fifteen clean, owner-approved rows
whose original Excel target was the ambiguous literal
`assessment-results.results[].observations[] or props[]`.

For each enabled row:

- the original Excel path and Notes remain unchanged as provenance;
- `EXECUTION_STATUS` is `APPROVED`;
- `TRANSFORM_ID` is `scalar-score`;
- `RUNTIME_TARGET_PATH` is `assessment-results.results[].observations[]`;
- the emitted observation contains one named inline `props[]` value.

This produces **32 executable Assessment Results mappings**: 17 previously
accepted fields plus 15 newly enabled fields.

The following ambiguous rows remain deferred and have no executable runtime
path:

- `RISK_ACCEPTANCE_RBDS` — reference-shaped source value;
- `TOTAL_PACKAGE_INHERENT_RISK` — unresolved Notes conflict;
- `RISK_ASSESSMENT_REPORT` — attachment/reference meaning is not a scalar score.

The seven result-level workflow properties, duplicate Average Security
Compliance Score rows, and `FINDINGS` remain deferred. No SSP mapping or OSCAL
registry row changed.

Validation: all **701** local unit tests passed. No Snowflake query, preview,
target DML, or database write was performed by this repository change.
