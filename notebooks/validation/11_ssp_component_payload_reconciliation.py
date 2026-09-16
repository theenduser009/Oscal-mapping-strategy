# SSP Validation 11 - focused system-implementation.components[] reconciliation
# 2026-09-16. READ ONLY. Run in the existing successful SSP PREVIEW session.
# Purpose: isolate the 4,792 component payload mismatches reported by Validation 10.
# This validator reproduces Cell 5 behavior more exactly: it calls _metadata_prepare,
# rebuilds component instances, then applies _metadata_payload with the actual node UUID
# before comparing to candidate-graph METADATA_JSON.

import copy as _v11_copy
import json as _v11_json
from collections import Counter as _v11_Counter

_V11_PATH = 'system-security-plan.system-implementation.components[]'
_V11_NODE_COLUMNS = (
    'NODE_KEY','ELEMENT_PATH','INSTANCE_KEY','OSCAL_UUID','METADATA_JSON',
    'SOURCE_RECORD_ID','PARENT_NODE_PATH','PARENT_INSTANCE_KEY'
)


def _v11_require(cond, msg):
    if not cond:
        raise ValueError(msg)


def _v11_obj(value):
    if isinstance(value, str):
        value = _v11_json.loads(value)
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object')
    return value


def run_ssp_validation_11(namespace):
    required = (
        'SELECTED_MODELS','CONFIG','OSCAL_LOAD_MODE','PIPELINE_REPORT','MODEL_GRAPHS',
        'SOURCE_INPUTS','_canonical_registry_rows','_metadata_prepare','_metadata_parse',
        '_metadata_instances','_metadata_payload'
    )
    _v11_require(all(k in namespace for k in required), 'Existing seven-cell SSP session is incomplete')
    _v11_require(tuple(namespace['SELECTED_MODELS']) == ('SSP',), 'Select SSP only')
    _v11_require(namespace['CONFIG'].get('EXECUTE_WRITES') is False, 'Keep EXECUTE_WRITES=False')
    _v11_require(namespace['OSCAL_LOAD_MODE'] == 'PREVIEW' and
                 namespace['PIPELINE_REPORT'].get('status') == 'PREVIEW_COMPLETE',
                 'A completed SSP PREVIEW is required')

    routes = [k for k in namespace['MODEL_GRAPHS'] if isinstance(k, tuple) and len(k) == 2 and k[1] == 'SSP']
    _v11_require(len(routes) == 1, 'Need exactly one SSP preview route')
    route = routes[0]
    graph = namespace['MODEL_GRAPHS'][route]
    context = graph['context']
    source_df = namespace['SOURCE_INPUTS'][route[0]]['source_df']

    # Reproduce Cell 5 preparation, including component hydration lookup construction.
    expected_ctx = _v11_copy.copy(context)
    expected_ctx['graph_report'] = {
        'SOURCE_RECORDS':0,'INVALID_SOURCE_RECORDS':0,'DUPLICATE_SOURCE_RECORDS':0,
        'MAPPED_VALUES':0,'MISSING_VALUES':0,'STATUS':'VALIDATION_EXPECTED_BUILD',
        'OUTPUTS_PUBLISHED':False,
    }
    expected_ctx.pop('_metadata_reference_cache', None)
    namespace['_metadata_prepare'](source_df, expected_ctx)

    registry = namespace['_canonical_registry_rows'](None, 'SSP', expected_ctx)
    row = next((r for r in registry if r['element_path'] == _V11_PATH), None)
    _v11_require(row is not None, 'Component registry path is not active')

    actual_nodes = [r.as_dict(recursive=True) for r in
                    graph['nodes'].select(*_V11_NODE_COLUMNS).filter(
                        graph['nodes']['ELEMENT_PATH'] == _V11_PATH
                    ).to_local_iterator()]
    actual_by_record = {}
    for node in actual_nodes:
        actual_by_record.setdefault(str(node['SOURCE_RECORD_ID']), {})[node['INSTANCE_KEY']] = node

    failures = _v11_Counter()
    expected_count = 0
    compared = 0
    examples = []

    for source_row in source_df.select('SOURCE_RECORD_ID','CURATED_JSON').to_local_iterator():
        sid = str(source_row['SOURCE_RECORD_ID'])
        source_obj = namespace['_metadata_parse'](source_row.as_dict(recursive=True), expected_ctx)
        expected_instances = namespace['_metadata_instances'](source_obj, sid, row, expected_ctx)
        expected_count += len(expected_instances)
        actual = actual_by_record.get(sid, {})

        expected_keys = {item['instance_key'] for item in expected_instances}
        if expected_keys != set(actual):
            failures['INSTANCE_SET_MISMATCH'] += 1

        for item in expected_instances:
            key = item['instance_key']
            node = actual.get(key)
            if node is None:
                continue
            # Cell 5 finalizes instance payload with the node UUID before persistence.
            expected_payload = namespace['_metadata_payload'](
                _V11_PATH, item['payload'], node['OSCAL_UUID'], expected_ctx
            )
            actual_payload = _v11_obj(node['METADATA_JSON'])
            compared += 1
            if expected_payload != actual_payload:
                failures['COMPONENT_PAYLOAD_MISMATCH'] += 1
                if len(examples) < 5:
                    examples.append({
                        'SOURCE_RECORD_ID': sid,
                        'INSTANCE_KEY': key,
                        'EXPECTED_PAYLOAD': expected_payload,
                        'ACTUAL_PAYLOAD': actual_payload,
                    })

    failures = {k:v for k,v in sorted(failures.items()) if v}
    return {
        'VALIDATION':'11_SSP_COMPONENT_PAYLOAD_RECONCILIATION',
        'VALIDATOR_VERSION':'2026-09-16-r1',
        'STATUS':'FAIL' if failures else 'PASS',
        'COMPONENT_PATH':_V11_PATH,
        'ACTUAL_COMPONENT_NODES':len(actual_nodes),
        'EXPECTED_COMPONENT_INSTANCES':expected_count,
        'COMPONENT_PAYLOADS_COMPARED':compared,
        'FAILURE_COUNTS':failures,
        'MISMATCH_EXAMPLES':examples,
        'INTERPRETATION':(
            'PASS means Validation 10 component mismatches were caused by an incomplete expected-payload comparison, '
            'not by the mapper output.' if not failures else
            'FAIL means component payloads still differ after reproducing Cell 5 preparation and UUID finalization; inspect examples before changing mapper code.'
        ),
        'WRITES_PERFORMED_BY_VALIDATOR':False,
        'RUN_ID':namespace['CONFIG'].get('RUN_ID'),
        'SOURCE_KEY':route[0],
    }


SSP_VALIDATION_11_REPORT = None
if __name__ == '__main__':
    try:
        SSP_VALIDATION_11_REPORT = run_ssp_validation_11(globals())
    except (ValueError,TypeError,KeyError,AttributeError) as _v11_error:
        SSP_VALIDATION_11_REPORT = {
            'VALIDATION':'11_SSP_COMPONENT_PAYLOAD_RECONCILIATION',
            'STATUS':'BLOCKED','REASON':str(_v11_error),
            'WRITES_PERFORMED_BY_VALIDATOR':False,
        }
    print('=== SSP VALIDATION 11 ===')
    print(_v11_json.dumps(SSP_VALIDATION_11_REPORT, indent=2, default=str))
