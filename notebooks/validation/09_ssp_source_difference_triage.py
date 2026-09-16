# SSP Validation 09 - triage wide-table / live RAW / frozen CURATED_JSON differences
# 2026-09-16. READ ONLY. Run in the existing successful SSP PREVIEW session.
#
# Purpose:
#   Validation 08 proved CURATED_JSON -> OSCAL mapping passes for sampled records,
#   while the wide Authorization Package table can differ from CURATED_JSON.
#   This diagnostic separates three states for those source differences:
#     1) frozen PREVIEW CURATED_JSON differs from the current live RAW CURATED_JSON,
#        which indicates the notebook preview is stale relative to the live RAW row;
#     2) frozen PREVIEW CURATED_JSON equals live RAW CURATED_JSON, while the wide table
#        differs, which points to wide-table vs RAW transformation/snapshot semantics;
#     3) normalization-equivalent or complex representations that should not be treated
#        as direct value mismatches.
#
# This script does NOT change the mapper and does NOT prove which upstream source is
# authoritative. It only provides evidence needed to classify the discrepancy safely.

import datetime as _v09_datetime
import html as _v09_html
import json as _v09_json
from decimal import Decimal as _v09_Decimal
from collections import Counter as _v09_Counter, defaultdict as _v09_defaultdict
from snowflake.snowpark import functions as _v09_F

_V09_WIDE_TABLE = 'RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE'
_V09_WIDE_ID_COLUMN = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONTENT_ID'
_V09_SOURCE_RECORD_IDS = ('7344415',)


def _v09_require(condition, message):
    if not condition:
        raise ValueError(message)


def _v09_python(value):
    if hasattr(value, 'as_dict'):
        return value.as_dict(recursive=True)
    if hasattr(value, 'as_list'):
        return value.as_list()
    return value


def _v09_json_obj(value):
    value = _v09_python(value)
    if isinstance(value, str):
        value = _v09_json.loads(value)
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object')
    return value


def _v09_source_value(source, field):
    if field in source:
        return source[field]
    current = source
    for token in str(field).replace('/', '.').split('.'):
        if not token:
            continue
        if isinstance(current, dict):
            current = current.get(token, current.get(token.upper()))
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return None
    return current


