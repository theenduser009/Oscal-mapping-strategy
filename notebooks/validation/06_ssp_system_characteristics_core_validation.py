# SSP Validation 06 - System Characteristics core source-to-payload checks
# 2026-09-15. READ ONLY. Run in the existing successful SSP PREVIEW session.
# Scope: system-name, system-name-short, description, and system-ids[].id only.
# Does not run the mapper, read target tables, or perform writes.

import json as _v06_json
import re as _v06_re
from collections import Counter as _v06_Counter, defaultdict as _v06_defaultdict

_V06_BASE = 'system-security-plan.system-characteristics'
_V06_IDS = _V06_BASE + '.system-ids[]'
_V06_NODE_COLUMNS = (
    'NODE_KEY', 'ELEMENT_PATH', 'PARENT_NODE_PATH', 'INSTANCE_KEY',
    'PARENT_INSTANCE_KEY', 'OSCAL_UUID', 'ELEMENT_TYPE', 'METADATA_JSON',
    'SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME', 'SOURCE_RECORD_ID', 'DW_PIPELINE_RUN_ID',
)
_V06_EDGE_COLUMNS = (
    'EDGE_KEY', 'FK_SOURCE_ELEMENT_HASH', 'FK_TARGET_ELEMENT_HASH',
    'DEPENDENCY_TYPE', 'SOURCE_OSCAL_UUID', 'TARGET_OSCAL_UUID',
)


def _v06_require(condition, message):
    if not condition:
        raise ValueError(message)


def _v06_text(value):
    return isinstance(value, str) and bool(value.strip())


def _v06_object(value):
    value = _v06_json.loads(value) if isinstance(value, str) else value
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    _v06_json.dumps(value, allow_nan=False)
    return value


def _v06_source_value(source, field):
    if field in source:
        return source[field]
    current = source
    for token in filter(None, _v06_re.split(r'[./]', str(field))):
        if isinstance(current, dict):
            current = current.get(token, current.get(token.upper()))
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return None
    return current


def _v06_scalar_text(value):
    if value is None or isinstance(value, (dict, list)):
        raise ValueError('System ID must be scalar')
    if isinstance(value, bool):
        text = 'true' if value else 'false'
    else:
        text = str(value).strip()
    if not text or text.lower() in {'nan', 'inf', '+inf', '-inf'}:
        raise ValueError('System ID must be finite and nonblank')
    return text


def _v06_expected_ids(raw, target):
    if raw in (None, '', [], {}):
        return set()
    result = set()
    for member in (raw if isinstance(raw, list) else [raw]):
        if isinstance(member, dict):
            current = member
            for token in target.split('.'):
                current = current.get(token) if isinstance(current, dict) else None
            member = current
        result.add(_v06_scalar_text(member))
    return result


