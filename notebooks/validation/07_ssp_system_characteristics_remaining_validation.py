# SSP Validation 07 - remaining approved System Characteristics mappings
# 2026-09-16. READ ONLY. Run in the existing successful SSP PREVIEW session.
# This validator is mapping-driven: it reads the current compiled CSV rules and
# compares the generated candidate graph to expected payloads rebuilt with the
# same reviewed Cell 4 transforms/assemblers against the frozen source snapshot.
#
# Scope begins where Validation 06 stopped. It covers APPROVED mappings under
# system-security-plan.system-characteristics except the four core rules already
# covered by Validation 06 (system-name, system-name-short, description, system-ids[].id).
# Typical covered branches include props[], status, authorization-boundary,
# date-authorized, security-sensitivity-level, and security-impact-level.
# It does not approve business meaning, full OSCAL schema conformance, timestamps,
# target persistence, deferred/excluded mappings, or non-System-Characteristics branches.

import json as _v07_json
from collections import Counter as _v07_Counter, defaultdict as _v07_defaultdict

_V07_BASE = 'system-security-plan.system-characteristics'
_V07_CORE_CANONICAL = {
    _V07_BASE + '.system-name',
    _V07_BASE + '.system-name-short',
    _V07_BASE + '.description',
    _V07_BASE + '.system-ids[].id',
}
_V07_NODE_COLUMNS = (
    'NODE_KEY', 'ELEMENT_PATH', 'PARENT_NODE_PATH', 'INSTANCE_KEY',
    'PARENT_INSTANCE_KEY', 'OSCAL_UUID', 'ELEMENT_TYPE', 'METADATA_JSON',
    'SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME', 'SOURCE_RECORD_ID', 'DW_PIPELINE_RUN_ID',
)
_V07_EDGE_COLUMNS = (
    'EDGE_KEY', 'FK_SOURCE_ELEMENT_HASH', 'FK_TARGET_ELEMENT_HASH',
    'DEPENDENCY_TYPE', 'SOURCE_OSCAL_UUID', 'TARGET_OSCAL_UUID',
)


def _v07_require(condition, message):
    if not condition:
        raise ValueError(message)


def _v07_object(value):
    value = _v07_json.loads(value) if isinstance(value, str) else value
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    _v07_json.dumps(value, allow_nan=False)
    return value


def _v07_get(payload, target):
    current = payload
    for token in str(target or '').split('.'):
        if not token:
            continue
        current = current.get(token) if isinstance(current, dict) else None
    return current


