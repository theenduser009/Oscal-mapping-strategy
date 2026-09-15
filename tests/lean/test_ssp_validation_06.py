import ast, contextlib, copy, io, json, runpy, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
VALIDATOR=ROOT/'notebooks/validation/06_ssp_system_characteristics_core_validation.py'
API=runpy.run_path(str(VALIDATOR), run_name='validation_06_test_import')

class Row(dict):
    def as_dict(self, recursive=False): return dict(self)
class Frame:
    def __init__(self, rows, columns): self.data=[Row(r) for r in rows]; self.columns=list(columns)
    def to_local_iterator(self): return iter(self.data)
    def select(self,*columns):
        if not set(columns).issubset(self.columns): raise AssertionError('unknown selected column')
        return Frame([{k:r[k] for k in columns} for r in self.data], columns)
    def count(self): return len(self.data)
class StructField:
    def __init__(self,name,dtype): self.name=name
class Session:
    def create_dataframe(self, values, schema):
        names=[f.name for f in schema]; return Frame([dict(zip(names,row)) for row in values], names)
    def sql(self,*a,**k): raise AssertionError('No SQL/database action allowed')
    def table(self,*a,**k): raise AssertionError('No database action allowed')

def load_cells():
    ns={'session':Session(),'StringType':lambda:None,'TimestampType':lambda _:None,
        'TimestampTimeZone':type('TZ',(),{'TZ':'TZ'}),'StructField':StructField,'StructType':list}
    with contextlib.redirect_stdout(io.StringIO()):
        for file in sorted((ROOT/'notebooks/cells').glob('[0-9][0-9]_*.py')):
            tree=ast.parse(file.read_text()); number=int(file.name[:2]); keep=[]
            for node in tree.body:
                if isinstance(node,ast.ImportFrom) and (node.module or '').startswith('snowflake'): continue
                targets={t.id for t in getattr(node,'targets',()) if isinstance(t,ast.Name)}
                if number==1 and 'session' in targets: continue
                if number==2 and not isinstance(node,ast.FunctionDef): continue
                if number==3 and ('MAPPING_CONTEXTS' in targets or isinstance(node,ast.Expr)): continue
                if number==7 and (targets & {'MODEL_GRAPHS','PIPELINE_REPORT'} or isinstance(node,ast.Try)): continue
                keep.append(node)
            exec(compile(ast.Module(body=keep,type_ignores=[]),str(file),'exec'),ns)
    return ns

def make_preview():
    ns=load_cells(); ns['MODEL_CONTRACTS']['SSP']['STORAGE_CONTRACT']=None
    profile=copy.deepcopy(ns['SOURCE_PROFILES'][0]); profile['MAPPING_FILE']=str(ROOT/'Mapping/ARCHER_OSCAL_MAPPINGS.csv')
    wanted={'AUTHORIZATION_PACKAGE_NAME','ACRONYM','MISSION_PURPOSE','SAP_ID'}
    mapping=[r for r in ns['load_mapping_rows'](profile) if r['SOURCE_FIELD_NAME'] in wanted]
    base='system-security-plan'
    rows=[
        {'OSCAL_MODEL_KEY':'SSP','NODE_PATH':base,'ELEMENT_TYPE':'system-security-plan','PARENT_NODE_PATH':None,'IS_COLLECTION':False,'INSTANCE_KEY_RULE':'SINGLETON','ITEM_PATH':None,'PROCESS_ORDER':1,'IS_ACTIVE':True,'OPERATOR':'object','UUID_POLICY':'node','REQUIRED_MEMBERS':None},
        {'OSCAL_MODEL_KEY':'SSP','NODE_PATH':base+'.system-characteristics','ELEMENT_TYPE':'system-characteristics','PARENT_NODE_PATH':base,'IS_COLLECTION':False,'INSTANCE_KEY_RULE':'SINGLETON','ITEM_PATH':None,'PROCESS_ORDER':2,'IS_ACTIVE':True,'OPERATOR':'object','UUID_POLICY':'omit','REQUIRED_MEMBERS':None},
        {'OSCAL_MODEL_KEY':'SSP','NODE_PATH':base+'.system-characteristics.system-ids[]','ELEMENT_TYPE':'system-ids','PARENT_NODE_PATH':base+'.system-characteristics','IS_COLLECTION':True,'INSTANCE_KEY_RULE':'VALUE','ITEM_PATH':'$','PROCESS_ORDER':3,'IS_ACTIVE':True,'OPERATOR':'values','UUID_POLICY':'omit','REQUIRED_MEMBERS':None},
    ]
    contexts=ns['compile_mapping_contexts']({'source-one':mapping},rows,[profile],ns['MODEL_CONTRACTS'],ns['ROUTING_METADATA'])
    assert contexts[0]['routing_report']['STATUS']=='READY'
    source_rows=[]
    for i in (1,2):
        payload={'AUTHORIZATION_PACKAGE_NAME':f'Synthetic SSP {i}','ACRONYM':f'SSP{i}','MISSION_PURPOSE':f'Mission {i}','SAP_ID':f'SAP-{i}'}
        source_rows.append({'SOURCE_RECORD_ID':f'SYNTHETIC-{i}','CURATED_JSON':json.dumps(payload)})
    sources={'source-one':{'source_df':Frame(source_rows,('SOURCE_RECORD_ID','CURATED_JSON')),'selection':{'SELECTED_ROWS':2},'lookups':{}}}
    graphs,report=ns['run_oscal_pipeline'](sources,contexts,'PREVIEW')
    ns.update(SOURCE_INPUTS=sources,MAPPING_CONTEXTS=contexts,MODEL_GRAPHS=graphs,PIPELINE_REPORT=report,REGISTRY_INPUT_ROWS=rows)
    return ns

