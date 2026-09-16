# SSP Validation 08 - sample source-table / CURATED_JSON / OSCAL reconciliation
# 2026-09-16. READ ONLY. Run in the existing successful SSP PREVIEW session.
#
# Goal:
#   For selected SOURCE_RECORD_ID values, compare the current approved SSP mapping scope across:
#     1) the wide Authorization Package source table,
#     2) the frozen CURATED_JSON used by Source 1,
#     3) the generated OSCAL candidate graph.
#
# This is mapping-driven. It does NOT compare all ~610 source columns blindly; it compares only
# source fields that are currently APPROVED SSP mappings and physically exist in the wide table.
# Complex/list source values are reported separately when a direct wide-column equality check is
# not representation-safe. OSCAL expected-vs-actual comparison still uses the current Cell 4
# transformation/assembly code against the frozen CURATED_JSON snapshot.

import datetime as _v08_datetime
import json as _v08_json
from decimal import Decimal as _v08_Decimal
from collections import Counter as _v08_Counter, defaultdict as _v08_defaultdict
from snowflake.snowpark import functions as _v08_F

_V08_WIDE_TABLE = 'RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE'
_V08_WIDE_ID_COLUMN = 'ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONTENT_ID'

# Add more IDs here if desired. 7344415 is the record currently being inspected interactively.
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
        return value.isoformat(sep=' ')
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
        # Normalize ISO timestamp separator only; do not infer/alter timezone semantics.
        if len(text) >= 19 and text[4:5] == '-' and text[7:8] == '-' and text[10:11] in {'T', ' '}:
            text = text[:10] + ' ' + text[11:]
        return text
    raise TypeError('Non-scalar source value')


def _v08_payload(value):
    value = _v08_python(value)
    value = _v08_json.loads(value) if isinstance(value, str) else value
    _v08_json.dumps(value, sort_keys=True, allow_nan=False, default=str)
    return value


def _v08_canonical(value):
    return _v08_json.dumps(_v08_payload(value), sort_keys=True, allow_nan=False, default=str)


def _v08_wide_vs_json(wide_value, json_value):
    """Return (status, normalized_wide, normalized_json).

    Strictly compares scalar values. For complex JSON, compare only when the wide-table value is
    parseable JSON. Otherwise classify as COMPLEX_REPRESENTATION_NOT_DIRECTLY_COMPARABLE instead
    of creating a false data defect from storage-format differences.
    """
    json_value = _v08_python(json_value)
    wide_value = _v08_python(wide_value)

    if isinstance(json_value, (dict, list)):
        if isinstance(wide_value, str):
            text = wide_value.strip()
            if text[:1] in {'{', '['}:
                try:
                    parsed = _v08_json.loads(text)
                    return ('MATCH' if _v08_canonical(parsed) == _v08_canonical(json_value) else 'MISMATCH',
                            _v08_canonical(parsed), _v08_canonical(json_value))
                except Exception:
                    pass
        return ('COMPLEX_REPRESENTATION_NOT_DIRECTLY_COMPARABLE', str(wide_value), _v08_canonical(json_value))

    try:
        left = _v08_scalar_normalize(wide_value)
        right = _v08_scalar_normalize(json_value)
    except TypeError:
        return ('COMPLEX_REPRESENTATION_NOT_DIRECTLY_COMPARABLE', str(wide_value), str(json_value))
    return ('MATCH' if left == right else 'MISMATCH', left, right)


