# Security Assessment Plan — three-field mapping

## What is enabled

The owner requested all three reviewed Source One Assessment Plan fields.
The existing source is ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW.CURATED_JSON.

| Archer field | Clean OSCAL path | Conversion |
| --- | --- | --- |
| REQUEST_TO_BEGIN_ASSESSMENT | assessment-plan.tasks[].props[] | Resolve the single Archer picklist ID to its existing label; property name request-to-begin-assessment. |
| APPROVAL_TO_BEGIN_ASSESSMENT | assessment-plan.tasks[].props[] | Resolve the single Archer picklist ID to its existing label; property name approval-to-begin-assessment. |
| PREASSESSMENT_REVIEW_COMMENTS | assessment-plan.tasks[].remarks | Preserve source text, including whitespace, or explicit JSON null. |

The [NIST OSCAL 1.2.3 Assessment Plan root](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_assessment-plan_metaschema.xml)
is assessment-plan. Its [task definition](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_assessment-common_metaschema.xml)
allows properties and remarks, and requires UUID, type and title.
The workbook's original security-assessment-plan prefix is retained in each
CSV execution note; both executable and visible paths now use the clean path.

One record-scoped task is titled **Preassessment review**, with type **action**.
Two labelled CONFIG support rows supply these structural members. They are
not additional source fields: Cell Three selects five rows, representing three
source mappings and two support mappings. No status, timing, dependencies,
approval meaning, dates, people or extra source values are inferred.

## Storage shape and null behavior

Each source record gets its own root and task, even when all three keys are
absent. Request and approval properties have separate DIM rows linked to the
task through FACT CONTAINS edges, as with existing SSP property collections.
They do not appear inline in the task's METADATA_JSON; join the FACT links to
read the child property rows. Comments are inside the task JSON as remarks.

NULL_POLICY=preserve applies only to these three CSV rows. An explicitly present
null survives; an absent key is omitted. Empty strings/containers remain omitted.
Unknown picklist IDs, multiple selected labels and invalid populated comment
shapes stop the run. Labels come from the already configured ARCHER_META_VALUE
lookup. The screenshots do not establish those label meanings.

The properties operator now accepts the registry's SOURCE_FIELD_NAME identity
with ITEM_PATH=$ for single-value fields. Null-to-value changes update the same
property hash and UUID; the task/root identities and FACT links also remain
stable. Existing SSP value-based property identity is unchanged. No new graph
operator or loader is added.

This is a partial warehouse mapping. Full OSCAL document export is still
incomplete: metadata, import-ssp and reviewed-controls are not supplied by these
three mappings. Explicit null property values/remarks are retained for the
warehouse and need a separate export policy for strict OSCAL string members.
FULL_MODEL_COMPLETE and SCHEMA_VALIDATED remain false.

## Prepare and run the first preview

Use the same simplification branch and seven-cell notebook.

1. In a Snowflake SQL worksheet outside a transaction, run
   [CREATE_ASSESSMENT_PLAN_TABLES.sql](../sql/CREATE_ASSESSMENT_PLAN_TABLES.sql).
   It creates missing targets only, using the existing SSP/AR ten-column DIM
   and six-column FACT layout. It does not replace or repair existing tables.
2. Run the complete [Assessment Plan registry SQL](../sql/registry/ENABLE_ASSESSMENT_PLAN_METADATA.sql).
   Success is SAP_METADATA_VERIFIED with three active rows. The statement
   configures root, tasks and properties; it retires only unconfigured legacy
   SAP paths and the unconfigured remarks leaf. It changes no registry columns
   or other models. Conflicting configured metadata stops before acceptance.
3. Upload the updated [mapping CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
   Replace [Cell One](../notebooks/cells/01_initialization_and_configuration.py),
   [Cell Three](../notebooks/cells/03_canonical_mapping_contract.py), and
   [Cell Four](../notebooks/cells/04_parsing_transform_payload_helpers.py).
   The other four cells stay as in the current package.
4. Select the existing registry model key and run all seven cells:

~~~python
# Cell One
SELECTED_MODELS = ("SECURITY_ASSESSMENT_PLAN",)

# Cell Seven
OSCAL_LOAD_MODE = "PREVIEW"
~~~

Keep CONFIG["EXECUTE_WRITES"] false. Cell Three must report READY with five
selected rows. Cell Seven must report PREVIEW_COMPLETE and the selected group's
PREVIEW_PASSED_NO_TARGET_DML, with graph/storage checks passed and no writes.
The live source determines the property count; do not assume both keys exist
in every record. Review that first preview before the initial COMMIT.

The targets in RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED are:

| Table | Primary key |
| --- | --- |
| DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT | PK_DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT_HASH |
| FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY | PK_FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY_HASH |

VERIFIED in Cell One selects the shared physical contract. It is not evidence
that these tables already exist or have passed a live run; Cell Six inspects the
actual schema before target DML. No live setup or SAP write has been performed
by this release.

## Validation

The local suite passed 216 tests with three unavailable-Snowpark class skips.
Ten focused Assessment Plan tests cover exact mappings, lookup errors, nulls
versus missing keys, record ownership, stable identities, and the shared
relational loader's preview/insert/update/readback/unchanged retry.
Existing SSP/AR/POAM regression checks pass. The seven-cell runtime is 1,903
lines, a net increase of 28 lines, with matching Cell Three/Four release
lean-csv-registry-v4. Generated copy pages match the maintained cells.

All three relevant private screenshot excerpts were tested separately with
synthetic source-record IDs. Request and approval each produced three nodes
and two edges; the null-comment excerpt produced two nodes and one edge.
Graph checks and null/value identity transitions passed. Lookup labels in
those tests were explicitly synthetic; actual Archer lookup meanings and live
source coverage remain unverified. No private source values are published.

The registry preflight and retirement predicates passed the review's 13 local
scenarios. This is not live Snowflake scripting, MERGE or transaction acceptance.
The CI package also includes a full seven-cell Assessment Plan test with
installed Snowpark and the local SQL adapter. Its result is recorded below
after execution.
