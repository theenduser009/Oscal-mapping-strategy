# Owner-confirmed empty AR DIM: replacement DDL

September 13, 2026. In the current voice task, the owner explicitly confirmed
DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT is completely empty/truncated and requested
the updated DDL. This is owner-provided empty-table evidence; no live count was
queried from this workstation. The earlier row-count request is superseded.

[ddl](../../sql/ddl)
replaces that empty DIM with the exact ten-column shared SSP physical contract,
retaining AR's confirmed primary-key name. It fixes the four VARCHAR widths,
NTZ/TZ type and missing timezone audit column in one CREATE OR REPLACE statement.
It includes the existing primary-key constraint. FACT already matches and needs
no schema change. No mapper, mapping CSV, graph identity or registry change is
required. COPY GRANTS retains existing privileges except ownership; the executing
role owns the replacement. See [Snowflake CREATE TABLE](https://docs.snowflake.com/en/sql-reference/sql/create-table#copy-grants).

The owner confirmed the empty table and asked for this DDL, so do not request
another count/approval before delivering the agreed replacement. This script
is a one-time empty-table repair, not a daily load step; never rerun it on a
populated table. Publication is not evidence that the DDL has run in Snowflake.

Next: execute the SQL once outside an active transaction. With the successfully
built AR contexts still present from the failed Cell Seven attempt, set Cell
Seven to PREVIEW and rerun that cell. Require PREVIEW_PASSED_NO_TARGET_DML,
storage_verified and pre_write_validation_passed true. Then the authorized
COMMIT can be run in Cell Seven and must report COMMITTED_AND_VERIFIED with
actual DIM/FACT changes and committed readback. Rerun all seven only if earlier
inputs, model selection or session contexts changed. No unchanged SSP rerun or
registry reset is needed. Unknown commit outcomes require inspection before retry.

The owner saved the same DDL as sql/ddl in branch commit
b5962d137dc0ad0a6993214f5c3f361319fe9267. Independent review confirms it matches
all ten columns, types/nullability and the AR primary key expected by the loader.
Saving the DDL is not evidence that it has executed in Snowflake.
