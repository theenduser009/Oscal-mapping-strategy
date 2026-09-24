# Level-355 control-id blocker narrowed to one row — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `b57f1259c45227d0a98e5e12f7405a895e4b1b7f`

## Owner-provided live evidence
The corrected control-id check returned:
- MATCHED_ROWS = 127,496
- CONTROL_NUMBER_EFFECTIVE = 127,495
- CONTROL_NUMBER_MISSING = 1
- FEED_CONTROL_NUMBER_EFFECTIVE = 127,495
- CONTROL_NUMBER shapes = 127,495 VARCHAR + 1 NULL_VALUE
- graph build fails on CONTROL_NUMBER required mapping

The exact overlap between the one missing CONTROL_NUMBER row and alternative
control-number fields was not visible in the screenshot, so it must not be guessed.

## Next action
Root `RUN_NOW.py` now checks only whether the one missing CONTROL_NUMBER row is
covered by:
- FEED_CONTROL_NUMBER
- CONTROL_NUMBER_ONLY

It prints aggregate counts only and performs no graph build or writes.
