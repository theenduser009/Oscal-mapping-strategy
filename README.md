Yes — good catch. The Snowpark column syntax you used is the right syntax in your notebook:

col("CURATED_JSON")["HARDWARE"]

But there’s a second issue: your filter found a row, yet this line:

source_obj.get("HARDWARE")

printed null.

That means we should use the same resolver our mapper uses, not Python .get(), because Archer key naming/casing can differ.

Replace only this line:

print(json.dumps(source_obj.get("HARDWARE"), indent=2, default=str))

with:

hardware_value = resolve_json_path(
    source_obj,
    "HARDWARE"
)

print(
    json.dumps(
        hardware_value,
        indent=2,
        default=str
    )
)

So the bottom of your test becomes:

record = rows[0]

source_obj = _parse_source_json(record)

hardware_value = resolve_json_path(
    source_obj,
    "HARDWARE"
)

print(
    "SOURCE_RECORD_ID:",
    record["SOURCE_RECORD_ID"]
)

print("\nHARDWARE:")

print(
    json.dumps(
        hardware_value,
        indent=2,
        default=str
    )
)

Run that first.

If it still says null, don’t change any production code. Then we’ll inspect the actual keys in that one CURATED_JSON record and find exactly how HARDWARE is represented.

And yes — I’ll keep the Snowpark syntax you just confirmed:

col("CURATED_JSON")["FIELD_NAME"]

rather than switching you back to a syntax that doesn’t match your environment.