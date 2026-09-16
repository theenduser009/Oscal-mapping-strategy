# SSP Validation 08 - sample source-table / CURATED_JSON / OSCAL reconciliation
# 2026-09-16. READ ONLY. Run in the existing successful SSP PREVIEW session.
#
# Goal:
#   For selected SOURCE_RECORD_ID values, compare the current approved SSP mapping scope across:
#     1) the wide Authorization Package source table,
#     2) the frozen CURATED_JSON used by Source 1,
#     3) the generated OSCAL candidate graph.
#
# IMPORTANT:
#   Wide-table vs CURATED_JSON differences are SOURCE SNAPSHOT / NORMALIZATION diagnostics.
#   They do NOT by themselves fail OSCAL mapping validation. The mapper actually consumes
#   CURATED_JSON, so pass/fail is determined by CURATED_JSON -> expected OSCAL -> actual OSCAL.
#
# This validator is mapping-driven. It does NOT compare all ~610 source columns blindly; it compares
# only source fields that are currently APPROVED SSP mappings and physically exist in the wide table.
# Complex/list source values are reported separately when direct wide-column equality is not safe.

import datetime as _v08_datetime
import json as _v08_json
import html as _v08_html
from decimal import Decimal as _v08_Decimal
from collections import Counter as _v08_Counter, defaultdict as _v08_defaultdict
from snowflake.snowpark import functions as _v08_F

_V08_WIDE_TABLE = 'RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE'
_V08_WIDE_ID_COLUMN = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONTENT_ID'
_V08_SOURCE_RECORD_IDS = ('7344415',)

_V08_NODE_COLUMNS = (
    'NODE_KEY', 'ELEMENT_PATH', 'PARENT_NODE_PATH', 'INSTANCE_KEY',
    'PARENT_INSTANCE_KEY', 'OSCAL_UUID', 'ELEMENT_TYPE', 'METADATA_JSON',
    'SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME', 'SOURCE_RECORD_ID', 'DW_PIPELINE_RUN_ID',
)


def _v08_require(condition, message):
    if not condition:
        raise ValueError(message)


def _v08_python(value):
    if hasattr(value, 'as_dict'):
        return value.as_dict(recursive=True)
    if hasattr(value, 'as_list'):
        return value.as_list()
    return value


def _v08_json_obj(value):
    value = _v08_python(value)
    if isinstance(value, str):
        value = _v08_json.loads(value)
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object')
    return value


