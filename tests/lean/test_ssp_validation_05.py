"""Validator regression tests using actual Cells 1-7 and a minimal frame adapter.
No Snowflake connection. The adapter implements only the frame operations used
by the pure compiler/Metadata builder, targetless Cell 6, Cell 7, and validator.
These tests are NOT Snowpark SQL-engine or live database acceptance tests.
Run: python -m unittest discover -s tests/lean -p test_ssp_validation_05.py -v
"""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / 'notebooks/validation/05_ssp_metadata_graph_validation.py'
API = runpy.run_path(str(VALIDATOR), run_name='validation_05_test_import')


class Row(dict):
    def as_dict(self, recursive=False):
        return dict(self)


class Frame:
    def __init__(self, rows, columns):
        self.data = [Row(row) for row in rows]
        self.columns = list(columns)

    def to_local_iterator(self):
        return iter(self.data)

    def select(self, *columns):
        if not set(columns).issubset(self.columns):
            raise AssertionError('Test adapter: unknown selected column')
        return Frame([{k: row[k] for k in columns} for row in self.data], columns)

    def count(self):
        return len(self.data)


class StructField:
    def __init__(self, name, dtype):
        self.name = name


class Session:
    def create_dataframe(self, values, schema):
        names = [field.name for field in schema]
        return Frame([dict(zip(names, row)) for row in values], names)

    def sql(self, *args, **kwargs):
        raise AssertionError('No SQL/database action is allowed in this local test')

    def table(self, *args, **kwargs):
        raise AssertionError('No database table access is allowed in this local test')


def load_actual_cells():
    # Preserve functions verbatim. Skip only deployment imports/input execution.
    ns = {'session': Session(), 'StringType': lambda: None,
          'TimestampType': lambda _: None, 'TimestampTimeZone': type('TZ', (), {'TZ': 'TZ'}),
          'StructField': StructField, 'StructType': list}
    with contextlib.redirect_stdout(io.StringIO()):
        for file in sorted((ROOT / 'notebooks/cells').glob('[0-9][0-9]_*.py')):
            tree = ast.parse(file.read_text())
            number = int(file.name[:2])
            keep = []
            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('snowflake'):
                    continue
                targets = {t.id for t in getattr(node, 'targets', ()) if isinstance(t, ast.Name)}
                if number == 1 and 'session' in targets:
                    continue
                if number == 2 and not isinstance(node, ast.FunctionDef):
                    continue
                if number == 3 and ('MAPPING_CONTEXTS' in targets or isinstance(node, ast.Expr)):
                    continue
                if number == 7 and (targets & {'MODEL_GRAPHS', 'PIPELINE_REPORT'} or isinstance(node, ast.Try)):
                    continue
                keep.append(node)
            exec(compile(ast.Module(body=keep, type_ignores=[]), str(file), 'exec'), ns)
    return ns


def make_preview():
    ns = load_actual_cells()
    # Synthetic test-only destination: exercises actual graph validator without DDL/DML.
    ns['MODEL_CONTRACTS']['SSP']['STORAGE_CONTRACT'] = None
    profile = copy.deepcopy(ns['SOURCE_PROFILES'][0])
    profile['MAPPING_FILE'] = str(ROOT / 'Mapping/ARCHER_OSCAL_MAPPINGS.csv')
    mapping = [r for r in ns['load_mapping_rows'](profile) if r['OSCAL_MODEL'] == 'SSP - Metadata']
    base = 'system-security-plan'
    def registry(path, operator, policy, identity='SINGLETON', item=None):
        return {'OSCAL_MODEL_KEY': 'SSP', 'NODE_PATH': path,
                'ELEMENT_TYPE': path.rsplit('.', 1)[-1].replace('[]', ''),
                'PARENT_NODE_PATH': path.rsplit('.', 1)[0] if '.' in path else None,
                'IS_COLLECTION': path.endswith('[]'), 'INSTANCE_KEY_RULE': identity,
                'ITEM_PATH': item, 'PROCESS_ORDER': path.count('.') + 1,
                'IS_ACTIVE': True, 'OPERATOR': operator, 'UUID_POLICY': policy, 'REQUIRED_MEMBERS': None}
    rows = [registry(base, 'object', 'node'), registry(base + '.metadata', 'object', 'omit'),
            registry(base + '.metadata.document-ids[]', 'values', 'omit', 'VALUE', '$'),
            registry(base + '.metadata.roles[]', 'roles', 'omit', 'SOURCE_FIELD_NAME', '$'),
            registry(base + '.metadata.parties[]', 'parties', 'instance', 'ID', 'UserList[]'),
            registry(base + '.metadata.responsible-parties[]', 'assignments', 'omit', 'SOURCE_FIELD_NAME+ID', 'UserList[]')]
    contexts = ns['compile_mapping_contexts']({'source-one': mapping}, rows, [profile],
                                             ns['MODEL_CONTRACTS'], ns['ROUTING_METADATA'])
    assert contexts[0]['routing_report']['STATUS'] == 'READY'
    source_rows = []
    for i in (1, 2):
        payload = {'AUTHORIZATION_PACKAGE_NAME': 'Synthetic SSP ' + str(i),
                   'TRACKING_ID': 'SYN-DOC-' + str(i),
                   'FIRST_PUBLISHED': '2020-01-01 01:02:03.000',
                   'LAST_UPDATED': '2021-01-01 01:02:03.000',
                   'INFORMATION_OWNER_IO': {'UserList': [{'Id': str(100 + i)}]},
                   'INFORMATION_SYSTEM_OWNER_ISO': {'UserList': [{'Id': str(200 + i)}, {'Id': str(100 + i)}]}}
        source_rows.append({'SOURCE_RECORD_ID': 'SYNTHETIC-' + str(i), 'CURATED_JSON': json.dumps(payload)})
    sources = {'source-one': {'source_df': Frame(source_rows, ('SOURCE_RECORD_ID', 'CURATED_JSON')),
                              'selection': {'SELECTED_ROWS': 2}, 'lookups': {}}}
    graphs, report = ns['run_oscal_pipeline'](sources, contexts, 'PREVIEW')
    ns.update(SOURCE_INPUTS=sources, MAPPING_CONTEXTS=contexts, MODEL_GRAPHS=graphs,
              PIPELINE_REPORT=report, REGISTRY_INPUT_ROWS=rows)
    return ns