class Tests(unittest.TestCase):
    def setUp(self): self.ns=make_preview(); self.graph=self.ns['MODEL_GRAPHS'][('source-one','SSP')]
    def validate(self): return API['run_ssp_validation_06'](self.ns)
    def node(self,path,record='SYNTHETIC-1'):
        return next(r for r in self.graph['nodes'].data if r['ELEMENT_PATH']==path and r['SOURCE_RECORD_ID']==record)
    def change_payload(self,path,fn,record='SYNTHETIC-1'):
        n=self.node(path,record); p=json.loads(n['METADATA_JSON']); fn(p); n['METADATA_JSON']=json.dumps(p)
    def assert_failure(self,name):
        r=self.validate(); self.assertEqual('FAIL',r['STATUS']); self.assertGreater(r['FAILURE_COUNTS'].get(name,0),0)
    def test_pass(self):
        r=self.validate(); self.assertEqual('PASS',r['STATUS']); self.assertEqual(2,r['SYSTEM_CHARACTERISTICS_NODES']); self.assertEqual(2,r['SYSTEM_ID_NODES']); self.assertEqual(2,r['SYSTEM_IDS_CHECKED'])
    def test_wrong_system_name(self):
        self.change_payload('system-security-plan.system-characteristics',lambda p:p.update({'system-name':'wrong'})); self.assert_failure('SOURCE_MISMATCH_SYSTEM_NAME')
    def test_wrong_short(self):
        self.change_payload('system-security-plan.system-characteristics',lambda p:p.update({'system-name-short':'wrong'})); self.assert_failure('SOURCE_MISMATCH_SYSTEM_NAME_SHORT')
    def test_wrong_description(self):
        self.change_payload('system-security-plan.system-characteristics',lambda p:p.update({'description':'wrong'})); self.assert_failure('SOURCE_MISMATCH_DESCRIPTION')
    def test_wrong_system_id(self):
        self.change_payload('system-security-plan.system-characteristics.system-ids[]',lambda p:p.update({'id':'wrong'})); self.assert_failure('SOURCE_MISMATCH_SYSTEM_IDS')
    def test_missing_system_char(self):
        n=self.node('system-security-plan.system-characteristics'); self.graph['nodes'].data.remove(n); self.assert_failure('SYSTEM_CHARACTERISTICS_NOT_EXACTLY_ONCE_PER_SOURCE')
    def test_extra_system_id(self):
        n=copy.deepcopy(self.node('system-security-plan.system-characteristics.system-ids[]')); n['NODE_KEY']='f'*32; n['OSCAL_UUID']='00000000-0000-4000-8000-000000000123'; n['INSTANCE_KEY']='extra'; n['METADATA_JSON']=json.dumps({'id':'EXTRA'}); self.graph['nodes'].data.append(n); self.assert_failure('SOURCE_MISMATCH_SYSTEM_IDS')
    def test_no_mutation(self):
        before=copy.deepcopy((self.graph,self.ns['SOURCE_INPUTS'])); self.validate(); self.assertEqual(before[0]['nodes'].data,self.graph['nodes'].data); self.assertEqual(before[1]['source-one']['source_df'].data,self.ns['SOURCE_INPUTS']['source-one']['source_df'].data)
    def test_report_private_values_omitted(self):
        text=json.dumps(self.validate()); self.assertNotIn('SYNTHETIC-1',text); self.assertNotIn('Synthetic SSP 1',text); self.assertNotIn('SAP-1',text)
    def test_bad_schema_blocked(self):
        self.graph['nodes'].columns.remove('NODE_KEY'); self.graph['nodes'].columns.append('PK_ELEMENT_HASH')
        with self.assertRaisesRegex(ValueError,'schema'): self.validate()
    def test_stale_run_blocked(self):
        self.ns['CONFIG']['RUN_ID']='new-run'
        with self.assertRaisesRegex(ValueError,'Stale'): self.validate()
    def test_cell_entrypoint(self):
        clean={k:self.ns[k] for k in ('SELECTED_MODELS','CONFIG','OSCAL_LOAD_MODE','PIPELINE_REPORT','MODEL_GRAPHS','MAPPING_CONTEXTS','SOURCE_INPUTS')}; clean['__name__']='__main__'
        with contextlib.redirect_stdout(io.StringIO()): exec(compile(VALIDATOR.read_text(),str(VALIDATOR),'exec'),clean)
        self.assertEqual('PASS',clean['SSP_VALIDATION_06_REPORT']['STATUS'])

if __name__=='__main__': unittest.main()