def _v08_scalar_normalize(value):
    value = _v08_python(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, _v08_datetime.datetime):
        text = value.isoformat(sep=' ')
        return text.rstrip('0').rstrip('.') if '.' in text else text
    if isinstance(value, _v08_datetime.date):
        return value.isoformat()
    if isinstance(value, _v08_Decimal):
        return format(value.normalize(), 'f')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return format(_v08_Decimal(str(value)).normalize(), 'f')
        except Exception:
            return str(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith('\\u') or '&' in text:
            try:
                text = _v08_html.unescape(text)
                text = text.encode('utf-8').decode('unicode_escape')
            except Exception:
                pass
        if len(text) >= 19 and text[4:5] == '-' and text[7:8] == '-' and text[10:11] in {'T', ' '}:
            text = text[:10] + ' ' + text[11:]
            if '.' in text:
                text = text.rstrip('0').rstrip('.')
        return text
    raise TypeError('Non-scalar source value')


def _v08_source_value(source, field):
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


def _v08_compare_wide_to_curated(wide_value, curated_value):
    wide_value = _v08_python(wide_value)
    curated_value = _v08_python(curated_value)
    if isinstance(wide_value, (dict, list)) or isinstance(curated_value, (dict, list)):
        return 'COMPLEX_REPRESENTATION_NOT_DIRECTLY_COMPARABLE'
    try:
        w = _v08_scalar_normalize(wide_value)
        c = _v08_scalar_normalize(curated_value)
    except TypeError:
        return 'COMPLEX_REPRESENTATION_NOT_DIRECTLY_COMPARABLE'
    if w == c:
        return 'MATCH'
    # Calendar-date normalization is expected for date-targeted mappings.
    if w and c and len(w) >= 10 and len(c) == 10 and w[:10] == c:
        return 'NORMALIZATION_EQUIVALENT'
    return 'SOURCE_SNAPSHOT_OR_NORMALIZATION_DIFFERENCE'


def _v08_check(namespace, context, nodes, source_rows):
    approved = [r for r in context['mapping_rows'] if r.get('EXECUTION_STATUS') == 'APPROVED'
                and str(r.get('OSCAL_MODEL') or '').upper().startswith('SSP')]
    fields = sorted({r['SOURCE_FIELD_NAME'] for r in approved if r.get('SOURCE_FIELD_NAME')})

    wide_df = namespace['session'].table(_V08_WIDE_TABLE)
    wide_cols = {str(c).strip('"').upper(): c for c in wide_df.columns}
    mapped_wide = {field: wide_cols[field.upper()] for field in fields if field.upper() in wide_cols}

    wanted = tuple(str(x) for x in _V08_SOURCE_RECORD_IDS)
    wide_rows = {}
    if wanted:
        df = wide_df.filter(_v08_F.trim(_v08_F.col(wide_cols[_V08_WIDE_ID_COLUMN])).cast('string').isin(list(wanted)))
        select_cols = [_v08_F.trim(_v08_F.col(wide_cols[_V08_WIDE_ID_COLUMN])).cast('string').alias('SOURCE_RECORD_ID')]
        select_cols += [_v08_F.col(actual).alias(field) for field, actual in mapped_wide.items()]
        for row in df.select(*select_cols).to_local_iterator():
            wide_rows[str(row['SOURCE_RECORD_ID'])] = row.as_dict(recursive=True)

    curated_rows = {str(r['SOURCE_RECORD_ID']): _v08_json_obj(r['CURATED_JSON']) for r in source_rows
                    if str(r['SOURCE_RECORD_ID']) in wanted}

    graph_by_record_path = _v08_defaultdict(list)
    for n in nodes:
        if str(n['SOURCE_RECORD_ID']) in wanted:
            graph_by_record_path[(str(n['SOURCE_RECORD_ID']), n['ELEMENT_PATH'])].append(n)

    diagnostics = []
    diag_counts = _v08_Counter()
    sample_status = _v08_defaultdict(_v08_Counter)
    oscal_failures = _v08_Counter()
    oscal_expected_instances = 0
    oscal_actual_instances = 0
    owner_paths_checked = set()

    for sid in wanted:
        wide = wide_rows.get(sid, {})
        curated = curated_rows.get(sid)
        if curated is None:
            oscal_failures['MISSING_CURATED_JSON_SAMPLE'] += 1
            continue

        for field in fields:
            if field not in mapped_wide:
                continue
            status = _v08_compare_wide_to_curated(wide.get(field), _v08_source_value(curated, field))
            diag_counts[status] += 1
            sample_status[sid][status] += 1
            if status != 'MATCH':
                diagnostics.append({
                    'SOURCE_RECORD_ID': sid,
                    'FIELD': field,
                    'STATUS': status,
                    'WIDE_VALUE': _v08_python(wide.get(field)),
                    'CURATED_JSON_VALUE': _v08_python(_v08_source_value(curated, field)),
                })

        # Rebuild expected OSCAL instances from the same CURATED_JSON and current approved mappings.
        expected_ctx = dict(context)
        expected_ctx['graph_report'] = {'SOURCE_RECORDS': 0, 'INVALID_SOURCE_RECORDS': 0,
                                        'DUPLICATE_SOURCE_RECORDS': 0, 'MAPPED_VALUES': 0,
                                        'MISSING_VALUES': 0, 'STATUS': 'VALIDATION_EXPECTED_BUILD',
                                        'OUTPUTS_PUBLISHED': False}
        expected_ctx.pop('_metadata_reference_cache', None)
        canonical_registry = namespace['_canonical_registry_rows'](None, 'SSP', expected_ctx)
        registry_by_path = {r['element_path']: r for r in canonical_registry}
        owner_paths = sorted({r['OWNER_ELEMENT_PATH'] for r in approved if r.get('OWNER_ELEMENT_PATH')})
        source_obj = curated

        for path in owner_paths:
            if path not in registry_by_path:
                continue
            owner_paths_checked.add(path)
            try:
                expected = namespace['_metadata_instances'](source_obj, sid, registry_by_path[path], expected_ctx)
            except Exception:
                oscal_failures['EXPECTED_MAPPING_REBUILD_ERROR'] += 1
                continue
            actual = graph_by_record_path.get((sid, path), [])
            oscal_expected_instances += len(expected)
            oscal_actual_instances += len(actual)
            expected_by_key = {x['instance_key']: x['payload'] for x in expected}
            actual_by_key = {x['INSTANCE_KEY']: _v08_json_obj(x['METADATA_JSON']) for x in actual}
            if set(expected_by_key) != set(actual_by_key):
                oscal_failures['OSCAL_INSTANCE_SET_MISMATCH'] += 1
                continue
            for key in expected_by_key:
                if expected_by_key[key] != actual_by_key[key]:
                    oscal_failures['OSCAL_PAYLOAD_MISMATCH'] += 1

    oscal_failures = {k: v for k, v in sorted(oscal_failures.items()) if v}
    return {
        'VALIDATION': '08_SSP_SOURCE_TABLE_TO_OSCAL_SAMPLE_RECONCILIATION',
        'VALIDATOR_VERSION': '2026-09-16-r2',
        'STATUS': 'FAIL' if oscal_failures else 'PASS',
        'WIDE_SOURCE_TABLE': _V08_WIDE_TABLE,
        'RAW_SOURCE_TABLE': context['config'].get('RAW_TABLE'),
        'SAMPLE_SOURCE_RECORD_IDS': list(wanted),
        'APPROVED_SSP_SOURCE_FIELDS': len(fields),
        'APPROVED_FIELDS_FOUND_IN_WIDE_TABLE': len(mapped_wide),
        'APPROVED_FIELDS_MISSING_FROM_WIDE_TABLE': sorted(set(fields) - set(mapped_wide)),
        'WIDE_VS_CURATED_JSON_DIAGNOSTIC_COUNTS': dict(diag_counts),
        'SAMPLE_RECORD_DIAGNOSTICS': {k: dict(v) for k, v in sample_status.items()},
        'OSCAL_OWNER_PATHS_CHECKED': len(owner_paths_checked),
        'OSCAL_EXPECTED_INSTANCES': oscal_expected_instances,
        'OSCAL_ACTUAL_INSTANCES': oscal_actual_instances,
        'OSCAL_FAILURE_COUNTS': oscal_failures,
        'SOURCE_DIFFERENCE_DETAILS': diagnostics,
        'NOTES': [
            'Wide-table vs CURATED_JSON differences are diagnostics, not OSCAL mapping failures.',
            'The mapper consumes CURATED_JSON, so OSCAL pass/fail is based on CURATED_JSON -> expected OSCAL -> actual OSCAL.',
            'NORMALIZATION_EQUIVALENT covers expected representation changes such as timestamp-to-date truncation.',
            'SOURCE_SNAPSHOT_OR_NORMALIZATION_DIFFERENCE should be investigated when values materially differ.',
            'This is PREVIEW/candidate-graph reconciliation and does not prove committed target persistence.',
            'The known Metadata timestamp timezone/lexical issue remains a separate deferred SME item.',
        ],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


def run_ssp_validation_08(namespace):
    required = ('session', 'SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE', 'PIPELINE_REPORT',
                'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS',
                '_canonical_registry_rows', '_metadata_instances')
    _v08_require(all(k in namespace for k in required), 'Existing seven-cell SSP session is incomplete')
    _v08_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    _v08_require(namespace['CONFIG'].get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    report = namespace['PIPELINE_REPORT']
    _v08_require(namespace['OSCAL_LOAD_MODE'] == 'PREVIEW' and report.get('status') == 'PREVIEW_COMPLETE',
                 'A completed SSP PREVIEW is required')
    routes = [k for k in namespace['MODEL_GRAPHS'] if isinstance(k, tuple) and len(k) == 2 and k[1] == 'SSP']
    _v08_require(len(routes) == 1, 'Need exactly one SSP preview route')
    route = routes[0]
    graph = namespace['MODEL_GRAPHS'][route]
    context = graph['context']
    source = namespace['SOURCE_INPUTS'][route[0]]['source_df']

    def read(frame, columns):
        _v08_require(set(columns).issubset(frame.columns), 'Dataframe schema differs from expected contract')
        return [r.as_dict(recursive=True) for r in frame.select(*columns).to_local_iterator()]

    nodes = read(graph['nodes'], _V08_NODE_COLUMNS)
    sources = read(source, ('SOURCE_RECORD_ID', 'CURATED_JSON'))
    out = _v08_check(namespace, context, nodes, sources)
    out['RUN_ID'] = namespace['CONFIG'].get('RUN_ID')
    out['SOURCE_KEY'] = route[0]
    return out


SSP_VALIDATION_08_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_08_REPORT = run_ssp_validation_08(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v08_error:
        SSP_VALIDATION_08_REPORT = {
            'VALIDATION': '08_SSP_SOURCE_TABLE_TO_OSCAL_SAMPLE_RECONCILIATION',
            'STATUS': 'BLOCKED', 'REASON': str(_v08_error),
            'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 08 ===')
    print(_v08_json.dumps(SSP_VALIDATION_08_REPORT, indent=2, default=str))