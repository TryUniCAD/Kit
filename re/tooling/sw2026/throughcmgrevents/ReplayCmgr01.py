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
 require(digest(root/'Inputs01.json')==manifest['inputs_sha256'] and digest(root/'NativeRules01.json')==manifest['native_rules_sha256'],'input or native rule metadata differs')
 inputs=json.loads((root/'Inputs01.json').read_text())
 for row in inputs['inputs']:
  require(digest(Path(row['path']))==row['sha256'],'disclosed source custody differs');prior=row['prior_ui_build'];require(digest(Path(prior['path']))==prior['sha256'],'prior generated UI output differs')
 return inputs
inputs=verify()
def execute(label,phase,value,base=False,expected=True,command=None,legacy=False):
 argv=command or [str(args.python),'-B',str(tools/('LegacyUiProcess01.py' if base or legacy else 'CmgrEventProcess01.py')),'--sdk',str(root/('BaseRoot' if base else 'Code01')),'--phase',phase];worker=subprocess.run(argv,input=json.dumps(value,allow_nan=False) if value is not None else None,text=True,capture_output=True,timeout=120);path=out/(label+'.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(worker.stdout);path.with_suffix('.stderr.txt').write_text(worker.stderr);require(bool(worker.stdout),'worker returned no record '+label);result=json.loads(worker.stdout);require((worker.returncode==0)==expected and result.get('passed',True)==expected,'unexpected worker decision '+label+' '+str(result)[:1500]);require(not result.get('denied_events'),'forbidden runtime access '+label)
 if not expected:
  require(result['error_type'] in ('ValueError','TypeError','ArchiveError','BodyUnsupported'),'observer failure counted as SDK refusal '+label);require(any(row.get('sdk_module') for row in result.get('trace',[])),'negative did not reach SDK '+label)
 records.append({'label':label,'exit':worker.returncode,'record_sha256':digest(path),'error_type':result.get('error_type'),'error':result.get('error')});return result
def equivalent(first,second):
 require(all(first[key]==second[key] for key in ('definition','fragments','pair_bits','manager_bits','line_bits','ui_bits','env_count','event_bits')),'independent event stream semantics differ');require(first['grammar']['factory_owner_checked'] is True and second['grammar']['factory_owner_checked'] is False and first['grammar']==dict(second['grammar'],factory_owner_checked=True),'factory and wire graph proof contexts differ')
def predict(event):
 ticks=(event['MomentValue']['SecondsValue']+11644473600)*10000000+event['MomentValue']['FractionTicks'];low=ticks&0xffffffff;high=ticks>>32;creator=event['CreatedBy'];return {'f29c':101,'f2a0':low-(1<<32) if low&(1<<31) else low,'f2a4':high-(1<<32) if high&(1<<31) else high,'f2b0':creator['FileVersion'],'f2b4':creator['DateCode'],'f2ac':creator['ParasolidVersion'],'f300':creator['ServicePack'],'f301':creator['SubservicePack'],'f2b8':0,'f2bc':0}
def predicted(bits,event):
 require(bits['manager_words']==predict(event['ManagerValue']) and bits['active_words']==predict(event['ActiveValue']),'independent event words differ');require(bits['distinct_owners'] and bits['directory_alias'] and bits['manager_native_id']==-1 and bits['active_native_id']==0,'actual manager/config identity differs')
sources={};builds={};positive=[]
for row in inputs['inputs']:
 name=row['name'];source_input={k:row[k] for k in ('name','path','sha256')};base=execute(name+'/BaselineSource','source',source_input,True);source=execute(name+'/Source','source',source_input)
 for key in base:require(source[key]==base[key],'old source projection or refusal changed '+key)
 request={key:source[key] for key in ('owner_input','config_intent','members','view_input','manager_input','line_input','ui_input','events')};first=execute(name+'/BuildA','build',request);second=execute(name+'/BuildB','build',request);require(first==second,'manager event construction is not deterministic');predicted(first['event_bits'],request['events']);require(first['event_bits']==source['source_event_bits'],'source exact owner event fields differ');audit=execute(name+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));equivalent(first,audit)
 inventory_path=out/'OwnerCounts'/(name+'.json');inventory_path.parent.mkdir(parents=True,exist_ok=True);argv=[str(args.python),'-B',str(tools/'InventoryOwners01.py'),'--sdk',str(root/'Code01'),'--source',row['path'],'--sha256',row['sha256'],'--definition-build',str(out/name/'BuildA.json'),'--member-build',str(out/name/'BuildA.json'),'--output',str(inventory_path)];counts=execute(name+'/RemainingOwners','inventory',None,command=argv);require([x['changed_frontier_paths'] for x in counts['counts']]==[2,23],'remaining source frontiers differ')
 prior=json.loads(Path(row['prior_ui_build']['path']).read_text());require(first['definition']==prior['definition'] and all(first[key]==prior[key] for key in ('pair_bits','manager_bits','line_bits','ui_bits','env_count','grammar')),'manager event changed prior document or owner semantics');changed=[key for key in prior['fragments'] if prior['fragments'][key]!=first['fragments'][key]];require(changed==['manager'],'manager feature event changed another native stream');old_request={key:value for key,value in request.items() if key!='events'};before=execute(name+'/OldCallerBaseline','build',old_request,True);after=execute(name+'/OldCallerCandidate','build',old_request,legacy=True);require(before==after==prior,'old constructor behavior or byte identities changed');sources[name]=request;builds[name]=first;positive.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':source['document_sha256'],'two_actual_events_exact':True,'high_and_low_words_and_creation_provenance_exact':True,'only_manager_fragment_changed':True,'old_definition_and_six_fragments_exact':True,'old_source_projection_and_full_refusal_exact':True,'seven_fragment_round_trips':True,'remaining_definition_frontiers':2,'remaining_manager_frontiers':23})
