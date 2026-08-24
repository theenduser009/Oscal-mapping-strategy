I caught the real issue. **Do not continue with this Cell 3 as written.** Nothing is damaged because it is read-only, but it found an important problem.

Your CSV loaded correctly. The actual 11 mapping columns are:

```text
ARCHER_FIELD_NAME
Sparx EA Mapping Completed
NULL%
DATA_TYPE
CARDINALITY
OSCAL_MODEL
OSCAL_ELEMENT_PATH
OSCAL_DATA_TYPE
MAPPING_TYPE
TRANSFORMATION_LOGIC
NOTES
```

But then Cell 3 did this:

```python
.filter(col("OSCAL_MODEL") == "SSP")
```

and the result is:

```text
Canonical mapping rows: 0
```

So `"SSP"` is **not the exact value stored in `OSCAL_MODEL`**. It may be something like `System Security Plan`, `System Security Plan (SSP)`, different casing, spaces, etc. We should inspect it instead of guessing.

There is also a second bug I want fixed now: this logic is wrong:

```python
has_node_type_col = any("TYPE" in c.upper() ...)
```

because your CSV has:

```text
DATA_TYPE
OSCAL_DATA_TYPE
MAPPING_TYPE
```

Those contain `"TYPE"` but **none of them means ELEMENT_TYPE / NODE_TYPE**. So the AI incorrectly printed:

> `Sufficient columns found for basic registry derivation`

We absolutely should not let that become production logic.

### Next action only

Do **not** derive `element_registry_df` yet.

Replace the current Cell 3 with a much smaller **inspection version**. Tell the other AI:

> Stop the current Cell 3 derivation. It exposed two issues and we need to correct them before creating canonical metadata.
>
> Actual `mapping_df` columns are now confirmed:
>
> `ARCHER_FIELD_NAME`
> `Sparx EA Mapping Completed`
> `NULL%`
> `DATA_TYPE`
> `CARDINALITY`
> `OSCAL_MODEL`
> `OSCAL_ELEMENT_PATH`
> `OSCAL_DATA_TYPE`
> `MAPPING_TYPE`
> `TRANSFORMATION_LOGIC`
> `NOTES`
>
> The current filter `OSCAL_MODEL == CONFIG["OSCAL_MODEL"]` where CONFIG contains `"SSP"` returned **0 rows**.
>
> Therefore do NOT assume `"SSP"` is the value stored in the CSV.
>
> Also remove any logic such as:
>
> `any("TYPE" in column_name...)`
>
> for detecting a node/element type column. `DATA_TYPE`, `OSCAL_DATA_TYPE`, and `MAPPING_TYPE` are not node-type columns.
>
> For the next Cell 3 version, do READ-ONLY inspection ONLY.
>
> Print:
>
> 1. distinct non-null `OSCAL_MODEL` values with counts,
> 2. total non-null `OSCAL_ELEMENT_PATH` count,
> 3. first 25 distinct `OSCAL_ELEMENT_PATH` values,
> 4. distinct `CARDINALITY` values with counts,
> 5. first 15 rows containing only:
>
>    * `ARCHER_FIELD_NAME`
>    * `OSCAL_MODEL`
>    * `OSCAL_ELEMENT_PATH`
>    * `CARDINALITY`
>    * `MAPPING_TYPE`
>    * `TRANSFORMATION_LOGIC`
>
> Do NOT create `canonical_mapping_df` yet.
> Do NOT create `element_registry_df`.
> Do NOT infer node boundaries.
> Do NOT infer parent-child relationships.
> Do NOT modify CONFIG yet.
> Do NOT write anything.
>
> Show the inspection output and STOP.

This is one of those checks that **saves** us time rather than adds delay. We found the model filter mismatch before building the entire hierarchy on an empty dataframe.

And importantly, I have **not changed our architecture**: mapping CSV → canonical metadata → generic element registry → reusable nodes/relationships for all OSCAL elements. We are simply making sure Cell 3 interprets the actual mapping correctly before we freeze the metadata contract.
