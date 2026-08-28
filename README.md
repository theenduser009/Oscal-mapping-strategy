I’d not activate system-implementation or add control-implementation nodes yet.

Since control-implementation has zero mappings, the safest next move is to let the Archer data tell us which SSP branch is actually supported. The inactive registry flag is useful here—it prevents the mapper from manufacturing structure we haven’t proven.

Run one read-only inventory query against CURATED_JSON across the Authorization Package table:

SELECT
    f.value::STRING AS ARCHER_FIELD,
    COUNT(*) AS RECORD_COUNT
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW a,
LATERAL FLATTEN(INPUT => OBJECT_KEYS(a.CURATED_JSON)) f
GROUP BY f.value::STRING
ORDER BY RECORD_COUNT DESC, ARCHER_FIELD;

This will give us the actual Archer fields and how commonly they occur.

Then we can classify them against the official SSP branches:

metadata
import-profile
system-characteristics
system-implementation
control-implementation
back-matter

My decision: keep everything inactive/unchanged for now, inspect the raw field inventory first, and then choose the strongest NIST SSP branch supported by real data. That avoids another long detour like the Hardware/component branch.

Send me that output and I’ll tell you exactly which branch I would tackle next.