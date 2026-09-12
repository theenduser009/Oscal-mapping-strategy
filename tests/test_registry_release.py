"""Released Cell One + actual mapping CSV + extended registry, with synthetic data."""
import ast
from collections import Counter
import copy
import csv
import hashlib
import json
from pathlib import Path
import runpy
import unittest

import test_metadata_driven_contract as metadata
import test_multi_model_graph as graph
import test_flat_mapping_release as previous
from test_model_selection import cell_namespace

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / 'Mapping/ARCHER_OSCAL_MAPPINGS.csv'
OLD = ROOT / 'tests/fixtures/mapper_contract_pre_registry.json'
SUPPORT = ('support:metadata-title', 'support:oscal-version', 'support:document-version')


def mapping_rows():
    with MAPPING.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def release_registry(original=None):
    """Independent migration expectation, rooted in the frozen accepted settings."""
    old = json.loads(OLD.read_text(encoding='utf-8'))
    full_old = json.loads(previous.OLD_CATALOG_PATH.read_text(encoding='utf-8'))
    originals = previous._registry_for_release(full_old) if original is None else original
    rows = []
    # These three older fixture rows omit identity columns recorded in live evidence.
    recorded = {'roles': ('SOURCE_FIELD_NAME', '$'), 'parties': ('ID', 'UserList[]'),
                'assignments': ('SOURCE_FIELD_NAME+ID', 'UserList[]')}
    for original_row in originals:
        row = dict(original_row)
        path = row['NODE_PATH']
        model = row.get('OSCAL_MODEL_KEY') or next(
            key for key, value in old['MODELS'].items() if path.startswith(value['ROOT_PATH']))
        row['OSCAL_MODEL_KEY'] = model
        contract = old['MODELS'][model]
        spec = contract['ELEMENTS'].get(path)
        if spec is None and contract.get('DEFAULT_ELEMENT') and '[]' not in path:
            spec = contract['DEFAULT_ELEMENT']
        if contract.get('ELEMENT_PATHS') and path not in contract['ELEMENT_PATHS']:
            spec = None
        row.update(MAPPER_METADATA_VERSION=None, MAPPER_ENABLED=spec is not None,
                   DEFAULT_SINGLETON_POLICY=None, REQUIRED_RULE_IDS=None,
                   REPORT_TARGET_PATH=None, ROLES_PATH=None, PARTIES_PATH=None,
                   PARTY_TYPE=None, PARTY_UUID_PARTS=None, PARTY_UUID_SOURCE_KEY=None)
        if spec is not None:
            params, operator = spec.get('parameters', {}), spec['operator']
            if operator in recorded and row.get('INSTANCE_KEY_RULE') is None:
                row['INSTANCE_KEY_RULE'], row['ITEM_PATH'] = recorded[operator]
            row.update(OPERATOR=operator, PARENT_INSTANCE_RULE=params.get('parent_instance_rule'),
                       UUID_POLICY=('instance' if params.get('uuid_from_instance') else
                                    'node' if params.get('include_uuid') else 'omit'),
                       EMPTY_POLICY='emit' if params.get('materialize_empty') else 'omit',
                       LIST_INSTANCE_RULE=params.get('list_identity', 'none'),
                       PROPERTY_NAME_RULE=params.get('property_name_rule'),
                       ASSEMBLY_POLICY='complete-only' if params.get('optional_assembly') else 'normal',
                       REQUIRED_MEMBERS='|'.join(params.get('required_members', ())) or None)
            group = next((group for group in contract.get('REFERENCE_GROUPS', ())
                          if group['assignments_path'] == path), None)
            if group:
                row.update(ROLES_PATH=group['roles_path'], PARTIES_PATH=group['parties_path'],
                           PARTY_TYPE=group['party_type'], PARTY_UUID_PARTS='|'.join(group['party_uuid_parts']),
                           PARTY_UUID_SOURCE_KEY='source-one')
        if path == contract['ROOT_PATH']:
            required = contract.get('REQUIRED_RULE_IDS', ()) or SUPPORT
            row.update(MAPPER_METADATA_VERSION=1,
                       DEFAULT_SINGLETON_POLICY='emit-outside-collections' if contract.get('DEFAULT_ELEMENT') else 'none',
                       REQUIRED_RULE_IDS='|'.join(required),
                       REPORT_TARGET_PATH=contract.get('REPORT', {}).get('TARGET_PATH'))
        rows.append(row)
    return rows


