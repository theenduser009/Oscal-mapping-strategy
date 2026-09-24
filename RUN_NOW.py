# RUN NOW — Diagnose Source One zero-row frozen snapshot
# Date: 2026-09-24
# READ ONLY. No source, registry, DIM, FACT, or mapping DML.
#
# Prior diagnostic showed:
#   SOURCE_SELECTED_ROWS = 0
#   GRAPH BUILD = FAILED
#   UNDERLYING_ERROR_MESSAGE = Graph builder produced no nodes
#
# This check compares the live RAW table with the frozen Cell-2 snapshot already
# present in SOURCE_INPUTS. It tells us whether Cell 2 captured the source while
# the truncate-and-load RAW table was temporarily empty, or whether the RAW table
# itself is currently empty.

SOURCE_KEY = "source-one"
RAW_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"

print("SOURCE_ONE_ZERO_ROW_SNAPSHOT_DIAGNOSTIC")

live = session.sql(f"""
SELECT
    COUNT(*) AS RAW_ROWS,
    COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS DISTINCT_CONTENT_IDS,
    COUNT_IF(CONTENT_ID IS NULL OR LENGTH(TRIM(CONTENT_ID::STRING)) = 0) AS NULL_OR_BLANK_CONTENT_IDS
FROM {RAW_TABLE}
""").collect()[0]

print("LIVE_RAW_ROWS =", live["RAW_ROWS"])
print("LIVE_DISTINCT_CONTENT_IDS =", live["DISTINCT_CONTENT_IDS"])
print("LIVE_NULL_OR_BLANK_CONTENT_IDS =", live["NULL_OR_BLANK_CONTENT_IDS"])

source = SOURCE_INPUTS.get(SOURCE_KEY)
if source is None:
    print("SOURCE_INPUT_PRESENT = False")
    print("RESULT: RERUN_CELL_2_REQUIRED")
else:
    print("SOURCE_INPUT_PRESENT = True")
    print("CELL2_SELECTION =", source.get("selection"))

    try:
        frozen_rows = source["source_df"].count()
    except Exception as error:
        frozen_rows = None
        print("FROZEN_SOURCE_DF_ERROR =", type(error).__name__, str(error))

    try:
        snapshot_rows = source["snapshot"].count()
    except Exception as error:
        snapshot_rows = None
        print("FROZEN_SNAPSHOT_ERROR =", type(error).__name__, str(error))

    print("FROZEN_SOURCE_DF_ROWS =", frozen_rows)
    print("FROZEN_SNAPSHOT_ROWS =", snapshot_rows)

    live_rows = int(live["RAW_ROWS"] or 0)

    if live_rows > 0 and frozen_rows == 0:
        print("RESULT: LIVE_RAW_REPOPULATED_RERUN_CELL_2_THEN_3_AND_7")
    elif live_rows == 0:
        print("RESULT: LIVE_RAW_CURRENTLY_EMPTY_WAIT_FOR_SOURCE_LOAD")
    elif frozen_rows == live_rows:
        print("RESULT: FROZEN_SOURCE_MATCHES_LIVE_RAW_RETRY_SSP_PREVIEW")
    else:
        print("RESULT: SOURCE_SNAPSHOT_COUNT_MISMATCH_REVIEW")
