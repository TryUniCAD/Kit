import argparse
from base64 import b64decode,b64encode
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--python',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.root.resolve();tools=Path(__file__).resolve().parent;out=args.output;out.mkdir(exist_ok=False);records=[]
def digest(path):return sha256(path.read_bytes()).hexdigest()
def require(value,message):
 if not value:raise ValueError(message)
def verify():
 manifest=json.loads((root/'SourceManifest01.json').read_text())
 for key,label in (('baseline','BaseRoot'),('candidate','Code01')):
  found={str(p.relative_to(root/label)):digest(p) for p in sorted((root/label).rglob('*')) if p.is_file() and not any(y in str(p) for y in ('__pycache__','.mypy_cache','.ruff_cache'))};require(found==manifest[key],'source closure differs '+label)
 for name,wanted in manifest['tools'].items():require(digest(tools/name)==wanted,'tool closure differs '+name)
 require(digest(root/'Inputs01.json')==manifest['inputs_sha256'],'source metadata differs')
 inputs=json.loads((root/'Inputs01.json').read_text())
 for row in inputs['inputs']:
  require(digest(Path(row['path']))==row['sha256'],'disclosed source custody differs')
  for key in ('prior_member_build','prior_definition_build'):
   entry=row[key];require(digest(Path(entry['path']))==entry['sha256'],'previous generated regression evidence differs')
 return inputs
inputs=verify()
def execute(label,phase,value,base=False,expected=True,command=None):
 argv=command or [str(args.python),'-B',str(tools/'ManagerProcess01.py'),'--sdk',str(root/('BaseRoot' if base else 'Code01')),'--phase',phase];worker=subprocess.run(argv,input=json.dumps(value,allow_nan=False) if value is not None else None,text=True,capture_output=True,timeout=120);target=out/(label+'.json');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(worker.stdout);target.with_suffix('.stderr.txt').write_text(worker.stderr);require(bool(worker.stdout),'no worker record '+label);result=json.loads(worker.stdout);require((worker.returncode==0)==expected and result.get('passed',True)==expected,'unexpected worker decision '+label+' '+str(result)[:1200]);require(not result.get('denied_events'),'forbidden product runtime access '+label)
 if not expected:
  require(result['error_type'] in ('ValueError','TypeError','ArchiveError','BodyUnsupported'),'observer setup failure counted as SDK refusal '+label);require(any(row.get('sdk_module') for row in result.get('trace',[])),'negative did not reach the SDK '+label)
 records.append({'label':label,'exit':worker.returncode,'record_sha256':digest(target),'error_type':result.get('error_type'),'error':result.get('error')});return result
identity={'MatrixValues':[float(i%4==0) for i in range(9)],'ShiftValues':[0.,0.,0.],'ScaleValue':1.};sources={};builds={};positive=[]
for row in inputs['inputs']:
 name=row['name'];source_input={k:row[k] for k in ('name','path','sha256')};base=execute(name+'/BaselineSource','source_base',source_input,True);source=execute(name+'/Source','source',source_input)
 for key in ('owner_input','config_intent','members','source_pair_bits','document_sha256','full_refusal','source_manager_definition_round_trips','view_input'):require(base[key]==source[key],'source reader or full-source admission changed '+key)
 request={key:source[key] for key in ('owner_input','config_intent','members','view_input','manager_input')};first=execute(name+'/BuildA','build',request);second=execute(name+'/BuildB','build',request);require(first==second,'source view construction is not deterministic');require(first['pair_bits']==source['source_pair_bits'],'camera source representation changed');read=execute(name+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));require(first['definition']==read['definition'] and first['fragments']==read['fragments'] and first['pair_bits']==read['pair_bits'],'independent camera/owner readback differs')
 inventory_path=out/'OwnerCounts'/(name+'.json');inventory_path.parent.mkdir(parents=True,exist_ok=True);inventory_argv=[str(args.python),'-B',str(tools/'InventoryOwners01.py'),'--sdk',str(root/'Code01'),'--source',row['path'],'--sha256',row['sha256'],'--definition-build',str(out/name/'BuildA.json'),'--member-build',str(out/name/'BuildA.json'),'--output',str(inventory_path)];counts=execute(name+'/RemainingOwners','inventory',None,command=inventory_argv);require([x['changed_frontier_paths'] for x in counts['counts']]==[10,29],'remaining owner frontier counts differ')
 previous=json.loads(Path(row['prior_member_build']['path']).read_text());require(first['fragments']==previous['fragments'],'camera altered any previous member/model fragment');plain=deepcopy(request);plain['manager_input']={'BomOnWire':False,'AppearanceValue':{'ManagerOnWire':False,'NextAppearanceId':1}};old=execute(name+'/LegacyBaseline','legacy',plain,True);new=execute(name+'/IdentityCandidate','build',plain);require(old=={**new,'phase':'legacy'},'identity camera changes old constructor output');prior_def=json.loads(Path(row['prior_definition_build']['path']).read_text());require(new['definition']==prior_def['definition'],'previous source camera Definition changed');require(new['fragments']==previous['fragments'],'old default member fragments changed');sources[name]=request;builds[name]=first;positive.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':source['document_sha256'],'source_view_bit_identity':True,'seven_round_trips':True,'all_six_prior_member_fragments_exact':True,'old_source_camera_definition_exact':True,'complete_refusal_unchanged':True,'remaining_definition_frontiers':10,'remaining_manager_frontiers':29})
