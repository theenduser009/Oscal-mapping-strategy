# SSP Validation 10 - full Source 1 CURATED_JSON -> OSCAL reconciliation
# 2026-09-16. READ ONLY. Run in the existing successful SSP PREVIEW session.
#
# Purpose:
#   Treat the configured Source 1 RAW table CURATED_JSON as the authoritative mapper input.
#   Validate two things across the current SSP source population:
#     1) the frozen PREVIEW source snapshot still matches the current live RAW CURATED_JSON;
#     2) every current APPROVED SSP mapping produces the expected OSCAL candidate instances/payloads.
#
# This deliberately ignores the separate wide Authorization Package table.
# It does not validate deferred/excluded mappings, committed target persistence, business meaning,
# or the known Metadata timestamp timezone/lexical issue beyond reproducing current mapper behavior.

import json as _v10_json
from collections import Counter as _v10_Counter, defaultdict as _v10_defaultdict
from snowflake.snowpark import functions as _v10_F

# Empty tuple means validate every Source 1 record selected into the current preview.
# Add IDs here to run a smaller targeted sample instead.
_V10_SOURCE_RECORD_IDS = ()

_V10_NODE_COLUMNS = (
    'NODE_KEY', 'ELEMENT_PATH', 'PARENT_NODE_PATH', 'INSTANCE_KEY',
    'PARENT_INSTANCE_KEY', 'OSCAL_UUID', 'ELEMENT_TYPE', 'METADATA_JSON',
    'SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME', 'SOURCE_RECORD_ID', 'DW_PIPELINE_RUN_ID',
)
_V10_EDGE_COLUMNS = (
    'EDGE_KEY', 'FK_SOURCE_ELEMENT_HASH', 'FK_TARGET_ELEMENT_HASH',
    'DEPENDENCY_TYPE', 'SOURCE_OSCAL_UUID', 'TARGET_OSCAL_UUID',
)


def _v10_require(condition, message):
    if not condition:
        raise ValueError(message)


def _v10_python(value):
    if hasattr(value, 'as_dict'):
        return value.as_dict(recursive=True)
    if hasattr(value, 'as_list'):
        return value.as_list()
    return value


def _v10_json_obj(value):
    value = _v10_python(value)
    if isinstance(value, str):
        value = _v10_json.loads(value)
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object')
    return value


def _v10_canonical_json(value):
    return _v10_json.dumps(_v10_python(value), sort_keys=True, separators=(',', ':'), default=str)


