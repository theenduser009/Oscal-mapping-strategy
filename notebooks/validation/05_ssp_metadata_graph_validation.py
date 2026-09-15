# SSP Validation 05 - Metadata graph and selected payload checks
# Revised 2026-09-15. Replaces the invalid earlier 05 at this SAME path.
# Run this file in one Python cell in the EXISTING successful SSP PREVIEW session.
# Does not run the pipeline, call the loader, read target tables, or change data.
# Contract baseline: 9c28ab11fd9cdb4cfe0697da0f0ce0fbe3b70202, cells/cells_v2 identical.
# Actual handles: MODEL_GRAPHS[(source_key, 'SSP')]['context']['registry_rows'];
# candidate nodes use NODE_KEY, not a physical DIM PK column.
# Scope: parent/edge ownership; title/version/oscal-version source equality;
# role/party payload shape and responsible-party references WITHIN each SSP.
# NOT full OSCAL/schema or business-semantic approval. Timestamps remain deferred.

import json as _v05_json
import re as _v05_re
import uuid as _v05_uuid
from collections import Counter as _v05_Counter, defaultdict as _v05_defaultdict

_V05_BASE = 'system-security-plan.metadata'
_V05_NODE_COLUMNS = (
    'NODE_KEY', 'ELEMENT_PATH', 'PARENT_NODE_PATH', 'INSTANCE_KEY',
    'PARENT_INSTANCE_KEY', 'OSCAL_UUID', 'ELEMENT_TYPE', 'METADATA_JSON',
    'SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME', 'SOURCE_RECORD_ID', 'DW_PIPELINE_RUN_ID',
)
_V05_EDGE_COLUMNS = (
    'EDGE_KEY', 'FK_SOURCE_ELEMENT_HASH', 'FK_TARGET_ELEMENT_HASH',
    'DEPENDENCY_TYPE', 'SOURCE_OSCAL_UUID', 'TARGET_OSCAL_UUID',
)


def _v05_require(condition, message):
    if not condition:
        raise ValueError(message)


def _v05_text(value):
    return isinstance(value, str) and bool(value.strip())


def _v05_uuid_ok(value):
    if not isinstance(value, str):
        return False
    try:
        return str(_v05_uuid.UUID(value)) == value
    except ValueError:
        return False


def _v05_object(value):
    value = _v05_json.loads(value) if isinstance(value, str) else value
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    _v05_json.dumps(value, allow_nan=False)
    return value


def _v05_source_value(source, field):
    # Same documented path semantics: literal key first, then dotted/slash path.
    if field in source:
        return source[field]
    current = source
    for token in filter(None, _v05_re.split(r'[./]', field)):
        if isinstance(current, dict):
            current = current.get(token, current.get(token.upper()))
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return None
    return current


