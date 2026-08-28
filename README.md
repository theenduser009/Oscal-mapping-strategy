Yes — this result is very useful.

For record 565189, three things stand out immediately:

authorization-boundary has 1 owned mapping but payload is {} → the source value for that record is probably null/empty.

security-impact-level has 12 owned mappings but payload is {} → same story for this record, or the mapped source fields are not present/populated.

status is working and produced state: [80661].

system-ids[] is working and produced an id.

props[] is working, but the payload is still using Archer field names like PACKAGE_TYPE and PACKAGE_TYPE_HELPER_CALC, which confirms we need to handle extension-property semantics separately later.


So the mapper is not broadly broken. The branch is being built, but some child payloads are empty because this particular record does not carry those source values.

The best next step is not code change. We should find a record where AUTHORIZATION_BOUNDARY_DESCRIPTION and at least one security-impact source field are populated, then rerun the same child test against that one record.

Run this read-only SQL:

SELECT
    CONTENT_ID,
    CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION AS AUTH_BOUNDARY,
    CURATED_JSON:CNSS_CONFIDENTIALITY_RATING       AS CONFIDENTIALITY,
    CURATED_JSON:CNSS_INTEGRITY_RATING             AS INTEGRITY,
    CURATED_JSON:CNSS_AVAILABILITY_RATING          AS AVAILABILITY,
    CURATED_JSON:SECURITY_CATEGORY                  AS SECURITY_CATEGORY
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
WHERE
       CURATED_JSON:AUTHORIZATION_BOUNDARY_DESCRIPTION IS NOT NULL
    OR CURATED_JSON:CNSS_CONFIDENTIALITY_RATING IS NOT NULL
    OR CURATED_JSON:CNSS_INTEGRITY_RATING IS NOT NULL
    OR CURATED_JSON:CNSS_AVAILABILITY_RATING IS NOT NULL
    OR CURATED_JSON:SECURITY_CATEGORY IS NOT NULL
LIMIT 20;

Pick one CONTENT_ID from that result where several of those columns are populated.

Then we rerun the exact same payload test against that record.

That will tell us whether authorization-boundary and security-impact-level are functioning correctly before we touch any mapper logic.