def _v08_run(namespace):
    required = (
        'session', 'SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE', 'PIPELINE_REPORT',
        'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS',
        '_canonical_registry_rows', '_metadata_instances', '_metadata_parse',
        'resolve_json_path',
    )
    _v08_require(all(name in namespace for name in required),
                 'Existing seven-cell SSP session is incomplete')
    _v08_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    config = namespace['CONFIG']
    report = namespace['PIPELINE_REPORT']
    _v08_require(config.get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    _v08_require(
        namespace['OSCAL_LOAD_MODE'] == 'PREVIEW'
        and report.get('mode') == 'PREVIEW'
        and report.get('status') == 'PREVIEW_COMPLETE'
        and report.get('writes_executed') is False
        and report.get('commit_attempted') is False,
        'A completed no-write PREVIEW is required',
    )

    routes = [key for key in namespace['MODEL_GRAPHS']
              if isinstance(key, tuple) and len(key) == 2 and key[1] == 'SSP']
    _v08_require(len(routes) == 1, 'Need exactly one SSP preview route')
    route = routes[0]
    graph = namespace['MODEL_GRAPHS'][route]
    context = graph['context']
    _v08_require(context['compiled_plan'].get('release') == 'lean-csv-registry-v4',
                 'Unsupported compiler release')
    _v08_require(context['config'].get('RUN_ID') == config.get('RUN_ID'), 'Stale graph context')

    # Approved field-driven SSP mappings only. CONFIG-generated support fields are not source-table checks.
    approved_rules = [
        row for row in context['mapping_rows']
        if row.get('EXECUTION_STATUS') == 'APPROVED'
        and (row.get('REPRESENTATION_PARAMS') or {}).get('value_source', 'FIELD') == 'FIELD'
        and isinstance(row.get('SOURCE_FIELD_NAME'), str)
        and row.get('SOURCE_FIELD_NAME')
    ]
    _v08_require(approved_rules, 'No approved SSP source-field mappings found')

    # Resolve live wide-table columns at run time; do not hard-code the 610-column inventory.
    wide_df = namespace['session'].table(_V08_WIDE_TABLE)
    wide_columns = {str(name).strip('"').upper(): name for name in wide_df.columns}
    _v08_require(_V08_WIDE_ID_COLUMN.upper() in wide_columns,
                 'Wide source table content-id column not found')
    wide_id_actual = wide_columns[_V08_WIDE_ID_COLUMN.upper()]

    source_fields = sorted({row['SOURCE_FIELD_NAME'] for row in approved_rules})
    source_field_to_wide = {
        field: wide_columns.get(field.upper())
        for field in source_fields
    }
    matched_fields = [field for field, actual in source_field_to_wide.items() if actual is not None]
    missing_wide_fields = [field for field, actual in source_field_to_wide.items() if actual is None]
    _v08_require(matched_fields, 'None of the approved SSP source fields exist in the wide source table')

    # Frozen Source 1 rows used by the preview.
    source_input = namespace['SOURCE_INPUTS'][route[0]]
    source_rows = [row.as_dict(recursive=True)
                   for row in source_input['source_df'].select('SOURCE_RECORD_ID', 'CURATED_JSON').to_local_iterator()]
    source_by_id = {row['SOURCE_RECORD_ID']: row for row in source_rows}
    _v08_require(len(source_by_id) == len(source_rows), 'Frozen source contains duplicate SOURCE_RECORD_ID')

    sample_ids = tuple(str(value) for value in _V08_SOURCE_RECORD_IDS)
    _v08_require(sample_ids and len(set(sample_ids)) == len(sample_ids), 'Choose distinct sample SOURCE_RECORD_ID values')
    missing_source_ids = [sid for sid in sample_ids if sid not in source_by_id]
    _v08_require(not missing_source_ids, 'Sample SOURCE_RECORD_ID missing from frozen Source 1: ' + ', '.join(missing_source_ids))

    # Read only mapped wide-table columns for the selected records.
    select_exprs = [_v08_F.col(wide_id_actual).cast('string').alias('SOURCE_RECORD_ID')]
    for field in matched_fields:
        select_exprs.append(_v08_F.col(source_field_to_wide[field]).alias(field))
    wide_rows = [row.as_dict(recursive=True) for row in
                 wide_df.filter(_v08_F.col(wide_id_actual).cast('string').isin(list(sample_ids)))
                        .select(*select_exprs).to_local_iterator()]
    wide_by_id = {row['SOURCE_RECORD_ID']: row for row in wide_rows}
    _v08_require(len(wide_by_id) == len(wide_rows), 'Wide table contains duplicate selected content IDs')

    failures = _v08_Counter()
    wide_status = _v08_Counter()
    mismatch_details = []
    sample_summary = {}

    def bad(name, count=1):
        failures[name] += count

    for sid in sample_ids:
        if sid not in wide_by_id:
            bad('SAMPLE_ID_MISSING_FROM_WIDE_TABLE')
            mismatch_details.append({'SOURCE_RECORD_ID': sid, 'FIELD': None, 'STATUS': 'MISSING_FROM_WIDE_TABLE'})
            continue
        source_obj = namespace['_metadata_parse'](source_by_id[sid], context)
        wide_row = wide_by_id[sid]
        per_record = _v08_Counter()
        for field in matched_fields:
            raw_value = namespace['resolve_json_path'](source_obj, field, default=None)
            status, wide_norm, json_norm = _v08_wide_vs_json(wide_row.get(field), raw_value)
            wide_status[status] += 1
            per_record[status] += 1
            if status == 'MISMATCH':
                bad('WIDE_TABLE_VS_CURATED_JSON_MISMATCH')
                mismatch_details.append({
                    'SOURCE_RECORD_ID': sid,
                    'FIELD': field,
                    'STATUS': status,
                    'WIDE_VALUE': wide_norm,
                    'CURATED_JSON_VALUE': json_norm,
                })
        sample_summary[sid] = dict(per_record)

    # Compare the generated OSCAL candidate graph to expectations rebuilt from the exact frozen
    # CURATED_JSON and current approved mapping/registry contract for these sample IDs.
    node_rows = [row.as_dict(recursive=True)
                 for row in graph['nodes'].select(*_V08_NODE_COLUMNS).to_local_iterator()]
    actual_by_record_path = _v08_defaultdict(list)
    for node in node_rows:
        if node['SOURCE_RECORD_ID'] in sample_ids:
            actual_by_record_path[(node['SOURCE_RECORD_ID'], node['ELEMENT_PATH'])].append(node)

    owner_paths = sorted({row['OWNER_ELEMENT_PATH'] for row in approved_rules if row.get('OWNER_ELEMENT_PATH')})
    canonical_registry = namespace['_canonical_registry_rows'](None, 'SSP', context)
    registry_by_path = {row['element_path']: row for row in canonical_registry}
    _v08_require(all(path in registry_by_path for path in owner_paths),
                 'Approved mapped owner path missing from compiled registry')

    expected_ctx = dict(context)
    expected_ctx['graph_report'] = {
        'SOURCE_RECORDS': 0, 'INVALID_SOURCE_RECORDS': 0, 'DUPLICATE_SOURCE_RECORDS': 0,
        'MAPPED_VALUES': 0, 'MISSING_VALUES': 0, 'STATUS': 'VALIDATION_EXPECTED_BUILD',
        'OUTPUTS_PUBLISHED': False,
    }
    expected_ctx.pop('_metadata_reference_cache', None)

    oscal_paths_checked = 0
    oscal_expected_instances = 0
    oscal_actual_instances = 0

    for sid in sample_ids:
        source_obj = namespace['_metadata_parse'](source_by_id[sid], expected_ctx)
        for path in owner_paths:
            expected_ctx.pop('_metadata_reference_cache', None)
            try:
                expected = namespace['_metadata_instances'](source_obj, sid, registry_by_path[path], expected_ctx)
            except (ValueError, TypeError, KeyError, ArithmeticError):
                bad('EXPECTED_OSCAL_REBUILD_ERROR')
                continue
            actual = actual_by_record_path.get((sid, path), [])
            expected_by_instance = {item['instance_key']: item for item in expected}
            actual_by_instance = {node['INSTANCE_KEY']: node for node in actual}
            oscal_paths_checked += 1
            oscal_expected_instances += len(expected)
            oscal_actual_instances += len(actual)
            if len(expected_by_instance) != len(expected) or len(actual_by_instance) != len(actual):
                bad('DUPLICATE_INSTANCE_KEY')
            if set(expected_by_instance) != set(actual_by_instance):
                bad('OSCAL_INSTANCE_SET_MISMATCH')
                mismatch_details.append({
                    'SOURCE_RECORD_ID': sid,
                    'OWNER_ELEMENT_PATH': path,
                    'STATUS': 'OSCAL_INSTANCE_SET_MISMATCH',
                    'EXPECTED_INSTANCE_KEYS': sorted(expected_by_instance),
                    'ACTUAL_INSTANCE_KEYS': sorted(actual_by_instance),
                })
                continue
            for key in expected_by_instance:
                expected_payload = _v08_canonical(expected_by_instance[key]['payload'])
                actual_payload = _v08_canonical(actual_by_instance[key]['METADATA_JSON'])
                if expected_payload != actual_payload:
                    bad('OSCAL_PAYLOAD_MISMATCH')
                    mismatch_details.append({
                        'SOURCE_RECORD_ID': sid,
                        'OWNER_ELEMENT_PATH': path,
                        'INSTANCE_KEY': key,
                        'STATUS': 'OSCAL_PAYLOAD_MISMATCH',
                        'EXPECTED_PAYLOAD': expected_payload,
                        'ACTUAL_PAYLOAD': actual_payload,
                    })

    failures = {key: value for key, value in sorted(failures.items()) if value}
    return {
        'VALIDATION': '08_SSP_SOURCE_TABLE_TO_OSCAL_SAMPLE_RECONCILIATION',
        'VALIDATOR_VERSION': '2026-09-16-r1',
        'STATUS': 'FAIL' if failures else 'PASS',
        'WIDE_SOURCE_TABLE': _V08_WIDE_TABLE,
        'RAW_SOURCE_TABLE': context['config'].get('RAW_TABLE'),
        'SAMPLE_SOURCE_RECORD_IDS': list(sample_ids),
        'APPROVED_SSP_SOURCE_FIELDS': len(source_fields),
        'APPROVED_FIELDS_FOUND_IN_WIDE_TABLE': len(matched_fields),
        'APPROVED_FIELDS_MISSING_FROM_WIDE_TABLE': missing_wide_fields,
        'WIDE_VS_CURATED_JSON_STATUS_COUNTS': dict(sorted(wide_status.items())),
        'SAMPLE_RECORD_STATUS': sample_summary,
        'OSCAL_OWNER_PATHS_CHECKED': oscal_paths_checked,
        'OSCAL_EXPECTED_INSTANCES': oscal_expected_instances,
        'OSCAL_ACTUAL_INSTANCES': oscal_actual_instances,
        'FAILURE_COUNTS': failures,
        'MISMATCH_DETAILS': mismatch_details[:50],
        'NOTES': [
            'Only APPROVED SSP source-field mappings are compared; the remaining ~610 source columns are out of current OSCAL mapping scope.',
            'Complex/list source values are not marked failed solely because the wide table serializes them differently from CURATED_JSON.',
            'OSCAL expected payloads are rebuilt from the frozen CURATED_JSON using the current Cell 4 mapping machinery.',
            'This is PREVIEW/candidate-graph reconciliation; it does not prove committed target-table persistence.',
            'The known Metadata timestamp timezone/lexical issue remains a separate deferred SME item.',
        ],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


SSP_VALIDATION_08_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_08_REPORT = _v08_run(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v08_error:
        SSP_VALIDATION_08_REPORT = {
            'VALIDATION': '08_SSP_SOURCE_TABLE_TO_OSCAL_SAMPLE_RECONCILIATION',
            'STATUS': 'BLOCKED',
            'REASON': str(_v08_error),
            'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 08 ===')
    print(_v08_json.dumps(SSP_VALIDATION_08_REPORT, indent=2, default=str))
