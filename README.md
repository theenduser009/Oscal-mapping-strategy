# OSCAL Mapping Strategy — Current SSP Step

## Where to look

For now, use **this README as the single source for the immediate next action**. Do not jump between `docs/`, `notebooks/`, SSP progress, or evidence files unless this README points you there.

## Current confirmed state

The SSP graph build is producing duplicate node and edge keys, but the graph builder itself is not yet proven to be the root cause.

Confirmed from the notebook:

- `source_df.count()` = **5,626**
- distinct `SOURCE_RECORD_ID` = **2,813**
- every sampled duplicate `SOURCE_RECORD_ID` appears **2 times**
- Cell 5 built **99,300 nodes** and **93,674 edges**
- Cell 6 correctly blocked DIM/FACT writes because duplicate keys were detected

This strongly indicates that `source_df` is already duplicated before Cell 5 graph construction.

## Important safety rule

Keep:

```python
EXECUTE_WRITES = False
```

Do **not** modify Cells 4, 5, or 6 yet. Do **not** enable writes.

## Immediate next step — run this SQL only

We now need to determine whether the duplicate records already exist in the physical Archer raw table or whether Cell 2 creates the duplication while building `source_df`.

Run:

```sql
SELECT
    COUNT(*) AS RAW_ROWS,
    COUNT(DISTINCT CONTENT_ID) AS DISTINCT_CONTENT_IDS
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW;
```

## How to interpret the result

If the result is approximately:

```text
RAW_ROWS = 5626
DISTINCT_CONTENT_IDS = 2813
```

then the **raw table itself contains each authorization package twice**. We will inspect why the raw load duplicated rows before changing notebook logic.

If the result is approximately:

```text
RAW_ROWS = 2813
DISTINCT_CONTENT_IDS = 2813
```

then the **raw table is clean and Cell 2/source loading is duplicating the data**. The next step will be to inspect Cell 2 only.

## Stop point

After running the SQL above, send back only:

```text
RAW_ROWS = ...
DISTINCT_CONTENT_IDS = ...
```

Do not make any code changes before that result is reviewed.