variants=[(0,0,0xffffffff,9999999,0,2),(1750000001,1,1750000003,2,2,0),(1795100000,9999999,1795100001,0,0,0),(1795100991,7654321,1795100123,1234567,2,2),(42,7,1000000,7777777,2,0),(0xffffffff,9999999,0,0,0,2)]
for index,(ms,mf,cs,cf,mp,cp) in enumerate(variants,1):
 request=deepcopy(sources['D01']);event=request['events'];event['ManagerValue']['MomentValue']={'SecondsValue':ms,'FractionTicks':mf};event['ActiveValue']['MomentValue']={'SecondsValue':cs,'FractionTicks':cf};event['ManagerValue']['CreatedBy']['SubservicePack']=mp;event['ActiveValue']['CreatedBy']['SubservicePack']=cp;first=execute('Independent'+str(index)+'/BuildA','build',request);second=execute('Independent'+str(index)+'/BuildB','build',request);require(first==second,'independent events are not deterministic');predicted(first['event_bits'],event);read=execute('Independent'+str(index)+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));equivalent(first,read);require(first['definition']==builds['D01']['definition'] and all(first['fragments'][key]==builds['D01']['fragments'][key] for key in first['fragments'] if key!='manager'),'independent manager event changed another native stream');positive.append({'case':'independent_'+str(index),'semantic_events':event,'two_independent_events_exact':True,'seven_fragment_round_trips':True,'only_manager_fragment_changed':True})
