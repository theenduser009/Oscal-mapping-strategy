Agreed. Cells 1–7 stay frozen. We work only in new SSP discovery cells.

Next step — inspect COMPONENTS

Add one new cell and run:

# ============================================================
# SSP — COMPONENTS Discovery
# READ ONLY
# ============================================================

samples = 0

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)

    components = resolve_json_path(
        source_obj,
        "COMPONENTS"
    )

    if components in (None, "", [], {}):
        continue

    print("\nSOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])
    print("TYPE:", type(components).__name__)
    print("COMPONENTS:", str(components)[:3000])

    samples += 1

    if samples >= 3:
        break

print("\nSamples found:", samples)

We need only one answer from this:

Does COMPONENTS contain actual component objects, or references like ContentId / LevelId?

Send me the output and we'll immediately take the next step.