class RegistryReleaseTests(unittest.TestCase):
    def setUp(self):
        self.ns = metadata.namespace()

    def compile(self, rows=None, models=('SSP', 'ASSESSMENT_RESULTS'), registry=None, base_config=None):
        deployed = cell_namespace(models)
        profiles = copy.deepcopy(deployed['SOURCE_PROFILES'])
        if base_config:
            for profile in profiles:
                profile['BASE_CONFIG'].update(base_config)
        contexts = self.ns['compile_mapping_contexts'](
            {'source-one': mapping_rows() if rows is None else rows},
            release_registry() if registry is None else registry, profiles,
            deployed['MODEL_CONTRACTS'], deployed['ROUTING_METADATA'])
        return contexts

    def test_original_mapping_cells_and_provenance_are_unchanged(self):
        rows = mapping_rows()
        with (ROOT / 'tests/fixtures/mappings_pre_registry.csv').open(encoding='utf-8', newline='') as handle:
            frozen = list(csv.DictReader(handle))
        self.assertEqual(151, len(rows))
        self.assertEqual(frozen, [{key: row[key] for key in frozen[0]} for row in rows[:148]])
        self.assertEqual(Counter(APPROVED=63, BLOCKED_IF_POPULATED=1, DEFERRED=85, EXCLUDED=2),
                         Counter(row['EXECUTION_STATUS'] for row in rows))
        self.assertEqual(set(SUPPORT), {row['RULE_ID'] for row in rows[148:]})
        self.assertEqual(['FIELD', 'CONFIG', 'CONFIG'], [row['VALUE_SOURCE'] for row in rows[148:]])

    def test_actual_release_compiles_all_61_original_contracts_and_three_supports(self):
        contexts = self.compile()
        for context in contexts:
            self.assertEqual('READY', context['routing_report']['STATUS'], context['routing_report'])
            self.assertFalse(context['config']['EXECUTE_WRITES'])
            self.assertFalse(any('controlled_fields' in spec['parameters']
                                 for spec in context['compiled_plan']['elements'].values()))
        original = copy.deepcopy(contexts)
        for context in original:
            context['compiled_plan']['mappings'] = [row for row in context['compiled_plan']['mappings']
                                                   if row['RULE_ID'] not in SUPPORT]
        frozen = json.loads(previous.OLD_CATALOG_PATH.read_text(encoding='utf-8'))
        self.assertEqual(previous._frozen_semantics(frozen), previous._compiled_semantics(original))
        self.assertEqual({'SSP': 47, 'ASSESSMENT_RESULTS': 17},
                         {c['config']['OSCAL_MODEL']: len(c['mapping_rows']) for c in contexts})

    def ssp(self, mutate_record=None, registry_extra=None):
        old, records, original_registry, lookups = graph.ssp_fixture(graph.namespace(legacy=True))
        fields = {row['SOURCE_FIELD_NAME'] for row in old['mapping_rows']}
        selected = [row for row in mapping_rows() if row['EXECUTION_STATUS'] == 'APPROVED'
                    and (row['SOURCE_FIELD_NAME'] in fields or row['RULE_ID'] in SUPPORT)]
        registry = release_registry(list(original_registry.rows) + (registry_extra or []))
        context = self.compile(selected, ('SSP',), registry, old['config'])[0]
        self.assertEqual('READY', context['routing_report']['STATUS'], context['routing_report'])
        context['lookups'] = copy.deepcopy(old['lookups'])
        context['lookups']['component_sources'] = {'software': graph.Frame([]), 'interconnection': graph.Frame([])}
        self.ns['_build_component_hydration_lookups'] = lambda *args: lookups
        if mutate_record:
            mutate_record(records)
        metadata.poison_legacy_classifier(self.ns)
        return graph.build(self.ns, context, records, graph.Frame(registry)), context

    def test_exact_accepted_ssp_graph_through_released_csv_and_registry(self):
        (nodes, edges), _ = self.ssp()
        self.assertEqual((20, 19), (len(nodes.rows), len(edges.rows)))
        serialized = json.dumps([graph.business(nodes.rows), graph.business(edges.rows)], sort_keys=True)
        self.assertEqual(previous.SSP_GRAPH_DIGEST, hashlib.sha256(serialized.encode()).hexdigest())

    def test_unmapped_nested_singleton_remains_unemitted(self):
        nested = {'NODE_PATH': 'system-security-plan.system-implementation.components[].component',
                  'PARENT_NODE_PATH': 'system-security-plan.system-implementation.components[]',
                  'IS_COLLECTION': False, 'IS_ACTIVE': True, 'ELEMENT_TYPE': 'component', 'PROCESS_ORDER': 20}
        (nodes, edges), _ = self.ssp(registry_extra=[nested])
        self.assertEqual((20, 19), (len(nodes.rows), len(edges.rows)))
        self.assertEqual([], metadata.payloads(nodes, nested['NODE_PATH']))

    def test_required_support_row_removal_blocks_before_graph(self):
        for rule in SUPPORT:
            contexts = self.compile([row for row in mapping_rows() if row['RULE_ID'] != rule], ('SSP',))
            self.assertEqual('BLOCKED', contexts[0]['routing_report']['STATUS'])
            self.assertFalse(contexts[0]['mapping_rows'])

    def test_ar17_required_row_removal_still_blocks(self):
        context = self.compile([row for row in mapping_rows() if row['RULE_ID'] != 'ar17:PATCH_SCORE'],
                               ('ASSESSMENT_RESULTS',))[0]
        self.assertEqual('BLOCKED', context['routing_report']['STATUS'])

    def test_config_value_does_not_read_same_named_source_field(self):
        row = {'SOURCE_FIELD_NAME': 'PIN', 'TRANSFORM_ID': 'text',
               'REPRESENTATION_PARAMS': {'value_source': 'CONFIG', 'required': True}}
        context = {'config': {'PIN': 'approved'}, 'graph_report': {'FIELDS': {}}, 'policy': {}}
        self.assertEqual('approved', self.ns['_metadata_mapped_value'](row, {'PIN': 'wrong'}, context))
        context['config'] = {}
        with self.assertRaises(ValueError):
            self.ns['_metadata_mapped_value'](row, {'PIN': 'not a fallback'}, context)

    def test_no_deployed_cell_reads_a_catalog_file(self):
        for path in (ROOT / 'notebooks/cells').glob('*.py'):
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('MAPPER_CATALOG', text)
            self.assertNotIn('mapper_contract.v1.json', text)
            self.assertNotIn('_load_mapper_catalog', text)

    def test_missing_registry_extension_fails_before_any_graph_build(self):
        original = previous._registry_for_release(json.loads(previous.OLD_CATALOG_PATH.read_text(encoding='utf-8')))
        with self.assertRaisesRegex(ValueError, 'versioned registry root'):
            self.compile(registry=original)

    def test_exact_ar17_standalone_outputs_use_current_inputs(self):
        old_ns = graph.namespace(legacy=True)
        old = graph.ar_context(old_ns)
        fields = tuple(row['SOURCE_FIELD_NAME'] for row in old['mapping_rows'])
        records = [{'SOURCE_RECORD_ID': '100', 'CURATED_JSON': json.dumps({f: n + 1 for n, f in enumerate(fields)})},
                   {'SOURCE_RECORD_ID': '101', 'CURATED_JSON': '{"VULNERABILITY_SCORE":1.000000000000000001,"PATCH_SCORE":0,"RISK_SCORE_GRADE":"A"}'}]
        registry = release_registry()
        context = self.compile(models=('ASSESSMENT_RESULTS',), registry=registry, base_config=old['config'])[0]
        self.assertEqual('READY', context['routing_report']['STATUS'], context['routing_report'])
        context['lookups'] = copy.deepcopy(old['lookups'])
        oracle = runpy.run_path(str(graph.AR), run_name='registry_release_oracle')
        scope = oracle['build_ar_score_batch'].__globals__
        scope['AR_SCORE_FIELDS'], scope['AR_ALTERNATIVE_SCORE_FIELDS'] = scope['AR_ACCEPTED_SCORE_FIELDS'], ()
        helpers = {name: old_ns[name] for name in oracle['AR_HELPERS']}
        helpers['resolve_archer_select_value'] = lambda value: old_ns['resolve_archer_select_value'](value, old)
        ar_registry = [row for row in registry if row['OSCAL_MODEL_KEY'] == 'ASSESSMENT_RESULTS']
        expected = oracle['build_ar_score_batch'](records, old['mapping_rows'], ar_registry, old['config'], helpers)
        nodes, edges = graph.build(self.ns, context, records, graph.Frame(registry))
        self.assertEqual(graph.business(expected['nodes']), graph.business(nodes.rows))
        self.assertEqual(graph.business(expected['edges']), graph.business(edges.rows))
        self.assertEqual(expected['report']['FIELDS'], context['graph_report']['FIELDS'])


if __name__ == '__main__':
    unittest.main()