def _v05_check_rows(context, nodes, edges, sources):
    """Pure checks; local tests use the actual compiler/builder output contract."""
    config = context['config']
    registry = context['registry_rows']
    plan = context['compiled_plan']
    _v05_require(registry and all(isinstance(r, dict) and 'NODE_PATH' in r for r in registry),
                 'registry_rows must contain the compiled registry dictionaries')
    paths = {r['NODE_PATH']: r for r in registry}
    _v05_require(len(paths) == len(registry), 'Compiled registry paths are not unique')
    _v05_require(_V05_BASE in paths, 'Compiled Metadata registry row is missing')
    scalar_rules = {}
    for member in ('title', 'version', 'oscal-version'):
        matches = [r for r in context['mapping_rows']
                   if r.get('CANONICAL_ELEMENT_PATH') == _V05_BASE + '.' + member]
        _v05_require(len(matches) == 1, 'Need exactly one compiled rule for metadata.' + member)
        rule = matches[0]
        _v05_require(rule.get('EXECUTION_STATUS') == 'APPROVED'
                     and rule.get('TRANSFORM_ID') in ('text', 'canonical-text')
                     and _v05_text(rule.get('SOURCE_FIELD_NAME')),
                     'Unsupported validation contract for metadata.' + member)
        scalar_rules[member] = rule

    failures = _v05_Counter()
    def bad(check, count=1):
        failures[check] += count

    source_by_id = {}
    for row in sources:
        sid = row['SOURCE_RECORD_ID']
        if not _v05_text(sid) or sid in source_by_id:
            bad('SOURCE_ID_MISSING_OR_DUPLICATE')
        try:
            raw = row['CURATED_JSON']
            source_by_id[sid] = {} if raw is None and plan['options'].get('null_source_as_empty') else _v05_object(raw)
        except (ValueError, TypeError):
            bad('INVALID_SOURCE_JSON')
            source_by_id[sid] = {}
    if not sources:
        bad('NO_SOURCE_RECORDS')

    meta = [n for n in nodes if n['ELEMENT_PATH'] == _V05_BASE
            or n['ELEMENT_PATH'].startswith(_V05_BASE + '.')]
    if not meta:
        bad('NO_METADATA_NODES')
    by_key = {n['NODE_KEY']: n for n in nodes}
    for values, check in (([n['NODE_KEY'] for n in nodes], 'DUPLICATE_NODE_KEY'),
                          ([n['OSCAL_UUID'] for n in meta], 'DUPLICATE_METADATA_UUID')):
        bad(check, sum(count - 1 for count in _v05_Counter(values).values() if count > 1))
    meta_by_record = _v05_defaultdict(list)
    role_ids, party_ids = _v05_defaultdict(set), _v05_defaultdict(set)
    responsibilities = []
    member_checks = _v05_Counter()
    for node in meta:
        sid, path = node['SOURCE_RECORD_ID'], node['ELEMENT_PATH']
        if sid not in source_by_id:
            bad('NODE_WITHOUT_SOURCE_RECORD')
        if not _v05_text(node['NODE_KEY']) or not _v05_text(node['INSTANCE_KEY']):
            bad('MISSING_NODE_OR_INSTANCE_KEY')
        if not _v05_uuid_ok(node['OSCAL_UUID']):
            bad('INVALID_GRAPH_UUID')
        if node['DW_PIPELINE_RUN_ID'] != config['RUN_ID']:
            bad('STALE_NODE_RUN_ID')
        if any(node[k] != config[k] for k in ('SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME')):
            bad('WRONG_SOURCE_NAMESPACE')
        spec = paths.get(path)
        if spec is None:
            bad('UNREGISTERED_METADATA_PATH')
        elif node['PARENT_NODE_PATH'] != (spec.get('PARENT_NODE_PATH') or None):
            bad('REGISTRY_PARENT_PATH_MISMATCH')
        try:
            payload = _v05_object(node['METADATA_JSON'])
        except (ValueError, TypeError):
            bad('INVALID_PAYLOAD_OBJECT')
            payload = {}
        params = plan['elements'].get(path, {}).get('parameters', {})
        # omit governs JSON uuid emission, NOT whether OSCAL_UUID exists on a node.
        if params.get('include_uuid') and payload.get('uuid') != node['OSCAL_UUID']:
            bad('PAYLOAD_UUID_MISMATCH')
        if not params.get('include_uuid') and 'uuid' in payload:
            bad('UNEXPECTED_PAYLOAD_UUID')

        if path == _V05_BASE:
            meta_by_record[sid].append(node)
            for member, rule in scalar_rules.items():
                member_checks[member] += 1
                if not _v05_text(payload.get(member)):
                    bad('MISSING_OR_NONSTRING_' + member.upper().replace('-', '_'))
                rp = rule.get('REPRESENTATION_PARAMS') or {}
                expected = (config.get(rule['SOURCE_FIELD_NAME']) if rp.get('value_source') == 'CONFIG'
                            else _v05_source_value(source_by_id.get(sid, {}), rule['SOURCE_FIELD_NAME']))
                if not _v05_text(expected) or payload.get(member) != expected:
                    bad('SOURCE_MISMATCH_' + member.upper().replace('-', '_'))
                if rule['TRANSFORM_ID'] == 'canonical-text' and _v05_text(expected) and expected != expected.strip():
                    bad('NONCANONICAL_CONFIG_TEXT')
        elif path == _V05_BASE + '.roles[]':
            rid = payload.get('id')
            if not _v05_text(rid) or not _v05_text(payload.get('title')):
                bad('INVALID_ROLE_PAYLOAD')
            elif rid in role_ids[sid]:
                bad('DUPLICATE_ROLE_ID_WITHIN_SSP')
            else:
                role_ids[sid].add(rid)
        elif path == _V05_BASE + '.parties[]':
            pid = payload.get('uuid')
            if not _v05_uuid_ok(pid) or payload.get('type') not in ('person', 'organization'):
                bad('INVALID_PARTY_PAYLOAD')
            elif pid in party_ids[sid]:
                bad('DUPLICATE_PARTY_UUID_WITHIN_SSP')
            else:
                party_ids[sid].add(pid)
        elif path == _V05_BASE + '.responsible-parties[]':
            responsibilities.append((sid, payload))

    for sid in source_by_id:
        if len(meta_by_record[sid]) != 1:
            bad('METADATA_NOT_EXACTLY_ONCE_PER_SOURCE')
    refs_checked = 0
    for sid, payload in responsibilities:
        role, refs = payload.get('role-id'), payload.get('party-uuids')
        if not _v05_text(role) or role not in role_ids[sid]:
            bad('ROLE_REFERENCE_NOT_IN_SAME_SSP')
        if not isinstance(refs, list) or not refs:
            bad('MISSING_PARTY_UUID_LIST')
            continue
        valid_refs = [p for p in refs if _v05_uuid_ok(p)]
        bad('INVALID_PARTY_UUID_REFERENCE', len(refs) - len(valid_refs))
        bad('DUPLICATE_PARTY_REFERENCE', len(valid_refs) - len(set(valid_refs)))
        for pid in valid_refs:
            refs_checked += 1
            if pid not in party_ids[sid]:
                bad('PARTY_REFERENCE_NOT_IN_SAME_SSP')

    incoming = _v05_Counter()
    edge_keys = set()
    meta_keys = {n['NODE_KEY'] for n in meta}
    edge_count = 0
    for edge in edges:
        sk, tk = edge['FK_SOURCE_ELEMENT_HASH'], edge['FK_TARGET_ELEMENT_HASH']
        if sk not in meta_keys and tk not in meta_keys:
            continue
        edge_count += 1
        if edge['EDGE_KEY'] in edge_keys:
            bad('DUPLICATE_METADATA_EDGE')
        edge_keys.add(edge['EDGE_KEY'])
        parent, child = by_key.get(sk), by_key.get(tk)
        if parent is None or child is None:
            bad('UNRESOLVED_METADATA_EDGE_ENDPOINT')
            continue
        incoming[tk] += 1
        if (parent['SOURCE_RECORD_ID'] != child['SOURCE_RECORD_ID']
                or parent['ELEMENT_PATH'] != child['PARENT_NODE_PATH']
                or child['PARENT_INSTANCE_KEY'] is not None and child['PARENT_INSTANCE_KEY'] != parent['INSTANCE_KEY']):
            bad('EDGE_WRONG_PARENT_OR_SSP')
        if (edge['SOURCE_OSCAL_UUID'] != parent['OSCAL_UUID']
                or edge['TARGET_OSCAL_UUID'] != child['OSCAL_UUID']):
            bad('EDGE_UUID_ENDPOINT_MISMATCH')
        if edge['DEPENDENCY_TYPE'] != 'CONTAINS':
            bad('WRONG_EDGE_TYPE')
    bad('METADATA_PARENT_EDGE_COUNT', sum(incoming[n['NODE_KEY']] != 1 for n in meta))
    failures = {k: v for k, v in sorted(failures.items()) if v}
    return {
        'VALIDATION': '05_SSP_METADATA_GRAPH_AND_SELECTED_PAYLOADS',
        'VALIDATOR_VERSION': '2026-09-15-r2',
        'STATUS': 'FAIL' if failures else 'PASS',
        'SOURCE_RECORDS': len(sources), 'METADATA_BRANCH_NODES': len(meta),
        'NODE_COUNTS_BY_PATH': dict(sorted(_v05_Counter(n['ELEMENT_PATH'] for n in meta).items())),
        'SCALAR_VALUES_CHECKED': dict(member_checks), 'METADATA_RELATED_EDGES': edge_count,
        'RESPONSIBLE_PARTY_NODES': len(responsibilities), 'PARTY_REFERENCES_CHECKED': refs_checked,
        'ROLE_PARTY_REFERENCE_COVERAGE': 'EXERCISED' if responsibilities else 'NOT_EXERCISED',
        'FAILURE_COUNTS': failures,
        'TIMESTAMPS': 'KNOWN_FAILED_LEXICAL_CHECK_REMEDIATION_DEFERRED_SME',
        'NOT_TESTED': ['Full OSCAL schema conformance', 'Business approval of field meaning',
                       'Complete source-to-party assignment reconciliation', 'Target persistence',
                       'Document-ID equality/uniqueness (separate Validation 04)'],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


def run_ssp_validation_05(namespace):
    """Read the exact existing preview objects, without modifying their contents."""
    required = ('SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE', 'PIPELINE_REPORT',
                'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS')
    _v05_require(all(k in namespace for k in required), 'Existing seven-cell session is incomplete')
    _v05_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    config, report = namespace['CONFIG'], namespace['PIPELINE_REPORT']
    _v05_require(config.get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    _v05_require(namespace['OSCAL_LOAD_MODE'] == 'PREVIEW' and isinstance(report, dict)
                 and report.get('mode') == 'PREVIEW' and report.get('status') == 'PREVIEW_COMPLETE'
                 and report.get('writes_executed') is False and report.get('commit_attempted') is False,
                 'A completed no-write PREVIEW is required; mode switch alone is not evidence')
    graphs = namespace['MODEL_GRAPHS']
    _v05_require(isinstance(graphs, dict), 'MODEL_GRAPHS is missing')
    routes = [k for k in graphs if isinstance(k, tuple) and len(k) == 2 and k[1] == 'SSP']
    _v05_require(len(routes) == 1, 'Need exactly one SSP preview route')
    key, graph = routes[0], graphs[routes[0]]
    _v05_require(all(k in graph for k in ('nodes', 'edges', 'context')), 'Cell 7 graph contract mismatch')
    ctx = graph['context']
    _v05_require(all(k in ctx for k in ('registry_rows', 'compiled_plan', 'mapping_rows', 'config', 'routing_report')),
                 'Graph context requires registry_rows, compiled_plan, mapping_rows, config, routing_report')
    _v05_require(ctx['config'].get('RUN_ID') == config.get('RUN_ID')
                 and ctx['config'].get('EXECUTE_WRITES') is False
                 and ctx['routing_report'].get('STATUS') == 'READY', 'Stale or blocked graph context')
    _v05_require(ctx['compiled_plan'].get('release') == 'lean-csv-registry-v4', 'Unsupported compiler release')
    current = [c for c in namespace['MAPPING_CONTEXTS']
               if (c.get('source_key'), c.get('config', {}).get('OSCAL_MODEL')) == key]
    _v05_require(len(current) == 1 and current[0]['compiled_plan'] == ctx['compiled_plan']
                 and current[0]['config']['RUN_ID'] == ctx['config']['RUN_ID'],
                 'Cell 3 context changed after this graph was built')
    groups = [g for g in report.get('groups', []) if (g.get('source'), g.get('model')) == key]
    _v05_require(len(groups) == 1 and groups[0]['load'].get('validation_passed') is True,
                 'The SSP route lacks successful Cell 6 graph validation')
    _v05_require(key[0] in namespace['SOURCE_INPUTS'], 'Frozen source input is missing')
    source = namespace['SOURCE_INPUTS'][key[0]]

    def read(frame, columns):
        _v05_require(hasattr(frame, 'columns') and set(columns).issubset(frame.columns),
                     'Dataframe schema differs from the verified contract: ' + ', '.join(columns))
        return [r.as_dict(recursive=True) for r in frame.select(*columns).to_local_iterator()]

    # Reads only existing candidate frames and the frozen source snapshot.
    nodes = read(graph['nodes'], _V05_NODE_COLUMNS)
    edges = read(graph['edges'], _V05_EDGE_COLUMNS)
    sources = read(source['source_df'], ('SOURCE_RECORD_ID', 'CURATED_JSON'))
    expected = source.get('selection', {}).get('SELECTED_ROWS')
    _v05_require(expected is not None and len(sources) == expected, 'Frozen source count changed')
    result = _v05_check_rows(ctx, nodes, edges, sources)
    result['RUN_ID'] = ctx['config']['RUN_ID']
    result['SOURCE_KEY'] = key[0]
    return result


if __name__ == '__main__':
    try:
        SSP_VALIDATION_05_REPORT = run_ssp_validation_05(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v05_error:
        SSP_VALIDATION_05_REPORT = {
            'VALIDATION': '05_SSP_METADATA_GRAPH_AND_SELECTED_PAYLOADS', 'STATUS': 'BLOCKED',
            'REASON': str(_v05_error), 'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 05 ===')
    print(_v05_json.dumps(SSP_VALIDATION_05_REPORT, indent=2))
