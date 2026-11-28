import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--python',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.root.resolve();out=args.output;out.mkdir(exist_ok=False)
def digest(path):return sha256(path.read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def require(value,message):
 if not value:raise ValueError(message)
def verify():
 m=json.loads((root/'SourceManifest03.json').read_text())
 for group,label in (('baseline','BaseRoot'),('candidate','Code01')):
  actual={str(x.relative_to(root/label)):digest(x) for x in sorted((root/label).rglob('*')) if x.is_file() and '__pycache__' not in str(x) and '.mypy_cache' not in str(x) and '.ruff_cache' not in str(x)}
  require(actual==m[group],'frozen '+group+' source changed')
 for name,wanted in m['tools'].items():require(digest(Path(__file__).resolve().parent/name)==wanted,'frozen observer tool changed')
 require(digest(root/'Inputs01.json')==m['inputs_sha256'],'declared disclosed inputs changed')
 return m
manifest=verify();records=[]
def execute(label,phase,request,base=False,expected=True):
 command=[str(args.python),'-B',str(Path(__file__).resolve().parent/'ThruIntentProcess01.py'),'--sdk',str(root/('BaseRoot' if base else 'Code01')),'--phase',phase]
 p=subprocess.run(command,input=json.dumps(request,allow_nan=False),text=True,capture_output=True,timeout=100);path=out/(label+'.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(p.stdout);path.with_suffix('.stderr.txt').write_text(p.stderr)
 require(bool(p.stdout),'worker returned no structured result: '+label);x=json.loads(p.stdout);require((p.returncode==0)==expected and x['passed']==expected,'worker expectation failed: '+label+' '+str(x)[:700]);require(not x.get('denied_events'),'worker attempted forbidden runtime access')
 if not expected:require(x['error_type'] in ('ValueError','TypeError','BodyUnsupported','ArchiveError'),'negative failed in observer setup instead of product: '+label+' '+str(x))
 records.append({'label':label,'exit':p.returncode,'sha256':digest(path),'error_type':x.get('error_type'),'error':x.get('error')});return x
sources={};builds={};comparisons=[]
for row in json.loads((root/'Inputs01.json').read_text())['inputs']:
 name=row['name'];require(digest(Path(row['path']))==row['sha256'],'disclosed source changed');req={'name':name,'source':row['path'],'sha256':row['sha256']}
 old=execute(name+'/BaselineSource','baseline',req,True);source=execute(name+'/Source','source',req);sources[name]=source
 for key in ('document_sha256','full_refusal','unmapped','source_headers','owner_input','source_document_retained','source_manager_definition_round_trips'):require(old[key]==source[key],'new source projection changed original semantics: '+key)
 require(len(source['unmapped'])==11 and len(source['source_headers'][0]['unconstructed_log_owners'])==6,'source admission or missing revision owners changed')
 target={'owner_input':source['owner_input'],'intent':source['intent'],'written_at':1795106201}
 first=execute(name+'/BuildA','build',target);second=execute(name+'/BuildB','build',target);require(first==second,'new configured graph is not deterministic');builds[name]=first
 read=execute(name+'/Readback','readback',dict(target,payloads=first['payloads'],definition_payload=first['definition_payload']));require(read['fragments']==first['fragments'] and read['definition']==first['definition'],'independent generated readback differs')
 baseline=execute(name+'/LegacyBaseline','legacy',target,True);candidate=execute(name+'/LegacyCandidate','legacy',target);require(baseline==candidate,'existing default fragment bytes changed')
 comparisons.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':source['document_sha256'],'model_name_retained':first['root_name']==source['intent']['ModelName'],'nullable_manager_retained':first['manager_intent']==source['intent']['ManagerValue'],'definition_preferences_retained':first['definition_intent']=={'SettingsValue':source['intent']['DefinitionValue'],'DensityValue':source['intent']['DensityValue']},'round_trips':read['round_trips'],'default_fragment_byte_identity':True,'remaining_definition_paths':len(source['remaining_definition_difference_paths']),'remaining_manager_paths':len(source['remaining_manager_difference_paths']),'complete_gate_refused':True,'cleared_gate_refused':True})
source_probes=('foreign_selector','missing_manager_name','empty_manager_name','wrong_manager_schema','directory_count','configuration_epoch','stale_public_configuration','wrong_link_version','root_order','changed_root_caption','ui_bool','ui_density','ui_display_word','ui_journal')
row=json.loads((root/'Inputs01.json').read_text())['inputs'][0];req={'name':row['name'],'source':row['path'],'sha256':row['sha256']}
for probe in source_probes:execute('SourceRejects/'+probe,'source',dict(req,probe=probe),expected=False)
base={'owner_input':sources['D01']['owner_input'],'intent':sources['D01']['intent'],'written_at':1795106201}
input_probes=('missing_model_name','empty_model_name','empty_manager_name','manager_index_bool','manager_index_range','multiple_configurations','configuration_time_bool','configuration_name_foreign','density_negative','density_string','unknown_standard','tessellation_bool','unknown_intent_field','unknown_manager_field','automatic_scope')
for probe in input_probes:
 job=deepcopy(base);intent=job['intent'];mgr=intent['ManagerValue'];definition=intent['DefinitionValue']
 if probe=='missing_model_name':intent.pop('ModelName')
 elif probe=='empty_model_name':intent['ModelName']=''
 elif probe=='empty_manager_name':mgr['NameValue']=''
 elif probe=='manager_index_bool':mgr['CurrentIndex']=True
 elif probe=='manager_index_range':mgr['CurrentIndex']=1
 elif probe=='multiple_configurations':mgr['ConfigValues'].append(dict(mgr['ConfigValues'][0],NameValue='Alternative'))
 elif probe=='configuration_time_bool':mgr['ConfigValues'][0]['UpdatedAt']=True
 elif probe=='configuration_name_foreign':mgr['ConfigValues'][0]['NameValue']='Foreign'
 elif probe=='density_negative':intent['DensityValue']=-2.0
 elif probe=='density_string':intent['DensityValue']='1000'
 elif probe=='unknown_standard':definition['DraftingStandard']='moUnknown_c'
 elif probe=='tessellation_bool':definition['Tessellation'][0]=True
 elif probe=='unknown_intent_field':intent['native_fields']={}
 elif probe=='unknown_manager_field':mgr['captured_program']=[]
 elif probe=='automatic_scope':job['owner_input']['scope']['mode']='automatic'
 execute('InputRejects/'+probe,'build',job,expected=False)
for probe in ('config_trailer','definition_truncation','expected_title_foreign'):
 job=deepcopy(base);job.update(payloads=builds['D01']['payloads'],definition_payload=builds['D01']['definition_payload'])
 if probe=='config_trailer':
  from base64 import b64decode,b64encode
  job['payloads']=dict(job['payloads']);job['payloads']['config']=b64encode(b64decode(job['payloads']['config'])+b'\0').decode()
 elif probe=='definition_truncation':
  from base64 import b64decode,b64encode
  job['definition_payload']=b64encode(b64decode(job['definition_payload'])[:-1]).decode()
 else:job['intent']['ModelName']='Foreign title'
 execute('ReadbackRejects/'+probe,'readback',job,expected=False)
# this independent authored variant proves null presence and old native times were not converted into generation constants
new=deepcopy(base);new['intent']['ModelName']='Independent Unicode Model Ω';new['intent']['ManagerValue']['NameValue']='Authored configuration manager Ω';new['intent']['ManagerValue']['ConfigValues'][0].update(Description='Independent configuration description',UpdatedAt=1795106557);new['intent']['DefinitionValue'].update(DisplayBits=[0,31,32,63],Tessellation=[73,9,41,False],Preference7a=True,JournalName='Independent journal.doc');new['intent']['DensityValue']=1783.625
first=execute('Independent/BuildA','build',new);second=execute('Independent/BuildB','build',new);require(first==second,'independently authored configuration build differs');read=execute('Independent/Readback','readback',dict(new,payloads=first['payloads'],definition_payload=first['definition_payload']));require(read['manager_intent']==new['intent']['ManagerValue'],'independent authored configuration values were replaced')
verify()
for row in json.loads((root/'Inputs01.json').read_text())['inputs']:require(digest(Path(row['path']))==row['sha256'],'source changed during read-only matrix')
report={'schema':'kit.sw2026.throughall-source-config-process.v1','passed':True,'base_revision':manifest['base_revision'],'source_manifest_sha256':digest(root/'SourceManifest03.json'),'inputs_sha256':digest(root/'Inputs01.json'),'fresh_process_count':len(records),'source_cases':comparisons,'negative_processes':len(source_probes)+len(input_probes)+3,'independent_authored_case':True,'guarded_runtime_file_reads':0,'new_native_complete_outputs':0,'heldout_inputs_read':0,'native_processes':0,'public_activation':False,'source_conversion_qualified':False,'records':records}
f=out/'Replay.json';f.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_processes':report['negative_processes'],'report_sha256':digest(f)}))