class Validator05Tests(unittest.TestCase):
    def setUp(self):
        self.ns = make_preview()
        self.graph = self.ns['MODEL_GRAPHS'][('source-one', 'SSP')]

    def validate(self):
        return API['run_ssp_validation_05'](self.ns)

    def node(self, suffix, record='SYNTHETIC-1'):
        return next(r for r in self.graph['nodes'].data if r['ELEMENT_PATH'].endswith(suffix)
                    and r['SOURCE_RECORD_ID'] == record)

    def change_payload(self, suffix, transform, record='SYNTHETIC-1'):
        node = self.node(suffix, record)
        payload = json.loads(node['METADATA_JSON'])
        transform(payload)
        node['METADATA_JSON'] = json.dumps(payload)

    def assert_failure(self, reason):
        result = self.validate()
        self.assertEqual('FAIL', result['STATUS'])
        self.assertGreater(result['FAILURE_COUNTS'].get(reason, 0), 0)

    def test_actual_seven_cell_metadata_pipeline_passes(self):
        result = self.validate()
        self.assertEqual('PASS', result['STATUS'])
        self.assertEqual(2, result['SOURCE_RECORDS'])
        self.assertEqual({'title': 2, 'version': 2, 'oscal-version': 2}, result['SCALAR_VALUES_CHECKED'])
        self.assertEqual(6, result['PARTY_REFERENCES_CHECKED'])
        self.assertEqual('EXERCISED', result['ROLE_PARTY_REFERENCE_COVERAGE'])

    def test_actual_context_uses_registry_rows(self):
        self.assertIn('registry_rows', self.graph['context'])
        self.assertNotIn('ELEMENT_REGISTRY', self.graph['context'])
        self.assertEqual('PASS', self.validate()['STATUS'])

    def test_rejects_old_registry_key_before_data_reads(self):
        ctx = self.graph['context']
        ctx['ELEMENT_REGISTRY'] = ctx.pop('registry_rows')
        with self.assertRaisesRegex(ValueError, 'registry_rows'):
            self.validate()

    def test_rejects_physical_pk_instead_of_node_key(self):
        self.graph['nodes'].columns.remove('NODE_KEY')
        self.graph['nodes'].columns.append('PK_ELEMENT_HASH')
        with self.assertRaisesRegex(ValueError, 'schema'):
            self.validate()

    def test_omit_payload_uuid_still_allows_graph_uuid(self):
        n = self.node('.metadata')
        self.assertTrue(n['OSCAL_UUID'])
        self.assertNotIn('uuid', json.loads(n['METADATA_JSON']))
        self.assertEqual('PASS', self.validate()['STATUS'])

    def test_payload_uuid_must_equal_graph_uuid(self):
        self.change_payload('.parties[]', lambda p: p.update(uuid='00000000-0000-4000-8000-000000000001'))
        self.assert_failure('PAYLOAD_UUID_MISMATCH')

    def test_wrong_valid_uuid_on_edge_detected(self):
        self.graph['edges'].data[0]['SOURCE_OSCAL_UUID'] = self.node('.parties[]')['OSCAL_UUID']
        self.assert_failure('EDGE_UUID_ENDPOINT_MISMATCH')

    def test_cross_ssp_parent_edge_detected(self):
        a = self.node('.metadata')
        b = self.node('system-security-plan', 'SYNTHETIC-2')
        edge = next(e for e in self.graph['edges'].data if e['FK_TARGET_ELEMENT_HASH'] == a['NODE_KEY'])
        edge['FK_SOURCE_ELEMENT_HASH'], edge['SOURCE_OSCAL_UUID'] = b['NODE_KEY'], b['OSCAL_UUID']
        self.assert_failure('EDGE_WRONG_PARENT_OR_SSP')

    def test_party_present_in_other_ssp_does_not_resolve(self):
        foreign = self.node('.parties[]', 'SYNTHETIC-2')['OSCAL_UUID']
        self.change_payload('.responsible-parties[]', lambda p: p.update({'party-uuids': [foreign]}))
        self.assert_failure('PARTY_REFERENCE_NOT_IN_SAME_SSP')

    def test_bad_role_reference_detected(self):
        self.change_payload('.responsible-parties[]', lambda p: p.update({'role-id': 'undefined'}))
        self.assert_failure('ROLE_REFERENCE_NOT_IN_SAME_SSP')

    def test_malformed_party_reference_detected(self):
        self.change_payload('.responsible-parties[]', lambda p: p.update({'party-uuids': ['not-a-uuid']}))
        self.assert_failure('INVALID_PARTY_UUID_REFERENCE')

    def test_duplicate_party_reference_detected(self):
        self.change_payload('.responsible-parties[]', lambda p: p.update({'party-uuids': p['party-uuids'] * 2}))
        self.assert_failure('DUPLICATE_PARTY_REFERENCE')

    def test_missing_party_list_detected(self):
        self.change_payload('.responsible-parties[]', lambda p: p.pop('party-uuids'))
        self.assert_failure('MISSING_PARTY_UUID_LIST')

    def test_empty_title_detected(self):
        self.change_payload('.metadata', lambda p: p.update(title=''))
        self.assert_failure('MISSING_OR_NONSTRING_TITLE')

    def test_wrong_title_even_if_nonblank_detected(self):
        self.change_payload('.metadata', lambda p: p.update(title='Incorrect but nonblank'))
        self.assert_failure('SOURCE_MISMATCH_TITLE')

    def test_wrong_config_version_detected(self):
        self.change_payload('.metadata', lambda p: p.update(version='wrong-version'))
        self.assert_failure('SOURCE_MISMATCH_VERSION')

    def test_invalid_json_detected(self):
        self.node('.metadata')['METADATA_JSON'] = '{invalid'
        self.assert_failure('INVALID_PAYLOAD_OBJECT')

    def test_missing_metadata_for_one_source_is_not_a_pass(self):
        missing = self.node('.metadata')
        self.graph['nodes'].data.remove(missing)
        self.assert_failure('METADATA_NOT_EXACTLY_ONCE_PER_SOURCE')

    def test_no_metadata_is_not_a_pass(self):
        self.graph['nodes'].data = [n for n in self.graph['nodes'].data if '.metadata' not in n['ELEMENT_PATH']]
        self.assert_failure('NO_METADATA_NODES')

    def test_missing_edge_detected(self):
        self.graph['edges'].data.pop(0)
        self.assert_failure('METADATA_PARENT_EDGE_COUNT')

    def test_stale_node_detected(self):
        self.node('.metadata')['DW_PIPELINE_RUN_ID'] = 'old-run'
        self.assert_failure('STALE_NODE_RUN_ID')

    def test_mixed_config_and_graph_run_blocked(self):
        self.ns['CONFIG']['RUN_ID'] = 'a-new-run'
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.validate()

    def test_a_commit_report_cannot_be_relabelled_by_switch_only(self):
        self.ns['PIPELINE_REPORT']['mode'] = 'COMMIT'
        with self.assertRaisesRegex(ValueError, 'no-write PREVIEW'):
            self.validate()

    def test_changed_compiled_plan_blocked(self):
        self.ns['MAPPING_CONTEXTS'][0]['compiled_plan']['release'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'Cell 3 context changed'):
            self.validate()

    def test_no_mutation_of_preview_or_source(self):
        before = copy.deepcopy((self.graph, self.ns['SOURCE_INPUTS']))
        self.validate()
        self.assertEqual(before[0]['context'], self.graph['context'])
        self.assertEqual(before[0]['nodes'].data, self.graph['nodes'].data)
        self.assertEqual(before[0]['edges'].data, self.graph['edges'].data)
        self.assertEqual(before[1]['source-one']['source_df'].data,
                         self.ns['SOURCE_INPUTS']['source-one']['source_df'].data)

    def test_report_omits_private_record_values(self):
        text = json.dumps(self.validate())
        for private in ('SYNTHETIC-1', 'Synthetic SSP 1', self.node('.parties[]')['OSCAL_UUID']):
            self.assertNotIn(private, text)

    def test_timestamps_remain_explicitly_out_of_scope(self):
        result = self.validate()
        self.assertEqual('PASS', result['STATUS'])
        self.assertIn('DEFERRED_SME', result['TIMESTAMPS'])

    def test_script_cell_entrypoint_needs_no_prior_validation_imports(self):
        clean = {k: self.ns[k] for k in ('SELECTED_MODELS', 'CONFIG', 'OSCAL_LOAD_MODE',
                 'PIPELINE_REPORT', 'MODEL_GRAPHS', 'MAPPING_CONTEXTS', 'SOURCE_INPUTS')}
        clean['__name__'] = '__main__'
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(VALIDATOR.read_text(), str(VALIDATOR), 'exec'), clean)
        self.assertEqual('PASS', clean['SSP_VALIDATION_05_REPORT']['STATUS'])


if __name__ == '__main__':
    unittest.main()