manager_cases=((True,False,1),(False,True,1),(True,True,0x8000000180000007),(False,True,0xffffffffffffffff),(True,True,0))
for index,(bom,present,counter) in enumerate(manager_cases,1):
 request=deepcopy(sources['D01']);request['manager_input']={'BomOnWire':bom,'AppearanceValue':{'ManagerOnWire':present,'NextAppearanceId':counter}};first=execute('Independent'+str(index)+'/BuildA','build',request);second=execute('Independent'+str(index)+'/BuildB','build',request);require(first==second,'independent empty manager construction is not deterministic');audit=execute('Independent'+str(index)+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));require(first['pair_bits']==audit['pair_bits'] and first['definition']==audit['definition'] and first['fragments']==audit['fragments'] and first['manager_bits']==audit['manager_bits'],'independent empty manager state changed through wire readback');actual=first['manager_bits'];require(actual['bom_present']==bom and bool(actual['appearance_present'])==present,'independent manager presence differs')
 if present:require(((actual['appearance_low']&0xffffffff)|((actual['appearance_high']&0xffffffff)<<32))==counter and actual['appearance_count']==actual['appearance_rows']==0,'unsigned appearance allocator or empty references differ')
 positive.append({'case':'independent_managers_'+str(index),'seven_round_trips':True,'bom_on_wire':bom,'appearance_on_wire':present,'explicit_uint64_counter':counter,'prior_six_fragment_identity':first['fragments']==builds['D01']['fragments'],'native_counter_domain_qualified':False})
row=inputs['inputs'][0];source_input={k:row[k] for k in ('name','path','sha256')};source_probes=('bom_wrong_class','bom_wrong_schema','bom_populated','bom_count_mismatch','bom_hidden_row','bom_boolean_count','bom_unknown_field','bom_missing_pointer','appearance_populated','appearance_hidden_row','appearance_count_mismatch','appearance_boolean_count','appearance_unknown_field','appearance_unknown_list','appearance_missing_body','appearance_missing_low','appearance_missing_high','appearance_low_outside','appearance_high_outside','appearance_boolean_word','appearance_bad_presence','appearance_boolean_presence','appearance_absent_with_body','wrong_schema','wrong_class','wrong_version')
for probe in source_probes:execute('SourceRejects/'+probe,'source',dict(source_input,probe=probe),expected=False)
input_probes=('bom_integer','appearance_integer','counter_boolean','counter_negative','counter_oversize','counter_float','absent_counter','wrong_type')
for probe in input_probes:
 request=deepcopy(sources['D01']);value=request['manager_input'];appearance=value['AppearanceValue']
 if probe=='bom_integer':value['BomOnWire']=1
 elif probe=='appearance_integer':appearance['ManagerOnWire']=1
 elif probe=='counter_boolean':appearance['NextAppearanceId']=True
 elif probe=='counter_negative':appearance['NextAppearanceId']=-1
 elif probe=='counter_oversize':appearance['NextAppearanceId']=1<<64
 elif probe=='counter_float':appearance['NextAppearanceId']=1.5
 elif probe=='absent_counter':appearance['ManagerOnWire']=False
 else:request['input_probe']='wrong_type'
 execute('InputRejects/'+probe,'build',request,expected=False)
for probe in ('truncated_definition','definition_trailer','resolved_map_base'):
 request=deepcopy(sources['D01']);request.update(payloads=deepcopy(builds['D01']['payloads']),definition_payload=builds['D01']['definition_payload'])
 if probe=='resolved_map_base':data=b64decode(request['payloads']['resolved']);request['payloads']['resolved']=b64encode((int.from_bytes(data[:4],'little')+1).to_bytes(4,'little')+data[4:]).decode()
 else:
  data=b64decode(request['definition_payload']);request['definition_payload']=b64encode(data[:-1] if probe=='truncated_definition' else data+b'\0').decode()
 execute('WireRejects/'+probe,'audit',request,expected=False)
for variant in (0,1):
 pair=[]
 for label in ('BaseRoot','Code01'):
  output=out/'FullCompatibility'/(label+str(variant)+'.json');command=[str(args.python),'-B',str(root/label/'re/tooling/sw2026/throughpresentation/Compat.py'),'--root',str(root/label),'--variant',str(variant),'--output',str(output)];pair.append(execute('FullCompatibility/'+label+str(variant),'compat',None,command=command))
 require(pair[0]==pair[1],'ordinary complete container or public reader changed')
verify();report={'schema':'kit.sw2026.throughall-empty-manager-process.v1','passed':True,'source_manifest_sha256':digest(root/'SourceManifest01.json'),'fresh_process_count':len(records),'negative_process_count':len(source_probes)+len(input_probes)+3,'positive_cases':positive,'independent_fragment_round_trips':56,'owner_inventory_stream_round_trips':12,'source_views_bit_identical':3,'source_empty_manager_states_retained':3,'independent_presence_counter_cases':len(manager_cases),'old_source_camera_definition_pairs':3,'old_member_fragment_pairs':3,'old_complete_container_pairs':2,'runtime_input_reads_during_construction':0,'heldout_inputs_read':0,'native_processes':0,'new_complete_native_outputs':0,'complete_source_preparation':False,'public_activation':False,'records':records};file=out/'Replay.json';file.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_process_count':report['negative_process_count'],'sha256':digest(file)}))