source_probes=[scope+':'+key+':'+value for scope in ('manager','active') for key,value in (('f29c','102'),('f2b8','19000'),('f2bc','1'),('f2a0','true'),('f2a0','2147483648'),('f2a4','-1'),('f2b0','18000'),('f2b4','-1'),('f2ac','0'),('f300','4'),('f301','1'),('f2a4','missing'),('f2b4','missing'))]+['manager_class','manager_schema','active_class','active_schema','selector_copy','row_copy','directory_count','allocation_count','extra_configuration','configuration_name','manager:f08:0','active:f08:1'];source_input={k:inputs['inputs'][0][k] for k in ('name','path','sha256')}
for index,probe in enumerate(source_probes,1):execute('SourceRejects/'+str(index),'source',dict(source_input,probe=probe),expected=False)
input_probes=('seconds_boolean','seconds_negative','seconds_overflow','fraction_boolean','fraction_negative','fraction_overflow','main_version','service','subservice','date_negative','kernel_zero','date_mismatch','kernel_mismatch')
for probe in input_probes:
 request=deepcopy(sources['D01']);target=request['events']['ManagerValue'];moment=target['MomentValue'];creator=target['CreatedBy']
 if probe=='seconds_boolean':moment['SecondsValue']=True
 elif probe=='seconds_negative':moment['SecondsValue']=-1
 elif probe=='seconds_overflow':moment['SecondsValue']=1<<32
 elif probe=='fraction_boolean':moment['FractionTicks']=False
 elif probe=='fraction_negative':moment['FractionTicks']=-1
 elif probe=='fraction_overflow':moment['FractionTicks']=10000000
 elif probe=='main_version':creator['FileVersion']=18000
 elif probe=='service':creator['ServicePack']=4
 elif probe=='subservice':creator['SubservicePack']=1
 elif probe=='date_negative':creator['DateCode']=-1
 elif probe=='kernel_zero':creator['ParasolidVersion']=0
 elif probe=='date_mismatch':creator['DateCode']+=1
 elif probe=='kernel_mismatch':creator['ParasolidVersion']+=1
 execute('InputRejects/'+probe,'build',request,expected=False)
fresh_probes=('wrong_type','manager_owner','active_owner','foreign_selected','manager_stamped','active_stamped','manager_update','active_update','target_provenance','selector_copy')
for probe in fresh_probes:execute('FreshRejects/'+probe,'build',dict(deepcopy(sources['D01']),input_probe=probe),expected=False)
for probe in ('truncated_manager','manager_trailer','resolved_map_base'):
 request=deepcopy(sources['D01']);request.update(payloads=deepcopy(builds['D01']['payloads']),definition_payload=builds['D01']['definition_payload']);key='resolved' if probe=='resolved_map_base' else 'manager';data=b64decode(request['payloads'][key]);data=(int.from_bytes(data[:4],'little')+1).to_bytes(4,'little')+data[4:] if probe=='resolved_map_base' else data[:-1] if probe=='truncated_manager' else data+b'\0';request['payloads'][key]=b64encode(data).decode();execute('WireRejects/'+probe,'audit',request,expected=False)
for variant in (0,1):
 pair=[]
 for label in ('BaseRoot','Code01'):
  path=out/'FullCompatibility'/(label+str(variant)+'.json');argv=[str(args.python),'-B',str(root/label/'re/tooling/sw2026/throughpresentation/Compat.py'),'--root',str(root/label),'--variant',str(variant),'--output',str(path)];pair.append(execute('FullCompatibility/'+label+str(variant),'compat',None,command=argv))
 require(pair[0]==pair[1],'old complete container or public read changed')
verify();report={'schema':'kit.sw2026.throughall-cmgr-feature-event-process.v1','passed':True,'source_manifest_sha256':digest(root/'SourceManifest01.json'),'fresh_process_count':len(records),'negative_process_count':len(source_probes)+len(input_probes)+len(fresh_probes)+3,'positive_cases':positive,'disclosed_source_cases':2,'independent_event_pairs':len(variants),'independent_fragment_round_trips':7*(2+len(variants)),'owner_inventory_stream_round_trips':8,'old_definition_and_owner_pairs':2,'old_complete_container_pairs':2,'runtime_input_reads_during_construction':0,'heldout_inputs_read':0,'native_processes':0,'new_complete_native_outputs':0,'source_environment_construction':False,'complete_source_preparation':False,'public_activation':False,'records':records};path=out/'Replay.json';path.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_process_count':report['negative_process_count'],'sha256':digest(path)}))
