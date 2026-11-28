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
  actual={str(p.relative_to(root/label)):digest(p) for p in sorted((root/label).rglob('*')) if p.is_file() and not any(x in p.parts for x in ('__pycache__','.mypy_cache','.ruff_cache'))};require(actual==manifest[key],'source closure differs '+label)
 for name,wanted in manifest['tools'].items():require(digest(tools/name)==wanted,'worker tool differs '+name)
 require(digest(root/'Inputs01.json')==manifest['inputs_sha256'] and digest(root/'NativeRules01.json')==manifest['native_rules_sha256'],'source metadata or native rules differ')
 inputs=json.loads((root/'Inputs01.json').read_text())
 for row in inputs['inputs']:
  require(digest(Path(row['path']))==row['sha256'],'disclosed input custody differs');prior=row['prior_line_build'];require(digest(Path(prior['path']))==prior['sha256'],'prior generated regression differs')
 return inputs
inputs=verify()
def execute(label,phase,value,base=False,expected=True,command=None,legacy=False):
 argv=command or [str(args.python),'-B',str(tools/('LegacyLineProcess01.py' if base or legacy else 'UiProcess01.py')),'--sdk',str(root/('BaseRoot' if base else 'Code01')),'--phase',phase];worker=subprocess.run(argv,input=json.dumps(value,allow_nan=False) if value is not None else None,text=True,capture_output=True,timeout=120);path=out/(label+'.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(worker.stdout);path.with_suffix('.stderr.txt').write_text(worker.stderr);require(bool(worker.stdout),'worker returned no record '+label);result=json.loads(worker.stdout);require((worker.returncode==0)==expected and result.get('passed',True)==expected,'unexpected worker decision '+label+' '+str(result)[:1500]);require(not result.get('denied_events'),'forbidden runtime access '+label)
 if not expected:
  require(result['error_type'] in ('ValueError','TypeError','ArchiveError','BodyUnsupported'),'observer failure counted as SDK refusal '+label);require(any(row.get('sdk_module') for row in result.get('trace',[])),'negative did not reach SDK '+label)
 records.append({'label':label,'exit':worker.returncode,'record_sha256':digest(path),'error_type':result.get('error_type'),'error':result.get('error')});return result
def equivalent(first,second):
 require(all(first[key]==second[key] for key in ('definition','fragments','pair_bits','manager_bits','line_bits','ui_bits','env_count')),'independent ui stream semantics differ');require(first['grammar']['factory_owner_checked'] is True and second['grammar']['factory_owner_checked'] is False and first['grammar']==dict(second['grammar'],factory_owner_checked=True),'factory and wire graph proof contexts differ')
def predict(value):return {'fad0':value['HlrQualityCode'],'fad4':2+int(value['DisplayGrid']),'fb00':1,'fb04':38284 if value['DefaultCommandGroup']=='features' else 0}
sources={};builds={};positive=[]
for row in inputs['inputs']:
 name=row['name'];source_input={k:row[k] for k in ('name','path','sha256')};base=execute(name+'/BaselineSource','source',source_input,True);source=execute(name+'/Source','source',source_input)
 for key in ('owner_input','config_intent','members','view_input','manager_input','line_input','source_line_bits','source_pair_bits','document_sha256','full_refusal','source_manager_definition_round_trips'):require(source[key]==base[key],'prior source projection or full refusal changed '+key)
 request={key:source[key] for key in ('owner_input','config_intent','members','view_input','manager_input','line_input','ui_input')};first=execute(name+'/BuildA','build',request);second=execute(name+'/BuildB','build',request);require(first==second,'ui source construction is not deterministic');require(first['ui_bits']==source['source_ui_bits']==predict(request['ui_input']),'source native ui operands differ');require(source['source_env_count']==1 and first['env_count']==0,'source window frontier was copied or misclassified');audit=execute(name+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));equivalent(first,audit)
 inventory_path=out/'OwnerCounts'/(name+'.json');inventory_path.parent.mkdir(parents=True,exist_ok=True);argv=[str(args.python),'-B',str(tools/'InventoryOwners01.py'),'--sdk',str(root/'Code01'),'--source',row['path'],'--sha256',row['sha256'],'--definition-build',str(out/name/'BuildA.json'),'--member-build',str(out/name/'BuildA.json'),'--output',str(inventory_path)];counts=execute(name+'/RemainingOwners','inventory',None,command=argv);require([x['changed_frontier_paths'] for x in counts['counts']]==[2,29],'remaining original source frontiers differ')
 prior=json.loads(Path(row['prior_line_build']['path']).read_text());require(all(first[key]==prior[key] for key in ('fragments','pair_bits','manager_bits','line_bits')),'ui settings changed previous fragments or line/camera/managers');old_request={key:value for key,value in request.items() if key!='ui_input'};before=execute(name+'/OldCallerBaseline','build',old_request,True);after=execute(name+'/OldCallerCandidate','build',old_request,legacy=True);require(before==after and before['definition']==prior['definition'],'old constructor bytes or API behavior changed');sources[name]=request;builds[name]=first;positive.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':source['document_sha256'],'four_ui_fields_exact':True,'source_environment_count':source['source_env_count'],'fresh_environment_count':first['env_count'],'source_window_state_still_refused':True,'old_definition_and_six_fragments_exact':True,'old_source_projection_and_full_refusal_exact':True,'seven_fragment_round_trips':True,'remaining_definition_frontiers':2,'remaining_manager_frontiers':29})
