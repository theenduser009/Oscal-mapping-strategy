# Source One upstream reconciliation prepared — 2026-09-28

## Repository version and supersession
- Repository: theenduser009/Oscal-mapping-strategy
- Branch: simplify-metadata-boundary
- Starting head inspected: 2d3610bac3efe33b2ba29638899bf3e3dc0ed0cd
- QA SQL commit: b6f4a29cb4bf2ecbdd97c965274ab14a80273dfe
- QA SQL blob, verified against locally prepared bytes: 37da0624df1d9cf02b54c32277541ccd4413bfa5

This supersedes the column-identification gap in the earlier September 28 upstream-validation checkpoint. Existing conversion SQL already identified RAW_DATA; the owner's live column-inventory screenshot confirms RAW_DATA VARIANT, CURATED_JSON VARIANT, and CONTENT_ID TEXT in RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW. Column discovery is closed. The screenshot and private sample record identifier remain in the Project conversation, not GitHub.

This does not supersede the September 25 per-model committed/read-back checkpoints or claim a new database run. The previously confirmed four executable Source One routes remain distinct from this upstream QA task. Historical handoff deferral counts must not be substituted for newer mapping decisions.

## Actual sources inspected
- sql/matillion/READ_ONLY_authorization_package_full_conversion_preview.sql — blob 2a58200961eb65625c04108b3783959e87ee107b.
- sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql — blob 89793be25352cdd5292a7ab512403bd074ce9830.
- sql/matillion/READ_ONLY_raw_curated_values_preview.sql — blob f9dbd8be15e33ebebad2c42530c70eff0da0ace0.
- Existing OSCAL-only integrated QA was inspected for its downstream-only boundary; it does not validate raw-to-curated conversion.

The saved Matillion conversion is explicitly a review candidate, not proof of the exact deployed component version. A new query must therefore report differences against the saved reference without automatically declaring every difference a production defect.

## Added deliverable
[Run this complete read-only SQL](../../sql/qa/SOURCE_ONE_RAW_CURATED_RECONCILIATION_2026-09-28.sql).

It reads the full current Authorization Package table and ARCHER_META_FIELD in one SELECT statement. It returns 29 aggregate checks plus an overall comparison status, with an execution timestamp and no business values or record IDs. It requires no substitutions, prior query results, session variables, temporary tables, DDL, DML, or notebook execution.

Coverage includes source/compared/uncompared record counts; raw and curated shapes; raw and derived ID nulls/duplicates; field metadata ties and conflicting output names; combined top-level/nested key collisions; conversion-to-null observations; fallback and lower-priority mapping counts; unmapped nested candidates; missing populated/null-valued keys; unexpected stored keys; exact type/value comparison; derived CONTENT_ID comparison; and an independent raw-JSON-null-to-populated-value check.

Recorded conversion rules are retained for unambiguous inputs. QA-only safe identifier casts and shape guards report malformed inputs rather than allowing strict casts to abort discovery of other issues. DENSE_RANK exposes ordering ties rather than choosing arbitrary tied winners. Blocked records remain counted as not compared. Reference precedence exclusions are reported, not silently hidden.

Identity is compared using the saved COALESCE precedence; raw RequestedObject.Id is not assumed to equal derived CONTENT_ID. The reference's numeric scale and session-dependent date/timestamp parsing are unchanged. This comparison is not approval of those business rules.

## Validation actually performed
- Direct GitHub branch/source inspection.
- Static safety checks passed: one statement, read-only token allowlist, balanced quotes/parentheses, exactly the two intended physical tables, no placeholders, and no private sample identifier.
- Fifteen independent synthetic field-classification examples passed, including null versus missing, zero versus false, string versus number, object-key ordering, and array order.
- Five independent overall-status examples passed, including empty source and partial coverage.
- These are static/design checks, NOT execution of the Snowflake SQL.
- Snowflake compilation and live data execution: NOT PERFORMED. No Snowflake plugin was returned by the capability search in this chat.
- A standalone SQL parser was not available; installing one failed because network name resolution was unavailable. No parser or engine validation is claimed.
- GitHub read-back returned the same blob SHA as the complete locally prepared SQL.

Only QA SQL and this checkpoint are added. No production converter, mapper cell, CSV mapping, registry, DIM/FACT table, or data was modified.

## Immediate next action
Run the complete SQL once in Snowflake and return its aggregate result grid. Review BLOCKED/REVIEW rows before any correction; no UPDATE, reload, or repeat COMMIT is authorized by this QA script.

MATCHED_SAVED_REFERENCE means eligible current rows matched that saved conversion reference. It is not full end-to-end QA sign-off, proof of Matillion deployment, proof of vendor-file completeness, or OSCAL document conformance. Field-level CURATED_JSON-to-OSCAL mapping reconciliation, full graph checks, and final scope sign-off remain separate QA gates.