def _v06_check_rows(context, nodes, edges, sources):
    config = context['config']
    registry = context['registry_rows']
    plan = context['compiled_plan']
    _v06_require(registry and all(isinstance(r, dict) and 'NODE_PATH' in r for r in registry),
                 'registry_rows must contain compiled registry dictionaries')
    paths = {r['NODE_PATH']: r for r in registry}
    _v06_require(_V06_BASE in paths and _V06_IDS in paths,
                 'Compiled System Characteristics core registry rows are missing')

    scalar_specs = {
        'system-name': ('AUTHORIZATION_PACKAGE_NAME', 'text'),
        'system-name-short': ('ACRONYM', 'text'),
        'description': ('MISSION_PURPOSE', 'text'),
    }
    scalar_rules = {}
    for member, (field, transform) in scalar_specs.items():
        matches = [r for r in context['mapping_rows']
                   if r.get('CANONICAL_ELEMENT_PATH') == _V06_BASE + '.' + member]
        _v06_require(len(matches) == 1, 'Need exactly one compiled rule for ' + member)
        rule = matches[0]
        _v06_require(rule.get('SOURCE_FIELD_NAME') == field
                     and rule.get('EXECUTION_STATUS') == 'APPROVED'
                     and rule.get('TRANSFORM_ID') == transform,
                     'Unexpected compiled rule for ' + member)
        scalar_rules[member] = rule

    id_matches = [r for r in context['mapping_rows']
                  if r.get('CANONICAL_ELEMENT_PATH') == _V06_IDS + '.id']
    _v06_require(len(id_matches) == 1, 'Need exactly one compiled system-id rule')
    id_rule = id_matches[0]
    _v06_require(id_rule.get('SOURCE_FIELD_NAME') == 'SAP_ID'
                 and id_rule.get('EXECUTION_STATUS') == 'APPROVED'
                 and id_rule.get('TRANSFORM_ID') == 'direct'
                 and id_rule.get('OWNER_ELEMENT_PATH') == _V06_IDS
                 and id_rule.get('REPRESENTATION') == 'values',
                 'Unexpected compiled system-id contract')
    id_target = (id_rule.get('REPRESENTATION_PARAMS') or {}).get('target')
    _v06_require(id_target == 'id', 'System-id target must compile to id')

    failures = _v06_Counter()
    def bad(name, count=1):
        failures[name] += count

    source_by_id = {}
    for row in sources:
        sid = row['SOURCE_RECORD_ID']
        if not _v06_text(sid) or sid in source_by_id:
            bad('SOURCE_ID_MISSING_OR_DUPLICATE')
            continue
        try:
            raw = row['CURATED_JSON']
            source_by_id[sid] = {} if raw is None and plan['options'].get('null_source_as_empty') else _v06_object(raw)
        except (ValueError, TypeError):
            bad('INVALID_SOURCE_JSON')
            source_by_id[sid] = {}
    if not sources:
        bad('NO_SOURCE_RECORDS')

    branch = [n for n in nodes if n['ELEMENT_PATH'] == _V06_BASE
              or n['ELEMENT_PATH'].startswith(_V06_BASE + '.')]
    core = [n for n in branch if n['ELEMENT_PATH'] in {_V06_BASE, _V06_IDS}]
    by_key = {n['NODE_KEY']: n for n in nodes}
    core_by_record = _v06_defaultdict(list)
    ids_by_record = _v06_defaultdict(list)
    scalar_checks = _v06_Counter()

    for node in core:
        sid, path = node['SOURCE_RECORD_ID'], node['ELEMENT_PATH']
        if sid not in source_by_id:
            bad('NODE_WITHOUT_SOURCE_RECORD')
        if not _v06_text(node.get('NODE_KEY')) or not _v06_text(node.get('INSTANCE_KEY')):
            bad('MISSING_NODE_OR_INSTANCE_KEY')
        if node.get('DW_PIPELINE_RUN_ID') != config['RUN_ID']:
            bad('STALE_NODE_RUN_ID')
        if any(node.get(k) != config[k] for k in ('SOURCE_SYSTEM_NAME', 'SOURCE_TABLE_NAME')):
            bad('WRONG_SOURCE_NAMESPACE')
        spec = paths.get(path)
        if spec is None or node.get('PARENT_NODE_PATH') != (spec.get('PARENT_NODE_PATH') or None):
            bad('REGISTRY_PARENT_PATH_MISMATCH')
        try:
            payload = _v06_object(node['METADATA_JSON'])
        except (ValueError, TypeError):
            bad('INVALID_PAYLOAD_OBJECT')
            payload = {}

        if path == _V06_BASE:
            core_by_record[sid].append(node)
            source = source_by_id.get(sid, {})
            for member, rule in scalar_rules.items():
                expected = _v06_source_value(source, rule['SOURCE_FIELD_NAME'])
                if expected in (None, '', [], {}):
                    if member in payload:
                        bad('UNEXPECTED_' + member.upper().replace('-', '_'))
                    continue
                scalar_checks[member] += 1
                if not _v06_text(expected):
                    bad('SOURCE_NOT_TEXT_' + member.upper().replace('-', '_'))
                elif payload.get(member) != expected:
                    bad('SOURCE_MISMATCH_' + member.upper().replace('-', '_'))
        elif path == _V06_IDS:
            value = payload.get('id')
            if not _v06_text(value):
                bad('INVALID_SYSTEM_ID_PAYLOAD')
            else:
                ids_by_record[sid].append(value)

    for sid, source in source_by_id.items():
        if len(core_by_record[sid]) != 1:
            bad('SYSTEM_CHARACTERISTICS_NOT_EXACTLY_ONCE_PER_SOURCE')
        try:
            expected_ids = _v06_expected_ids(_v06_source_value(source, id_rule['SOURCE_FIELD_NAME']), id_target)
        except ValueError:
            bad('INVALID_SOURCE_SYSTEM_ID_SHAPE')
            expected_ids = set()
        actual_ids = ids_by_record[sid]
        if len(actual_ids) != len(set(actual_ids)):
            bad('DUPLICATE_SYSTEM_ID_WITHIN_SSP')
        if set(actual_ids) != expected_ids:
            bad('SOURCE_MISMATCH_SYSTEM_IDS')

    core_keys = {n['NODE_KEY'] for n in core}
    incoming = _v06_Counter()
    edge_count = 0
    for edge in edges:
        tk = edge['FK_TARGET_ELEMENT_HASH']
        if tk not in core_keys:
            continue
        edge_count += 1
        parent, child = by_key.get(edge['FK_SOURCE_ELEMENT_HASH']), by_key.get(tk)
        if parent is None or child is None:
            bad('UNRESOLVED_CORE_EDGE_ENDPOINT')
            continue
        incoming[tk] += 1
        if (parent['SOURCE_RECORD_ID'] != child['SOURCE_RECORD_ID']
                or parent['ELEMENT_PATH'] != child['PARENT_NODE_PATH']):
            bad('CORE_EDGE_WRONG_PARENT_OR_SSP')
        if (edge['SOURCE_OSCAL_UUID'] != parent['OSCAL_UUID']
                or edge['TARGET_OSCAL_UUID'] != child['OSCAL_UUID']):
            bad('CORE_EDGE_UUID_ENDPOINT_MISMATCH')
        if edge['DEPENDENCY_TYPE'] != 'CONTAINS':
            bad('CORE_EDGE_WRONG_TYPE')
    bad('CORE_PARENT_EDGE_COUNT', sum(incoming[n['NODE_KEY']] != 1 for n in core))

    failures = {k: v for k, v in sorted(failures.items()) if v}
    return {
        'VALIDATION': '06_SSP_SYSTEM_CHARACTERISTICS_CORE',
        'VALIDATOR_VERSION': '2026-09-15-r1',
        'STATUS': 'FAIL' if failures else 'PASS',
        'SOURCE_RECORDS': len(sources),
        'SYSTEM_CHARACTERISTICS_NODES': len([n for n in core if n['ELEMENT_PATH'] == _V06_BASE]),
        'SYSTEM_ID_NODES': len([n for n in core if n['ELEMENT_PATH'] == _V06_IDS]),
        'SCALAR_VALUES_CHECKED': dict(scalar_checks),
        'SYSTEM_IDS_CHECKED': sum(len(v) for v in ids_by_record.values()),
        'CORE_RELATED_EDGES': edge_count,
        'FAILURE_COUNTS': failures,
        'NOT_TESTED': [
            'System Characteristics props', 'status/state/remarks', 'authorization boundary',
            'date-authorized', 'security-impact-level', 'full OSCAL schema conformance',
            'business approval of field meanings', 'target persistence'
        ],
        'WRITES_PERFORMED_BY_VALIDATOR': False,
    }