def _v07_check(namespace, context, nodes, edges, source_rows):
    config = context['config']

    # Use only current APPROVED compiled mapping rows under System Characteristics,
    # excluding the four rules already proven by Validation 06.
    rules = [
        row for row in context['mapping_rows']
        if row.get('EXECUTION_STATUS') == 'APPROVED'
        and isinstance(row.get('CANONICAL_ELEMENT_PATH'), str)
        and row['CANONICAL_ELEMENT_PATH'].startswith(_V07_BASE + '.')
        and row['CANONICAL_ELEMENT_PATH'] not in _V07_CORE_CANONICAL
    ]
    _v07_require(rules, 'No remaining APPROVED System Characteristics mappings were compiled')
    _v07_require(len({row.get('RULE_ID') for row in rules}) == len(rules),
                 'Remaining System Characteristics RULE_ID values must be unique')
    _v07_require(all(row.get('OWNER_ELEMENT_PATH') for row in rules),
                 'Remaining mapping row is missing OWNER_ELEMENT_PATH')

    owner_paths = sorted({row['OWNER_ELEMENT_PATH'] for row in rules})
    rules_by_owner = _v07_defaultdict(list)
    for row in rules:
        rules_by_owner[row['OWNER_ELEMENT_PATH']].append(row)

    canonical_registry = namespace['_canonical_registry_rows'](None, 'SSP', context)
    registry_by_path = {row['element_path']: row for row in canonical_registry}
    _v07_require(all(path in registry_by_path for path in owner_paths),
                 'A remaining mapped owner path is absent from the compiled registry')

    source_by_id = {}
    for row in source_rows:
        sid = row['SOURCE_RECORD_ID']
        if not isinstance(sid, str) or not sid.strip() or sid in source_by_id:
            raise ValueError('Frozen source contains missing or duplicate SOURCE_RECORD_ID')
        source_by_id[sid] = row

    actual_by_record_path = _v07_defaultdict(list)
    by_key = {}
    for node in nodes:
        by_key[node['NODE_KEY']] = node
        if node['ELEMENT_PATH'] in owner_paths:
            actual_by_record_path[(node['SOURCE_RECORD_ID'], node['ELEMENT_PATH'])].append(node)

    failures = _v07_Counter()
    expected_instance_counts = _v07_Counter()
    actual_instance_counts = _v07_Counter()
    rules_exercised = _v07_Counter()
    owner_records_checked = _v07_Counter()
    relevant_node_keys = set()

    def bad(name, count=1):
        failures[name] += count

    # Build expected payloads using the exact current Cell 4 mapping machinery,
    # but in a shallow isolated context so the retained preview context/report is not changed.
    expected_ctx = dict(context)
    expected_ctx['graph_report'] = {
        'SOURCE_RECORDS': 0, 'INVALID_SOURCE_RECORDS': 0, 'DUPLICATE_SOURCE_RECORDS': 0,
        'MAPPED_VALUES': 0, 'MISSING_VALUES': 0, 'STATUS': 'VALIDATION_EXPECTED_BUILD',
        'OUTPUTS_PUBLISHED': False,
    }
    expected_ctx.pop('_metadata_reference_cache', None)

    for sid, source_row in source_by_id.items():
        try:
            source_obj = namespace['_metadata_parse'](source_row, expected_ctx)
        except (ValueError, TypeError):
            bad('INVALID_FROZEN_SOURCE_JSON')
            continue

        for path in owner_paths:
            owner_records_checked[path] += 1
            expected_ctx.pop('_metadata_reference_cache', None)
            try:
                expected_instances = namespace['_metadata_instances'](
                    source_obj, sid, registry_by_path[path], expected_ctx
                )
            except (ValueError, TypeError, KeyError, ArithmeticError):
                bad('EXPECTED_MAPPING_REBUILD_ERROR')
                continue

            actual_nodes = actual_by_record_path.get((sid, path), [])
            expected_instance_counts[path] += len(expected_instances)
            actual_instance_counts[path] += len(actual_nodes)

            expected_by_key = {item['instance_key']: item for item in expected_instances}
            actual_by_instance = {node['INSTANCE_KEY']: node for node in actual_nodes}

            if len(expected_by_key) != len(expected_instances):
                bad('DUPLICATE_EXPECTED_INSTANCE_KEY')
            if len(actual_by_instance) != len(actual_nodes):
                bad('DUPLICATE_ACTUAL_INSTANCE_KEY')
            if set(expected_by_key) != set(actual_by_instance):
                bad('INSTANCE_SET_MISMATCH')

            # props[] is entirely part of this remaining-validation scope, so compare
            # each generated property node exactly by INSTANCE_KEY and payload.
            operator = context['compiled_plan']['elements'][path]['operator']
            if operator == 'properties':
                for key in set(expected_by_key) & set(actual_by_instance):
                    try:
                        expected_payload = _v07_object(expected_by_key[key]['payload'])
                        actual_payload = _v07_object(actual_by_instance[key]['METADATA_JSON'])
                    except (ValueError, TypeError):
                        bad('INVALID_PROPERTY_PAYLOAD')
                        continue
                    if expected_payload != actual_payload:
                        bad('PROPERTY_PAYLOAD_MISMATCH')
                    relevant_node_keys.add(actual_by_instance[key]['NODE_KEY'])
                continue

            # Other remaining owner paths are singleton/object assemblies. For child
            # objects (status, authorization-boundary, security-impact-level, etc.),
            # compare the full rebuilt payload. For the shared System Characteristics
            # object itself, compare only members owned by remaining rules so Validation
            # 07 does not re-judge the four core fields already handled by Validation 06.
            for key in set(expected_by_key) & set(actual_by_instance):
                try:
                    expected_payload = _v07_object(expected_by_key[key]['payload'])
                    actual_payload = _v07_object(actual_by_instance[key]['METADATA_JSON'])
                except (ValueError, TypeError):
                    bad('INVALID_OBJECT_PAYLOAD')
                    continue

                if path == _V07_BASE:
                    targets = sorted({
                        (row.get('REPRESENTATION_PARAMS') or {}).get('target')
                        for row in rules_by_owner[path]
                        if (row.get('REPRESENTATION_PARAMS') or {}).get('target')
                    })
                    for target in targets:
                        if _v07_get(expected_payload, target) != _v07_get(actual_payload, target):
                            bad('BASE_MEMBER_PAYLOAD_MISMATCH')
                elif expected_payload != actual_payload:
                    bad('OBJECT_PAYLOAD_MISMATCH')

                relevant_node_keys.add(actual_by_instance[key]['NODE_KEY'])

            # Count a compiled rule as exercised for this source when its source field
            # is present in the frozen JSON. This is coverage information, not pass logic.
            for row in rules_by_owner[path]:
                field = row.get('SOURCE_FIELD_NAME')
                if isinstance(source_obj, dict) and field in source_obj:
                    rules_exercised[field] += 1

    # Relationship integrity only for nodes validated above. Cell 6 already performed
    # full generic graph validation; here we ensure the mapping-owned nodes still have
    # the expected single incoming parent relationship in this same source record.
    incoming = _v07_Counter()
    relevant_edges = 0
    for edge in edges:
        target_key = edge['FK_TARGET_ELEMENT_HASH']
        if target_key not in relevant_node_keys:
            continue
        relevant_edges += 1
        parent = by_key.get(edge['FK_SOURCE_ELEMENT_HASH'])
        child = by_key.get(target_key)
        if parent is None or child is None:
            bad('UNRESOLVED_RELEVANT_EDGE_ENDPOINT')
            continue
        incoming[target_key] += 1
        if parent['SOURCE_RECORD_ID'] != child['SOURCE_RECORD_ID']:
            bad('CROSS_RECORD_RELEVANT_EDGE')
        if parent['ELEMENT_PATH'] != child['PARENT_NODE_PATH']:
            bad('WRONG_RELEVANT_PARENT_PATH')
        if edge['DEPENDENCY_TYPE'] != 'CONTAINS':
            bad('WRONG_RELEVANT_EDGE_TYPE')
        if (edge['SOURCE_OSCAL_UUID'] != parent['OSCAL_UUID']
                or edge['TARGET_OSCAL_UUID'] != child['OSCAL_UUID']):
            bad('RELEVANT_EDGE_UUID_MISMATCH')

    bad('RELEVANT_PARENT_EDGE_COUNT', sum(incoming[key] != 1 for key in relevant_node_keys))

    failures = {key: value for key, value in sorted(failures.items()) if value}
    return {
        'VALIDATION': '07_SSP_SYSTEM_CHARACTERISTICS_REMAINING_MAPPINGS',
        'VALIDATOR_VERSION': '2026-09-16-r1',
        'STATUS': 'FAIL' if failures else 'PASS',
        'SOURCE_RECORDS': len(source_rows),
        'APPROVED_RULES_IN_SCOPE': len(rules),
        'SOURCE_FIELDS_IN_SCOPE': sorted({row['SOURCE_FIELD_NAME'] for row in rules}),
        'OWNER_PATHS_IN_SCOPE': owner_paths,
        'EXPECTED_INSTANCES_BY_PATH': dict(expected_instance_counts),
        'ACTUAL_INSTANCES_BY_PATH': dict(actual_instance_counts),
        'SOURCE_FIELD_PRESENCE_COUNTS': dict(sorted(rules_exercised.items())),
        'RELEVANT_EDGES_CHECKED': relevant_edges,
        'FAILURE_COUNTS': failures,
        'EXCLUDED_FROM_THIS_VALIDATION': [
            'Validation 06 core fields: system-name, system-name-short, description, system-ids[].id',
            'Metadata timestamps and their known deferred timezone remediation',
            'Deferred, excluded, and blocked-if-populated mappings',
            'System Implementation and Control Implementation',
            'Full OSCAL schema conformance',
            'Business/SME approval of field meanings',
            'Target persistence / COMMIT readback',
        ],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


def run_ssp_validation_07(namespace):
    required = (
        'SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE', 'PIPELINE_REPORT',
        'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS',
        '_canonical_registry_rows', '_metadata_instances', '_metadata_parse',
    )
    _v07_require(all(name in namespace for name in required),
                 'Existing seven-cell SSP session is incomplete')
    _v07_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')

    config = namespace['CONFIG']
    pipeline_report = namespace['PIPELINE_REPORT']
    _v07_require(config.get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    _v07_require(
        namespace['OSCAL_LOAD_MODE'] == 'PREVIEW'
        and isinstance(pipeline_report, dict)
        and pipeline_report.get('mode') == 'PREVIEW'
        and pipeline_report.get('status') == 'PREVIEW_COMPLETE'
        and pipeline_report.get('writes_executed') is False
        and pipeline_report.get('commit_attempted') is False,
        'A completed no-write PREVIEW is required',
    )

    graphs = namespace['MODEL_GRAPHS']
    routes = [key for key in graphs if isinstance(key, tuple) and len(key) == 2 and key[1] == 'SSP']
    _v07_require(len(routes) == 1, 'Need exactly one SSP preview route')
    route = routes[0]
    graph = graphs[route]
    _v07_require(all(name in graph for name in ('nodes', 'edges', 'context')),
                 'Cell 7 graph contract mismatch')

    context = graph['context']
    _v07_require(all(name in context for name in (
        'registry_rows', 'compiled_plan', 'mapping_rows', 'config', 'routing_report'
    )), 'Graph context contract mismatch')
    _v07_require(
        context['config'].get('RUN_ID') == config.get('RUN_ID')
        and context['config'].get('EXECUTE_WRITES') is False
        and context['routing_report'].get('STATUS') == 'READY',
        'Stale or blocked graph context',
    )
    _v07_require(context['compiled_plan'].get('release') == 'lean-csv-registry-v4',
                 'Unsupported compiler release')

    current = [ctx for ctx in namespace['MAPPING_CONTEXTS']
               if (ctx.get('source_key'), ctx.get('config', {}).get('OSCAL_MODEL')) == route]
    _v07_require(
        len(current) == 1
        and current[0]['compiled_plan'] == context['compiled_plan']
        and current[0]['config']['RUN_ID'] == context['config']['RUN_ID'],
        'Cell 3 context changed after this graph was built',
    )

    groups = [group for group in pipeline_report.get('groups', [])
              if (group.get('source'), group.get('model')) == route]
    _v07_require(len(groups) == 1 and groups[0]['load'].get('validation_passed') is True,
                 'The SSP route lacks successful Cell 6 graph validation')

    source = namespace['SOURCE_INPUTS'].get(route[0])
    _v07_require(source is not None, 'Frozen source input is missing')

    def read(frame, columns):
        _v07_require(hasattr(frame, 'columns') and set(columns).issubset(frame.columns),
                     'Dataframe schema differs from the verified graph contract')
        return [row.as_dict(recursive=True)
                for row in frame.select(*columns).to_local_iterator()]

    nodes = read(graph['nodes'], _V07_NODE_COLUMNS)
    edges = read(graph['edges'], _V07_EDGE_COLUMNS)
    sources = read(source['source_df'], ('SOURCE_RECORD_ID', 'CURATED_JSON'))

    report = _v07_check(namespace, context, nodes, edges, sources)
    report['RUN_ID'] = config.get('RUN_ID')
    report['SOURCE_KEY'] = route[0]
    return report


SSP_VALIDATION_07_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_07_REPORT = run_ssp_validation_07(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v07_error:
        SSP_VALIDATION_07_REPORT = {
            'VALIDATION': '07_SSP_SYSTEM_CHARACTERISTICS_REMAINING_MAPPINGS',
            'STATUS': 'BLOCKED',
            'REASON': str(_v07_error),
            'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 07 ===')
    print(_v07_json.dumps(SSP_VALIDATION_07_REPORT, indent=2))
