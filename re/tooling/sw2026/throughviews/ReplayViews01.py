import argparse
from base64 import b64decode,b64encode
from copy import deepcopy
from hashlib import sha256
import json
from math import cos,sin
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
 argv=command or [str(args.python),'-B',str(tools/'ViewProcess01.py'),'--sdk',str(root/('BaseRoot' if base else 'Code01')),'--phase',phase];worker=subprocess.run(argv,input=json.dumps(value,allow_nan=False) if value is not None else None,text=True,capture_output=True,timeout=120);target=out/(label+'.json');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(worker.stdout);target.with_suffix('.stderr.txt').write_text(worker.stderr);require(bool(worker.stdout),'no worker record '+label);result=json.loads(worker.stdout);require((worker.returncode==0)==expected and result.get('passed',True)==expected,'unexpected worker decision '+label+' '+str(result)[:1200]);require(not result.get('denied_events'),'forbidden product runtime access '+label)
 if not expected:
  require(result['error_type'] in ('ValueError','TypeError','ArchiveError','BodyUnsupported'),'observer setup failure counted as SDK refusal '+label);require(any(row.get('sdk_module') for row in result.get('trace',[])),'negative did not reach the SDK '+label)
 records.append({'label':label,'exit':worker.returncode,'record_sha256':digest(target),'error_type':result.get('error_type'),'error':result.get('error')});return result
identity={'MatrixValues':[float(i%4==0) for i in range(9)],'ShiftValues':[0.,0.,0.],'ScaleValue':1.};sources={};builds={};positive=[]
for row in inputs['inputs']:
 name=row['name'];source_input={k:row[k] for k in ('name','path','sha256')};base=execute(name+'/BaselineSource','source_base',source_input,True);source=execute(name+'/Source','source',source_input)
 for key in ('owner_input','config_intent','members','source_pair_bits','document_sha256','full_refusal','source_manager_definition_round_trips'):require(base[key]==source[key],'source reader or full-source admission changed '+key)
 request={key:source[key] for key in ('owner_input','config_intent','members','view_input')};first=execute(name+'/BuildA','build',request);second=execute(name+'/BuildB','build',request);require(first==second,'source view construction is not deterministic');require(first['pair_bits']==source['source_pair_bits'],'camera source representation changed');read=execute(name+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));require(first['definition']==read['definition'] and first['fragments']==read['fragments'] and first['pair_bits']==read['pair_bits'],'independent camera/owner readback differs')
 inventory_path=out/'OwnerCounts'/(name+'.json');inventory_path.parent.mkdir(parents=True,exist_ok=True);inventory_argv=[str(args.python),'-B',str(tools/'InventoryOwners01.py'),'--sdk',str(root/'Code01'),'--source',row['path'],'--sha256',row['sha256'],'--definition-build',str(out/name/'BuildA.json'),'--member-build',str(out/name/'BuildA.json'),'--output',str(inventory_path)];counts=execute(name+'/RemainingOwners','inventory',None,command=inventory_argv);require([x['changed_frontier_paths'] for x in counts['counts']]==[13,29],'remaining owner frontier counts differ')
 previous=json.loads(Path(row['prior_member_build']['path']).read_text());require(first['fragments']==previous['fragments'],'camera altered any previous member/model fragment');plain=deepcopy(request);plain['view_input']=identity;old=execute(name+'/LegacyBaseline','legacy',plain,True);new=execute(name+'/IdentityCandidate','build',plain);require(old=={**new,'phase':'legacy'},'identity camera changes old constructor output');prior_def=json.loads(Path(row['prior_definition_build']['path']).read_text());require(new['definition']==prior_def['definition'],'old default Definition changed');require(new['fragments']==previous['fragments'],'old default member fragments changed');sources[name]=request;builds[name]=first;positive.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':source['document_sha256'],'source_view_bit_identity':True,'seven_round_trips':True,'all_six_prior_member_fragments_exact':True,'old_default_definition_exact':True,'complete_refusal_unchanged':True,'remaining_definition_frontiers':13,'remaining_manager_frontiers':29})
for index,(angle,shift,scale) in enumerate(((.431,(.0713,-.0937,.0131),.375),(-.823,(-.0217,.0839,-.0073),2.343)),1):
 request=deepcopy(sources['D01']);a=cos(angle);b=sin(angle);request['view_input']={'MatrixValues':[a,b,0.,-b,a,0.,0.,0.,1.] if index==1 else [1.,0.,0.,0.,a,b,0.,-b,a],'ShiftValues':list(shift),'ScaleValue':scale};first=execute('Independent'+str(index)+'/BuildA','build',request);second=execute('Independent'+str(index)+'/BuildB','build',request);require(first==second,'independent authored view is not deterministic');audit=execute('Independent'+str(index)+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));require(first['pair_bits']==audit['pair_bits'] and first['definition']==audit['definition'] and first['fragments']==audit['fragments'],'independent varied view changed through wire readback');positive.append({'case':'independent_camera_'+str(index),'seven_round_trips':True,'distinct_analytic_rotation':True,'nonzero_three_axis_translation':True,'explicit_positive_scale':scale,'prior_six_fragment_identity':first['fragments']==builds['D01']['fragments']})
row=inputs['inputs'][0];source_input={k:row[k] for k in ('name','path','sha256')};source_probes=('wrong_schema','wrong_class','wrong_version','perspective','pan_matrix','absent_orientation','unknown_orientation','absent_model_scale','identity_matrix','model_translation','model_scale','model_negative_zero','boolean_flag','corrupt_pan','reflection','nonfinite_pan')
for probe in source_probes:execute('SourceRejects/'+probe,'source',dict(source_input,probe=probe),expected=False)
input_probes=('negative_scale','zero_scale','boolean_scale','text_scale','boolean_translation','short_matrix','reflection','nonorthogonal','short_translation','wrong_type','nonfinite_translation','nonfinite_scale')
for probe in input_probes:
 request=deepcopy(sources['D01']);view=request['view_input']
 if probe=='negative_scale':view['ScaleValue']=-.3
 elif probe=='zero_scale':view['ScaleValue']=0.
 elif probe=='boolean_scale':view['ScaleValue']=True
 elif probe=='text_scale':view['ScaleValue']='2.3'
 elif probe=='boolean_translation':view['ShiftValues'][1]=False
 elif probe=='short_matrix':view['MatrixValues']=view['MatrixValues'][:-1]
 elif probe=='reflection':view['MatrixValues'][0]=-1.
 elif probe=='nonorthogonal':view['MatrixValues'][1]=.3
 elif probe=='short_translation':view['ShiftValues']=view['ShiftValues'][:-1]
 else:request['input_probe']=probe
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
verify();report={'schema':'kit.sw2026.throughall-source-view-process.v1','passed':True,'source_manifest_sha256':digest(root/'SourceManifest01.json'),'fresh_process_count':len(records),'negative_process_count':len(source_probes)+len(input_probes)+3,'positive_cases':positive,'independent_fragment_round_trips':35,'owner_inventory_stream_round_trips':12,'source_views_bit_identical':3,'old_default_definition_pairs':3,'old_member_fragment_pairs':3,'old_complete_container_pairs':2,'runtime_input_reads_during_construction':0,'heldout_inputs_read':0,'native_processes':0,'new_complete_native_outputs':0,'complete_source_preparation':False,'public_activation':False,'records':records};file=out/'Replay.json';file.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_process_count':report['negative_process_count'],'sha256':digest(file)}))
