"""Maintained CSV and registry contracts, compared with immutable accepted fixtures."""
import copy
import json
import unittest
from lean_support import ROOT, namespace
import test_registry_release as fixtures
import test_metadata_driven_contract as base
from test_flat_mapping_release import _frozen_semantics
from test_registry_first_routing import posted_rows


class LeanCompilerTests(unittest.TestCase):
    def setUp(self):
        self.ns = namespace(models=('SSP', 'ASSESSMENT_RESULTS'))
        self.args = ({'source-one': fixtures.mapping_rows()}, fixtures.release_registry(),
                     self.ns['SOURCE_PROFILES'], self.ns['MODEL_CONTRACTS'], self.ns['ROUTING_METADATA'])

    def compile(self, args=None):
        original = copy.deepcopy(args or self.args)
        result = self.ns['compile_mapping_contexts'](*(args or self.args))
        self.assertEqual(original, args or self.args)
        return result

    def test_actual_csv_accepted_semantics_match_frozen_contracts(self):
        frozen = json.loads((ROOT / 'tests/fixtures/mapper_contract_pre_flat.json').read_text(encoding='utf-8'))
        candidate = self.compile()
        compiled = sorted([
            [ctx['config']['OSCAL_MODEL'], row['SOURCE_FIELD_NAME'], row['OWNER_ELEMENT_PATH'],
             row['REPRESENTATION'], row['TRANSFORM_ID'], row['TRANSFORM_PARAMS'],
             row['REPRESENTATION_PARAMS'], row['APPROVAL_STATUS'], {}]
            for ctx in candidate for row in ctx['mapping_rows'] if row['RULE_ID'] not in fixtures.SUPPORT
        ], key=lambda row: tuple(row[:3]))
        self.assertEqual(_frozen_semantics(frozen), compiled)
        self.assertEqual({'SSP':47, 'ASSESSMENT_RESULTS':17},
                         {ctx['config']['OSCAL_MODEL']: len(ctx['mapping_rows']) for ctx in candidate})
        for context in candidate:
            report = context['routing_report']
            self.assertEqual('READY', report['STATUS'], report)
            self.assertEqual(151, sum(report[key] for key in ('SELECTED_ROWS', 'EXCLUDED_ROWS', 'DEFERRED_ROWS', 'BLOCKED_ROWS')))
            self.assertFalse(context['config']['EXECUTE_WRITES'])

    def test_unknown_model_display_label_still_uses_registry_ownership(self):
        self.args[0]['source-one'][1]['OSCAL_MODEL'] = 'New display label'
        self.assertEqual('READY', self.compile()[0]['routing_report']['STATUS'])

    def test_posted_459_unapproved_rows_remain_deferred_or_other_model(self):
        foreign = [
            {'OSCAL_MODEL_KEY': model, 'NODE_PATH': path, 'IS_ACTIVE': True}
            for model, path in (('PROFILE', 'profile.imports[]'),
                                ('SECURITY_ASSESSMENT_PLAN', 'security-assessment-plan.tasks[]'))
        ]
        args = ({'source-one': posted_rows()}, [*self.args[1], *foreign], *self.args[2:])
        for context in self.compile(args):
            report = context['routing_report']
            self.assertEqual(('READY', 459, 455, 4, 0, 0),
                             (report['STATUS'], report['INPUT_ROWS'], report['DEFERRED_ROWS'],
                              report['EXCLUDED_ROWS'], report['BLOCKED_ROWS'], report['SELECTED_ROWS']))

    def test_deferred_and_excluded_transform_metadata_cannot_execute(self):
        rows = [base.mapping(EXECUTION_STATUS=status, TRANSFORM_ID='do-not-execute')
                for status in ('DEFERRED', 'EXCLUDED')]
        args = ({'source-one':rows}, base.registry_rows(), [base.profile()], {base.MODEL:base.model_contract()})
        context = self.compile(args)[0]
        self.assertEqual([], context['mapping_rows'])
        self.assertEqual('READY', context['routing_report']['STATUS'])

    def test_populated_only_guard_is_retained_with_its_runtime_target(self):
        rows = self.compile()[0]['mapping_rows']
        guard = next(row for row in rows if row['SOURCE_FIELD_NAME'] == 'RECOMMENDED_SECURITY_CATEGORY')
        self.assertEqual('reject-populated', guard['TRANSFORM_ID'])
        self.assertEqual('BLOCKED_IF_POPULATED', guard['APPROVAL_STATUS'])
        self.assertEqual('', guard['OSCAL_ELEMENT_PATH'])
        self.assertTrue(guard['CANONICAL_ELEMENT_PATH'].startswith('system-security-plan.'))

    def test_conflicting_known_model_label_blocks(self):
        self.args[0]['source-one'][1]['OSCAL_MODEL'] = 'Assessment Results'
        self.assertEqual('BLOCKED', self.compile()[0]['routing_report']['STATUS'])

    def test_unknown_transform_blocks_before_execution(self):
        self.args[0]['source-one'][1]['TRANSFORM_ID'] = 'eval-python'
        self.assertEqual('BLOCKED', self.compile()[0]['routing_report']['STATUS'])

    def test_retired_json_rules_rejected(self):
        self.args[0]['source-one'][1]['VALUE_CONSTRAINTS'] = '{"required": true}'
        self.assertEqual('BLOCKED', self.compile()[0]['routing_report']['STATUS'])

    def test_config_required_support_rows_survive(self):
        contexts = self.compile()
        rows = {row['RULE_ID']: row for row in contexts[0]['mapping_rows']}
        self.assertEqual({'value_source':'CONFIG', 'required':True, 'target':'oscal-version'},
                         rows['support:oscal-version']['REPRESENTATION_PARAMS'])
        self.assertEqual('text', rows['support:metadata-title']['TRANSFORM_ID'])

    def test_duplicate_rule_rejected(self):
        self.args[0]['source-one'].append(copy.deepcopy(self.args[0]['source-one'][1]))
        self.assertEqual('BLOCKED', self.compile()[0]['routing_report']['STATUS'])

    def test_new_field_third_model_needs_only_metadata(self):
        args = ({'source-one':[base.mapping()]}, base.registry_rows(), [base.profile()],
                {base.MODEL:base.model_contract()})
        context = self.compile(args)[0]
        self.assertEqual('READY', context['routing_report']['STATUS'])
        self.assertEqual('NEVER_SEEN_SOURCE_FIELD', context['mapping_rows'][0]['SOURCE_FIELD_NAME'])

    def test_inactive_registry_boundary_cannot_be_attached_to_parent(self):
        row = base.registry_rows()[1]
        row['IS_ACTIVE'] = False
        registry = [row if r['NODE_PATH'] == row['NODE_PATH'] else r for r in base.registry_rows()]
        args = ({'source-one':[base.mapping()]}, registry, [base.profile()], {base.MODEL:base.model_contract()})
        context = self.compile(args)[0]
        self.assertEqual('BLOCKED', context['routing_report']['STATUS'])
        self.assertIn('REGISTRY_PATH_NOT_EXECUTABLE', context['routing_report']['REASON_COUNTS'])

    def test_conflicting_registry_roots_reject(self):
        registry = copy.deepcopy(self.args[1])
        registry[0]['OSCAL_MODEL_KEY'] = 'FOREIGN'
        with self.assertRaises(ValueError):
            self.compile((self.args[0], registry, *self.args[2:]))

    def test_collection_identity_must_match_operator(self):
        registry = base.registry_rows()
        registry[-1]['INSTANCE_KEY_RULE'] = 'VALUE'
        args = ({'source-one':[base.mapping()]}, registry, [base.profile()], {base.MODEL:base.model_contract()})
        with self.assertRaises(ValueError):
            self.compile(args)

    def test_missing_status_cannot_keep_runtime_metadata(self):
        self.args[0]['source-one'][1]['EXECUTION_STATUS'] = ''
        self.assertEqual('BLOCKED', self.compile()[0]['routing_report']['STATUS'])

    def test_observation_member_path_cannot_be_silently_ignored(self):
        args = ({'source-one':[base.mapping(path=base.OBSERVATION + '.title')]},
                base.registry_rows(), [base.profile()], {base.MODEL:base.model_contract()})
        self.assertEqual('BLOCKED', self.compile(args)[0]['routing_report']['STATUS'])

    def test_model_settings_cannot_inject_field_rules(self):
        args = ({'source-one':[base.mapping()]}, base.registry_rows(), [base.profile()],
                {base.MODEL:dict(base.model_contract(), MAPPING_RULES=[])})
        with self.assertRaises(ValueError):
            self.compile(args)

    def test_two_sources_cannot_collide_under_existing_party_identity(self):
        second = copy.deepcopy(self.args[2][0])
        second.update(SOURCE_KEY='source-two', SOURCE_TABLE_NAME='OTHER_TABLE', RAW_TABLE='TEST.OTHER_TABLE')
        rows = [dict(row, SOURCE_KEY='source-two') for row in self.args[0]['source-one']]
        args = (dict(self.args[0], **{'source-two':rows}), self.args[1], [*self.args[2],second], *self.args[3:])
        with self.assertRaisesRegex(ValueError, 'one source namespace'):
            self.compile(args)


if __name__ == '__main__':
    unittest.main()