def _v09_scalar_normalize(value):
    value = _v09_python(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, _v09_datetime.datetime):
        text = value.isoformat(sep=' ')
        return text.rstrip('0').rstrip('.') if '.' in text else text
    if isinstance(value, _v09_datetime.date):
        return value.isoformat()
    if isinstance(value, _v09_Decimal):
        return format(value.normalize(), 'f')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return format(_v09_Decimal(str(value)).normalize(), 'f')
        except Exception:
            return str(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith('\\u') or '&' in text:
            try:
                text = _v09_html.unescape(text)
                text = text.encode('utf-8').decode('unicode_escape')
            except Exception:
                pass
        if len(text) >= 19 and text[4:5] == '-' and text[7:8] == '-' and text[10:11] in {'T', ' '}:
            text = text[:10] + ' ' + text[11:]
            if '.' in text:
                text = text.rstrip('0').rstrip('.')
        return text
    raise TypeError('Non-scalar source value')


def _v09_compare(a, b):
    a, b = _v09_python(a), _v09_python(b)
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        try:
            return 'MATCH' if _v09_json.dumps(a, sort_keys=True, default=str) == _v09_json.dumps(b, sort_keys=True, default=str) \
                else 'COMPLEX_REPRESENTATION_DIFFERENCE'
        except Exception:
            return 'COMPLEX_REPRESENTATION_DIFFERENCE'
    try:
        x, y = _v09_scalar_normalize(a), _v09_scalar_normalize(b)
    except TypeError:
        return 'COMPLEX_REPRESENTATION_DIFFERENCE'
    if x == y:
        return 'MATCH'
    if x and y and len(x) >= 10 and len(y) == 10 and x[:10] == y:
        return 'NORMALIZATION_EQUIVALENT'
    if x and y and len(y) >= 10 and len(x) == 10 and y[:10] == x:
        return 'NORMALIZATION_EQUIVALENT'
    return 'DIFFERENT'


def run_ssp_validation_09(namespace):
    required = ('session', 'SELECTED_MODELS', 'CONFIG', 'SOURCE_INPUTS', 'MAPPING_CONTEXTS')
    _v09_require(all(k in namespace for k in required), 'Existing SSP session is incomplete')
    _v09_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    _v09_require(namespace['CONFIG'].get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')

    contexts = [c for c in namespace['MAPPING_CONTEXTS'] if c.get('config', {}).get('OSCAL_MODEL') == 'SSP']
    _v09_require(len(contexts) == 1, 'Need exactly one current SSP context')
    context = contexts[0]
    approved = [r for r in context['mapping_rows'] if r.get('EXECUTION_STATUS') == 'APPROVED'
                and str(r.get('OSCAL_MODEL') or '').upper().startswith('SSP')]
    fields = sorted({r['SOURCE_FIELD_NAME'] for r in approved if r.get('SOURCE_FIELD_NAME')})

    source_key = context['source_key']
    frozen_df = namespace['SOURCE_INPUTS'][source_key]['source_df']
    wanted = tuple(str(x) for x in _V09_SOURCE_RECORD_IDS)

    frozen_rows = {}
    for row in frozen_df.filter(_v09_F.col('SOURCE_RECORD_ID').cast('string').isin(list(wanted))) \
                        .select('SOURCE_RECORD_ID', 'CURATED_JSON').to_local_iterator():
        frozen_rows[str(row['SOURCE_RECORD_ID'])] = _v09_json_obj(row['CURATED_JSON'])

    raw_table = context['config']['RAW_TABLE']
    raw_id_col = context['config'].get('CONTENT_ID_COLUMN', 'CONTENT_ID')
    raw_json_col = context['config'].get('CURATED_JSON_COLUMN', 'CURATED_JSON')
    raw_df = namespace['session'].table(raw_table)
    raw_cols = {str(c).strip('"').upper(): c for c in raw_df.columns}
    _v09_require(raw_id_col.upper() in raw_cols and raw_json_col.upper() in raw_cols,
                 'Live RAW table lacks expected CONTENT_ID or CURATED_JSON columns')

    live_raw_rows = {}
    live = raw_df.filter(_v09_F.trim(_v09_F.col(raw_cols[raw_id_col.upper()])).cast('string').isin(list(wanted)))
    for row in live.select(
        _v09_F.trim(_v09_F.col(raw_cols[raw_id_col.upper()])).cast('string').alias('SOURCE_RECORD_ID'),
        _v09_F.col(raw_cols[raw_json_col.upper()]).alias('CURATED_JSON')
    ).to_local_iterator():
        live_raw_rows[str(row['SOURCE_RECORD_ID'])] = _v09_json_obj(row['CURATED_JSON'])

    wide_df = namespace['session'].table(_V09_WIDE_TABLE)
    wide_cols = {str(c).strip('"').upper(): c for c in wide_df.columns}
    _v09_require(_V09_WIDE_ID_COLUMN in wide_cols, 'Wide table ID column is missing')
    mapped_wide = {field: wide_cols[field.upper()] for field in fields if field.upper() in wide_cols}

    wide_rows = {}
    wide = wide_df.filter(_v09_F.trim(_v09_F.col(wide_cols[_V09_WIDE_ID_COLUMN])).cast('string').isin(list(wanted)))
    select_cols = [_v09_F.trim(_v09_F.col(wide_cols[_V09_WIDE_ID_COLUMN])).cast('string').alias('SOURCE_RECORD_ID')]
    select_cols += [_v09_F.col(actual).alias(field) for field, actual in mapped_wide.items()]
    for row in wide.select(*select_cols).to_local_iterator():
        wide_rows[str(row['SOURCE_RECORD_ID'])] = row.as_dict(recursive=True)

    counts = _v09_Counter()
    details = []
    per_record = _v09_defaultdict(_v09_Counter)

    for sid in wanted:
        frozen = frozen_rows.get(sid)
        live_raw = live_raw_rows.get(sid)
        wide_row = wide_rows.get(sid)
        if frozen is None:
            counts['MISSING_FROZEN_PREVIEW_ROW'] += 1
            continue
        if live_raw is None:
            counts['MISSING_LIVE_RAW_ROW'] += 1
            continue
        if wide_row is None:
            counts['MISSING_WIDE_ROW'] += 1
            continue

        frozen_vs_live = _v09_compare(frozen, live_raw)
        if frozen_vs_live != 'MATCH':
            counts['FROZEN_PREVIEW_DIFFERS_FROM_LIVE_RAW'] += 1
            per_record[sid]['FROZEN_PREVIEW_DIFFERS_FROM_LIVE_RAW'] += 1

        for field in mapped_wide:
            wide_value = wide_row.get(field)
            frozen_value = _v09_source_value(frozen, field)
            live_value = _v09_source_value(live_raw, field)
            wide_vs_frozen = _v09_compare(wide_value, frozen_value)
            wide_vs_live = _v09_compare(wide_value, live_value)
            frozen_vs_live_field = _v09_compare(frozen_value, live_value)

            if wide_vs_frozen == 'MATCH':
                classification = 'MATCH'
            elif wide_vs_frozen == 'NORMALIZATION_EQUIVALENT':
                classification = 'EXPECTED_NORMALIZATION'
            elif wide_vs_frozen == 'COMPLEX_REPRESENTATION_DIFFERENCE':
                classification = 'COMPLEX_REPRESENTATION_REVIEW'
            elif frozen_vs_live_field != 'MATCH':
                classification = 'PREVIEW_STALE_OR_RAW_CHANGED'
            elif wide_vs_live in {'MATCH', 'NORMALIZATION_EQUIVALENT'}:
                classification = 'PREVIEW_STALE_OR_RAW_CHANGED'
            else:
                classification = 'WIDE_VS_RAW_SOURCE_DIFFERENCE'

            counts[classification] += 1
            per_record[sid][classification] += 1
            if classification != 'MATCH':
                details.append({
                    'SOURCE_RECORD_ID': sid,
                    'FIELD': field,
                    'CLASSIFICATION': classification,
                    'WIDE_VALUE': _v09_python(wide_value),
                    'FROZEN_CURATED_JSON_VALUE': _v09_python(frozen_value),
                    'LIVE_RAW_CURATED_JSON_VALUE': _v09_python(live_value),
                    'WIDE_VS_FROZEN': wide_vs_frozen,
                    'WIDE_VS_LIVE_RAW': wide_vs_live,
                    'FROZEN_VS_LIVE_RAW': frozen_vs_live_field,
                })

    return {
        'VALIDATION': '09_SSP_SOURCE_DIFFERENCE_TRIAGE',
        'VALIDATOR_VERSION': '2026-09-16-r1',
        'STATUS': 'DIAGNOSTIC_COMPLETE',
        'SOURCE_RECORD_IDS': list(wanted),
        'WIDE_SOURCE_TABLE': _V09_WIDE_TABLE,
        'LIVE_RAW_TABLE': raw_table,
        'APPROVED_SSP_FIELDS': len(fields),
        'APPROVED_FIELDS_PRESENT_IN_WIDE_TABLE': len(mapped_wide),
        'CLASSIFICATION_COUNTS': dict(sorted(counts.items())),
        'PER_RECORD_COUNTS': {k: dict(v) for k, v in per_record.items()},
        'DIFFERENCE_DETAILS': details,
        'INTERPRETATION': {
            'EXPECTED_NORMALIZATION': 'Representation changed in an expected way; not evidence of bad source data.',
            'COMPLEX_REPRESENTATION_REVIEW': 'Wide display value and CURATED_JSON structure need lookup-aware comparison.',
            'PREVIEW_STALE_OR_RAW_CHANGED': 'Frozen notebook CURATED_JSON differs from the current live RAW row; rerun/rebuild preview before judging.',
            'WIDE_VS_RAW_SOURCE_DIFFERENCE': 'Frozen and live RAW agree, but the wide source differs; investigate upstream wide-table vs RAW lineage/refresh/normalization.',
        },
        'NOTES': [
            'This diagnostic does not modify OSCAL mappings.',
            'Validation 08 already establishes CURATED_JSON -> OSCAL PASS for the sampled record when OSCAL_FAILURE_COUNTS is empty.',
            'This script does not decide which upstream representation is authoritative.',
            'Use owner/source-team evidence before changing upstream logic or mapping semantics.',
        ],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


SSP_VALIDATION_09_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_09_REPORT = run_ssp_validation_09(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v09_error:
        SSP_VALIDATION_09_REPORT = {
            'VALIDATION': '09_SSP_SOURCE_DIFFERENCE_TRIAGE',
            'STATUS': 'BLOCKED',
            'REASON': str(_v09_error),
            'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 09 ===')
    print(_v09_json.dumps(SSP_VALIDATION_09_REPORT, indent=2, default=str))