def run_ssp_validation_06(namespace):
    required = ('SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE', 'PIPELINE_REPORT',
                'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS')
    _v06_require(all(k in namespace for k in required), 'Existing seven-cell session is incomplete')
    _v06_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    config, report = namespace['CONFIG'], namespace['PIPELINE_REPORT']
    _v06_require(config.get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    _v06_require(namespace['OSCAL_LOAD_MODE'] == 'PREVIEW' and isinstance(report, dict)
                 and report.get('mode') == 'PREVIEW' and report.get('status') == 'PREVIEW_COMPLETE'
                 and report.get('writes_executed') is False and report.get('commit_attempted') is False,
                 'A completed no-write PREVIEW is required')
    graphs = namespace['MODEL_GRAPHS']
    routes = [k for k in graphs if isinstance(k, tuple) and len(k) == 2 and k[1] == 'SSP']
    _v06_require(len(routes) == 1, 'Need exactly one SSP preview route')
    key, graph = routes[0], graphs[routes[0]]
    _v06_require(all(k in graph for k in ('nodes', 'edges', 'context')), 'Cell 7 graph contract mismatch')
    ctx = graph['context']
    _v06_require(all(k in ctx for k in ('registry_rows', 'compiled_plan', 'mapping_rows', 'config', 'routing_report')),
                 'Graph context contract mismatch')
    _v06_require(ctx['config'].get('RUN_ID') == config.get('RUN_ID')
                 and ctx['config'].get('EXECUTE_WRITES') is False
                 and ctx['routing_report'].get('STATUS') == 'READY', 'Stale or blocked graph context')
    _v06_require(ctx['compiled_plan'].get('release') == 'lean-csv-registry-v4', 'Unsupported compiler release')
    current = [c for c in namespace['MAPPING_CONTEXTS']
               if (c.get('source_key'), c.get('config', {}).get('OSCAL_MODEL')) == key]
    _v06_require(len(current) == 1 and current[0]['compiled_plan'] == ctx['compiled_plan']
                 and current[0]['config']['RUN_ID'] == ctx['config']['RUN_ID'],
                 'Cell 3 context changed after this graph was built')
    groups = [g for g in report.get('groups', []) if (g.get('source'), g.get('model')) == key]
    _v06_require(len(groups) == 1 and groups[0]['load'].get('validation_passed') is True,
                 'The SSP route lacks successful Cell 6 graph validation')
    source = namespace['SOURCE_INPUTS'].get(key[0])
    _v06_require(source is not None, 'Frozen source input is missing')

    def read(frame, columns):
        _v06_require(hasattr(frame, 'columns') and set(columns).issubset(frame.columns),
                     'Dataframe schema differs from verified contract')
        return [r.as_dict(recursive=True) for r in frame.select(*columns).to_local_iterator()]

    nodes = read(graph['nodes'], _V06_NODE_COLUMNS)
    edges = read(graph['edges'], _V06_EDGE_COLUMNS)
    sources = read(source['source_df'], ('SOURCE_RECORD_ID', 'CURATED_JSON'))
    report_out = _v06_check_rows(ctx, nodes, edges, sources)
    report_out['RUN_ID'] = config.get('RUN_ID')
    report_out['SOURCE_KEY'] = key[0]
    return report_out


SSP_VALIDATION_06_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_06_REPORT = run_ssp_validation_06(globals())
    except (ValueError, TypeError, KeyError, AttributeError) as _v06_error:
        SSP_VALIDATION_06_REPORT = {
            'VALIDATION': '06_SSP_SYSTEM_CHARACTERISTICS_CORE', 'STATUS': 'BLOCKED',
            'REASON': str(_v06_error), 'WRITES_PERFORMED_BY_VALIDATOR': False,
        }
    print('=== SSP VALIDATION 06 ===')
    print(_v06_json.dumps(SSP_VALIDATION_06_REPORT, indent=2))
