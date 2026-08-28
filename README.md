Good — that narrows it down a lot.

If ELEMENT_JSON for components[].component is empty, then the deeper nodes cannot be built from that parent payload. So the issue is not activation and not the graph validator. It’s that the component node itself has no usable payload feeding child extraction.

Next step only: inspect the raw Archer fields that map to the component branch for a few source records.

Run this read-only cell:

from snowflake.snowpark.functions import col

component_fields = [
    "SUBSYSTEMS",
    "SOFTWARE",
    "HARDWARE",
    "INTERCONNECTIONS",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM",
    "SAP_INTAKE_FORM_INTERCONNECTIONS"
]

for record in source_df.limit(5).to_local_iterator():
    print("\nSOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])

    obj = _parse_source_json(record)

    for field in component_fields:
        value = resolve_json_path(obj, field)
        print(field, "=>", value)

What I need from the output is whether those six fields contain:

IDs/references only,

dictionaries,

arrays,

or empty/null values.


That tells us whether components[] should be built from reference IDs or whether we must follow those references into another Archer raw table.