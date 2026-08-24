Cell 2 is **mostly right**, but I would make **two corrections now before we approve it**. They matter for the reusable design.

The source part is good:

```python
source_df = session.table(CONFIG["RAW_TABLE"]).select(
    col("CONTENT_ID").alias("SOURCE_RECORD_ID"),
    col("CURATED_JSON")
)
```

That gives the clean runtime contract we wanted:

```text
SOURCE_RECORD_ID
CURATED_JSON
```

### Correction 1 — don’t hardcode the mapping filename

Right now it has:

```python
pd.read_csv("archer_to_oscal_mapping (4).csv", ...)
```

That would make the engine dependent on one particular uploaded filename. Since the CSV is our mapping source of truth, the location should come from CONFIG.

Add to Cell 1:

```python
"MAPPING_FILE": "archer_to_oscal_mapping (4).csv",
```

Then Cell 2 uses:

```python
mapping_artifact_pdf = pd.read_csv(
    CONFIG["MAPPING_FILE"],
    encoding="cp1252",
    dtype=str
)
```

Later we can change the mapping location without rewriting Cell 2.

### Correction 2 — remove `astype(str)`

This line is dangerous:

```python
mapping_artifact_pdf = mapping_artifact_pdf.astype(str)
```

Because blank CSV values become literal strings such as:

```text
"nan"
```

Then later the engine may think `"nan"` is a real mapping value.

Instead use:

```python
mapping_artifact_pdf = pd.read_csv(
    CONFIG["MAPPING_FILE"],
    encoding="cp1252",
    dtype=str
)

mapping_artifact_pdf = mapping_artifact_pdf.where(
    mapping_artifact_pdf.notna(),
    None
)
```

That gives us:

```text
real value → string
blank value → None
```

which is what we want before canonical normalization.

Then:

```python
artifact_columns = list(mapping_artifact_pdf.columns)

mapping_df = session.create_dataframe(
    mapping_artifact_pdf.values.tolist(),
    schema=artifact_columns
)
```

is fine for now.

### Also simplify the validation

We don't need to dump `CURATED_JSON` from:

```python
source_df.show(1)
```

That can print a huge record and starts us down the old validation rabbit hole.

For Cell 2, I only want:

```python
print(f"SOURCE RECORDS: {source_df.count()}")
print(f"MAPPING ROWS: {mapping_df.count()}")

print("SOURCE COLUMNS:", source_df.columns)
print("MAPPING COLUMNS:", mapping_df.columns)
```

That's enough.

### Tell the other AI exactly this

> Cell 2 is almost approved. Make ONLY these corrections:
>
> 1. Do not hardcode `"archer_to_oscal_mapping (4).csv"` inside Cell 2. Add `"MAPPING_FILE"` to CONFIG and reference `CONFIG["MAPPING_FILE"]`.
>
> 2. Remove `mapping_artifact_pdf.astype(str)` because it converts null/NaN values into the literal string `"nan"`.
>
> Read the CSV using `dtype=str`, then preserve missing values as Python `None` using:
>
> `mapping_artifact_pdf = mapping_artifact_pdf.where(mapping_artifact_pdf.notna(), None)`
>
> 3. Keep creation of `mapping_df` as a raw/unprocessed Snowpark dataframe. Do not rename mapping columns, derive paths, filter SSP, or transform mappings yet.
>
> 4. Keep validation minimal. Print only source row count, mapping row count, source columns, and mapping columns. Do not display full `CURATED_JSON` records.
>
> 5. Do not create Cell 3 yet.
>
> Show corrected Cell 2 only and STOP.

And yes — this stays aligned with the dynamic architecture: **Cell 2 knows nothing about `metadata`, `system-security-plan`, `import-profile`, POA&M, components, props, etc.** It only loads source + mapping. That's exactly what we want.