def _v10_check(namespace, context, nodes, edges, frozen_rows):
    failures = _v10_Counter()
    by_key = {n['NODE_KEY']: n for n in nodes}

    approved = [
        row for row in context['mapping_rows']
        if row.get('EXECUTION_STATUS') == 'APPROVED'
        and str(row.get('OSCAL_MODEL') or '').upper().startswith('SSP')
        and row.get('OWNER_ELEMENT_PATH')
    ]
    _v10_require(approved, 'No APPROVED SSP mappings found in current compiled context')

    owner_paths = sorted({row['OWNER_ELEMENT_PATH'] for row in approved})
    canonical_registry = namespace['_canonical_registry_rows'](None, 'SSP', context)
    registry_by_path = {row['element_path']: row for row in canonical_registry}
    _v10_require(all(path in registry_by_path for path in owner_paths),
                 'Approved SSP owner path missing from compiled registry')

    frozen_by_id = {str(r['SOURCE_RECORD_ID']): _v10_json_obj(r['CURATED_JSON']) for r in frozen_rows}
    wanted = tuple(str(x) for x in _V10_SOURCE_RECORD_IDS)
    if wanted:
        frozen_by_id = {k: v for k, v in frozen_by_id.items() if k in wanted}
        _v10_require(set(wanted).issubset(frozen_by_id), 'Requested sample ID missing from frozen preview source')
    _v10_require(frozen_by_id, 'No frozen Source 1 records selected')

    # Read the current live RAW table using the actual configured contract.
    raw_table = context['config']['RAW_TABLE']
    raw_id_col = context['config'].get('CONTENT_ID_COLUMN', 'CONTENT_ID')
    raw_json_col = context['config'].get('CURATED_JSON_COLUMN', 'CURATED_JSON')
    raw_df = namespace['session'].table(raw_table)
    raw_cols = {str(c).strip('"').upper(): c for c in raw_df.columns}
    _v10_require(raw_id_col.upper() in raw_cols and raw_json_col.upper() in raw_cols,
                 'Configured live RAW identity/CURATED_JSON columns are missing')

    selected_ids = sorted(frozen_by_id)
    live_df = raw_df.filter(
        _v10_F.trim(_v10_F.col(raw_cols[raw_id_col.upper()])).cast('string').isin(selected_ids)
    ).select(
        _v10_F.trim(_v10_F.col(raw_cols[raw_id_col.upper()])).cast('string').alias('SOURCE_RECORD_ID'),
        _v10_F.col(raw_cols[raw_json_col.upper()]).alias('CURATED_JSON')
    )
    live_by_id = {}
    for row in live_df.to_local_iterator():
        sid = str(row['SOURCE_RECORD_ID'])
        if sid in live_by_id:
            failures['DUPLICATE_LIVE_RAW_SOURCE_RECORD'] += 1
            continue
        try:
            live_by_id[sid] = _v10_json_obj(row['CURATED_JSON'])
        except (ValueError, TypeError, _v10_json.JSONDecodeError):
            failures['INVALID_LIVE_RAW_CURATED_JSON'] += 1

    for sid in selected_ids:
        if sid not in live_by_id:
            failures['MISSING_LIVE_RAW_SOURCE_RECORD'] += 1
            continue
        if _v10_canonical_json(frozen_by_id[sid]) != _v10_canonical_json(live_by_id[sid]):
            failures['FROZEN_PREVIEW_VS_LIVE_RAW_CURATED_JSON_MISMATCH'] += 1

    graph_by_record_path = _v10_defaultdict(list)
    for node in nodes:
        sid = str(node['SOURCE_RECORD_ID'])
        if sid in frozen_by_id:
            graph_by_record_path[(sid, node['ELEMENT_PATH'])].append(node)

    expected_instances = _v10_Counter()
    actual_instances = _v10_Counter()
    mapped_records = _v10_Counter()
    relevant_node_keys = set()

    expected_ctx = dict(context)
    expected_ctx['graph_report'] = {
        'SOURCE_RECORDS': 0, 'INVALID_SOURCE_RECORDS': 0, 'DUPLICATE_SOURCE_RECORDS': 0,
        'MAPPED_VALUES': 0, 'MISSING_VALUES': 0, 'STATUS': 'VALIDATION_EXPECTED_BUILD',
        'OUTPUTS_PUBLISHED': False,
    }
    expected_ctx.pop('_metadata_reference_cache', None)

    for sid, source_obj in frozen_by_id.items():
        for path in owner_paths:
            expected_ctx.pop('_metadata_reference_cache', None)
            try:
                expected = namespace['_metadata_instances'](
                    source_obj, sid, registry_by_path[path], expected_ctx
                )
            except (ValueError, TypeError, KeyError, ArithmeticError):
                failures['EXPECTED_MAPPING_REBUILD_ERROR'] += 1
                continue

            actual = graph_by_record_path.get((sid, path), [])
            expected_instances[path] += len(expected)
            actual_instances[path] += len(actual)
            mapped_records[path] += 1

            expected_by_instance = {item['instance_key']: _v10_json_obj(item['payload']) for item in expected}
            actual_by_instance = {node['INSTANCE_KEY']: _v10_json_obj(node['METADATA_JSON']) for node in actual}

            if len(expected_by_instance) != len(expected):
                failures['DUPLICATE_EXPECTED_INSTANCE_KEY'] += 1
            if len(actual_by_instance) != len(actual):
                failures['DUPLICATE_ACTUAL_INSTANCE_KEY'] += 1
            if set(expected_by_instance) != set(actual_by_instance):
                failures['OSCAL_INSTANCE_SET_MISMATCH'] += 1
                continue

            for key in expected_by_instance:
                if expected_by_instance[key] != actual_by_instance[key]:
                    failures['OSCAL_PAYLOAD_MISMATCH'] += 1
                else:
                    # Track only nodes whose payload has been proven against current mapping machinery.
                    matching = [n for n in actual if n['INSTANCE_KEY'] == key]
                    if len(matching) == 1:
                        relevant_node_keys.add(matching[0]['NODE_KEY'])

    # Re-check relationship integrity only for the mapping-proven nodes.
    incoming = _v10_Counter()
    relevant_edges = 0
    for edge in edges:
        target = edge['FK_TARGET_ELEMENT_HASH']
        if target not in relevant_node_keys:
            continue
        relevant_edges += 1
        parent = by_key.get(edge['FK_SOURCE_ELEMENT_HASH'])
        child = by_key.get(target)
        if parent is None or child is None:
            failures['UNRESOLVED_RELEVANT_EDGE_ENDPOINT'] += 1
            continue
        incoming[target] += 1
        if parent['SOURCE_RECORD_ID'] != child['SOURCE_RECORD_ID']:
            failures['CROSS_RECORD_RELEVANT_EDGE'] += 1
        if parent['ELEMENT_PATH'] != child['PARENT_NODE_PATH']:
            failures['WRONG_RELEVANT_PARENT_PATH'] += 1
        if edge['DEPENDENCY_TYPE'] != 'CONTAINS':
            failures['WRONG_RELEVANT_EDGE_TYPE'] += 1
        if (edge['SOURCE_OSCAL_UUID'] != parent['OSCAL_UUID']
                or edge['TARGET_OSCAL_UUID'] != child['OSCAL_UUID']):
            failures['RELEVANT_EDGE_UUID_MISMATCH'] += 1

    missing_parent_count = sum(incoming[key] != 1 for key in relevant_node_keys)
    if missing_parent_count:
        failures['RELEVANT_PARENT_EDGE_COUNT'] += missing_parent_count

    failures = {k: v for k, v in sorted(failures.items()) if v}
    return {
        'VALIDATION': '10_SSP_CURATED_JSON_TO_OSCAL_FULL_RECONCILIATION',
        'VALIDATOR_VERSION': '2026-09-16-r1',
        'STATUS': 'FAIL' if failures else 'PASS',
        'SOURCE_KEY': context['source_key'],
        'LIVE_RAW_TABLE': raw_table,
        'SOURCE_RECORDS_CHECKED': len(frozen_by_id),
        'APPROVED_SSP_MAPPING_ROWS_IN_SCOPE': len(approved),
        'OWNER_PATHS_IN_SCOPE': owner_paths,
        'EXPECTED_INSTANCES_BY_PATH': dict(expected_instances),
        'ACTUAL_INSTANCES_BY_PATH': dict(actual_instances),
        'RELEVANT_NODES_PAYLOAD_MATCHED': len(relevant_node_keys),
        'RELEVANT_EDGES_CHECKED': relevant_edges,
        'FAILURE_COUNTS': failures,
        'NOTES': [
            'The wide Authorization Package table is intentionally excluded from this validator.',
            'Pass means the frozen Source 1 CURATED_JSON matches current live RAW CURATED_JSON and current APPROVED SSP mappings reproduce the candidate OSCAL graph.',
            'This is PREVIEW/candidate-graph evidence; it does not prove committed target persistence.',
            'Deferred/excluded mappings are outside scope.',
            'The known Metadata timestamp timezone/lexical issue remains separately deferred to SME; this validator only verifies current mapper behavior is reproduced consistently.',
        ],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


def run_ssp_validation_10(namespace):
    required = (
        'session', 'SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE', 'PIPELINE_REPORT',
        'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS',
        '_canonical_registry_rows', '_metadata_instances',
    )
    _v10_require(all(name in namespace for name in required), 'Existing seven-cell SSP session is incomplete')
    _v10_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    config = namespace['CONFIG']
    report = namespace['PIPELINE_REPORT']
    _v10_require(config.get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    _v10_require(
        namespace['OSCAL_LOAD_MODE'] == 'PREVIEW'
        and isinstance(report, dict)
        and report.get('status') == 'PREVIEW_COMPLETE'
        and report.get('writes_executed') is False
        and report.get('commit_attempted') is False,
        'A completed no-write SSP PREVIEW is required',
    )

    routes = [k for k in namespace['MODEL_GRAPHS'] if isinstance(k, tuple) and len(k) == 2 and k[1] == 'SSP']
    _v10_require(len(routes) == 1, 'Need exactly one SSP preview route')
    route = routes[0]
    graph = namespace['MODEL_GRAPHS'][route]
    context = graph['context']
    _v10_require(context['config'].get('RUN_ID') == config.get('RUN_ID'), 'Graph context is stale')
    _v10_require(context['routing_report'].get('STATUS') == 'READY', 'Current SSP route is not READY')

    groups = [g for g in report.get('groups', []) if (g.get('source'), g.get('model')) == route]
    _v10_require(len(groups) == 1 and groups[0]['load'].get('validation_passed') is True,
                 'The SSP route lacks successful Cell 6 graph validation')

    source = namespace['SOURCE_INPUTS'][route[0]]['source_df']

    def read(frame, columns):
        _v10_require(hasattr(frame, 'columns') and set(columns).issubset(frame.columns),
                     'Dataframe schema differs from verified contract')
        return [row.as_dict(recursive=True) for row in frame.select(*columns).to_local_iterator()]

    nodes = read(graph['nodes'], _V10_NODE_COLUMNS)
    edges = read(graph['edges'], _V10_EDGE_COLUMNS)
    frozen = read(source, ('SOURCE_RECORD_ID', 'CURATED_JSON'))
    out = _v10_check(namespace, context, nodes, edges, frozen)
    out['RUN_ID'] = config.get('RUN_ID')
    return out


SSP_VALIDATION_10_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_10_REPORT = run_ssp_validation_10(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v10_error:
        SSP_VALIDATION_10_REPORT = {
            'VALIDATION': '10_SSP_CURATED_JSON_TO_OSCAL_FULL_RECONCILIATION',
            'STATUS': 'BLOCKED',
            'REASON': str(_v10_error),
            'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 10 ===')
    print(_v10_json.dumps(SSP_VALIDATION_10_REPORT, indent=2, default=str))
