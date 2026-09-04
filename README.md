Yes — this screenshot gives us the key clue.

For system-security-plan itself you have:

2,813 duplicate keys

5,626 rows involved


And your Cell 5 source count was also 5,626.

That is an almost perfect signal that every SSP root is being created twice: 2,813 unique SSPs × 2 = 5,626 rows. So this is not a props[] problem yet. The duplication starts at the root.

We need to determine just one thing: is source_df already duplicated, or is Cell 5 creating each root twice?

Run only this read-only check:

from snowflake.snowpark import functions as F

print("TOTAL SOURCE ROWS =", source_df.count())

print(
    "DISTINCT SOURCE_RECORD_ID =",
    source_df.select("SOURCE_RECORD_ID").distinct().count()
)

print("=== DUPLICATE SOURCE RECORD IDS ===")

(
    source_df
    .group_by("SOURCE_RECORD_ID")
    .agg(F.count("*").alias("ROW_COUNT"))
    .filter(F.col("ROW_COUNT") > 1)
    .sort(F.col("ROW_COUNT").desc())
    .show(20)
)

What I expect

If it says:

TOTAL SOURCE ROWS = 5626
DISTINCT SOURCE_RECORD_ID = 2813

then we have found the upstream issue: source_df itself is duplicated 2×, and we fix Cell 2/source loading — not Cell 5 or Cell 6.

If distinct is 5626, then Cell 5 is creating the root twice, and we'll inspect that next.

Run only this. Don't change anything yet. Your screenshot narrowed the problem down a lot.