variants=[{'HlrQualityCode':quality,'DisplayGrid':grid,'DefaultCommandGroup':group} for quality in (0,1) for grid in (False,True) for group in ('none','features')]
for index,ui in enumerate(variants,1):
 request=deepcopy(sources['D01']);request['ui_input']=ui;first=execute('Independent'+str(index)+'/BuildA','build',request);second=execute('Independent'+str(index)+'/BuildB','build',request);require(first==second,'independent ui construction is not deterministic');read=execute('Independent'+str(index)+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));equivalent(first,read);require(first['ui_bits']==predict(ui) and first['env_count']==0,'independent native ui operands differ');require(all(first[key]==builds['D01'][key] for key in ('fragments','pair_bits','manager_bits','line_bits')),'independent ui values changed another owner');positive.append({'case':'independent_'+str(index),'semantic_input':ui,'four_native_operands_exact':True,'seven_fragment_round_trips':True,'previous_fragments_and_presentations_exact':True,'window_state_not_generated':True})
source_probes=('quality_reserved','quality_unqualified','quality_boolean','quality_missing','grid_unsupported_bits','grid_missing_seed','grid_boolean','grid_missing','context_unconfirmed','context_assembly','context_drawing','context_boolean','context_missing','group_drawing','group_unqualified','group_boolean','group_missing','display_mode','display_boolean','count_mismatch','count_boolean','count_negative','count_overflow','count_missing','environment_rows_missing','environment_unknown_row','environment_alias','environment_null','environment_wrong_class','environment_wrong_schema','wrong_schema','wrong_class','wrong_version');source_input={k:inputs['inputs'][0][k] for k in ('name','path','sha256')}
for probe in source_probes:execute('SourceRejects/'+probe,'source',dict(source_input,probe=probe),expected=False)
input_probes=('quality_boolean','quality_negative','quality_unqualified','quality_reserved','quality_float','grid_integer','grid_text','group_unknown','group_drawing','group_empty','group_integer','wrong_type')
for probe in input_probes:
 request=deepcopy(sources['D01']);ui=request['ui_input']
 if probe=='quality_boolean':ui['HlrQualityCode']=True
 elif probe=='quality_negative':ui['HlrQualityCode']=-1
 elif probe=='quality_unqualified':ui['HlrQualityCode']=2
 elif probe=='quality_reserved':ui['HlrQualityCode']=65535
 elif probe=='quality_float':ui['HlrQualityCode']=1.0
 elif probe=='grid_integer':ui['DisplayGrid']=0
 elif probe=='grid_text':ui['DisplayGrid']='false'
 elif probe=='group_unknown':ui['DefaultCommandGroup']='unqualified'
 elif probe=='group_drawing':ui['DefaultCommandGroup']='drawings'
 elif probe=='group_empty':ui['DefaultCommandGroup']=''
 elif probe=='group_integer':ui['DefaultCommandGroup']=38284
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
  path=out/'FullCompatibility'/(label+str(variant)+'.json');argv=[str(args.python),'-B',str(root/label/'re/tooling/sw2026/throughpresentation/Compat.py'),'--root',str(root/label),'--variant',str(variant),'--output',str(path)];pair.append(execute('FullCompatibility/'+label+str(variant),'compat',None,command=argv))
 require(pair[0]==pair[1],'old complete container or public read changed')
verify();report={'schema':'kit.sw2026.throughall-part-ui-process.v1','passed':True,'source_manifest_sha256':digest(root/'SourceManifest01.json'),'fresh_process_count':len(records),'negative_process_count':len(source_probes)+len(input_probes)+3,'positive_cases':positive,'source_scalar_cases':2,'independent_scalar_cases':len(variants),'independent_fragment_round_trips':7*(2+len(variants)),'owner_inventory_stream_round_trips':8,'old_definition_and_owner_pairs':2,'old_complete_container_pairs':2,'runtime_input_reads_during_construction':0,'heldout_inputs_read':0,'native_processes':0,'new_complete_native_outputs':0,'source_environment_construction':False,'complete_source_preparation':False,'public_activation':False,'records':records};path=out/'Replay.json';path.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_process_count':report['negative_process_count'],'sha256':digest(path)}))
