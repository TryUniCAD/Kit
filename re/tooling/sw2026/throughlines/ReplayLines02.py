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
 manifest=json.loads((root/'SourceManifest02.json').read_text())
 for key,label in (('baseline','BaseRoot'),('candidate','Code01')):
  found={str(p.relative_to(root/label)):digest(p) for p in sorted((root/label).rglob('*')) if p.is_file() and not any(y in p.parts for y in ('__pycache__','.mypy_cache','.ruff_cache'))};require(found==manifest[key],'source closure differs '+label)
 for name,wanted in manifest['tools'].items():require(digest(tools/name)==wanted,'tool closure differs '+name)
 require(digest(root/'Inputs01.json')==manifest['inputs_sha256'],'disclosed metadata differs')
 require(digest(root/manifest['native_rules_path'])==manifest['native_rules_sha256'],'native static rules differ')
 inputs=json.loads((root/'Inputs01.json').read_text())
 for row in inputs['inputs']:
  require(digest(Path(row['path']))==row['sha256'],'disclosed source custody differs')
  for key in ('prior_manager_build',):
   entry=row[key];require(digest(Path(entry['path']))==entry['sha256'],'prior generated regression differs')
 return inputs
inputs=verify()
def execute(label,phase,value,base=False,expected=True,command=None):
 argv=command or [str(args.python),'-B',str(tools/('LegacyManagerProcess01.py' if base else 'LineProcess01.py')),'--sdk',str(root/('BaseRoot' if base else 'Code01')),'--phase',phase];worker=subprocess.run(argv,input=json.dumps(value,allow_nan=False) if value is not None else None,text=True,capture_output=True,timeout=120);target=out/(label+'.json');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(worker.stdout);target.with_suffix('.stderr.txt').write_text(worker.stderr);require(bool(worker.stdout),'no worker record '+label);result=json.loads(worker.stdout);require((worker.returncode==0)==expected and result.get('passed',True)==expected,'unexpected worker decision '+label+' '+str(result)[:1600]);require(not result.get('denied_events'),'forbidden SDK runtime access '+label)
 if not expected:
  require(result['error_type'] in ('ValueError','TypeError','ArchiveError','BodyUnsupported','UnicodeEncodeError'),'observer failure counted as SDK rejection '+label);require(any(row.get('sdk_module') for row in result.get('trace',[])),'negative did not reach SDK '+label)
 records.append({'label':label,'exit':worker.returncode,'record_sha256':digest(target),'error_type':result.get('error_type'),'error':result.get('error')});return result
def predicted_bindings(value):
 entries=[]
 for index,row in enumerate(value):
  raw=row['CategoryValue'].encode('utf-16-le');units=[raw[i]|raw[i+1]<<8 for i in range(0,len(raw),2)];h=2166136261
  for unit in units[::len(units)//10+1]:h=((h*16777619)&4294967295)^unit
  entries.append((h%17,-index,row))
 return [row for bucket,index,row in sorted(entries,key=lambda item:(item[0],item[1]))]
sources={};builds={};positive=[]
for row in inputs['inputs']:
 name=row['name'];source_input={k:row[k] for k in ('name','path','sha256')};old=execute(name+'/BaselineSource','source',source_input,True);source=execute(name+'/Source','source',source_input)
 for key in ('owner_input','config_intent','members','source_pair_bits','document_sha256','full_refusal','source_manager_definition_round_trips','view_input','manager_input'):require(source[key]==old[key],'prior source semantics or whole-source refusal changed '+key)
 request={key:source[key] for key in ('owner_input','config_intent','members','view_input','manager_input','line_input')};first=execute(name+'/BuildA','build',request);second=execute(name+'/BuildB','build',request);require(first==second,'source line construction is not deterministic');require(first['line_bits']==source['source_line_bits'],'source line node ownership or values changed');require(first['line_bits']['bindings']==predicted_bindings(request['line_input']['BindingValues']),'source native map order disagrees with independent predictor');read=execute(name+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));require(all(first[key]==read[key] for key in ('definition','fragments','pair_bits','manager_bits','line_bits')),'independent seven-fragment readback differs');require(first['grammar']['factory_owner_checked'] is True and read['grammar']['factory_owner_checked'] is False and first['grammar']==dict(read['grammar'],factory_owner_checked=True),'factory and serialized graph proof contexts differ')
 inventory_path=out/'OwnerCounts'/(name+'.json');inventory_path.parent.mkdir(parents=True,exist_ok=True);argv=[str(args.python),'-B',str(tools/'InventoryOwners01.py'),'--sdk',str(root/'Code01'),'--source',row['path'],'--sha256',row['sha256'],'--definition-build',str(out/name/'BuildA.json'),'--member-build',str(out/name/'BuildA.json'),'--output',str(inventory_path)];counts=execute(name+'/RemainingOwners','inventory',None,command=argv);require([x['changed_frontier_paths'] for x in counts['counts']]==[6,29],'remaining original owner frontier changed')
 previous=json.loads(Path(row['prior_manager_build']['path']).read_text());require(first['fragments']==previous['fragments'] and first['pair_bits']==previous['pair_bits'] and first['manager_bits']==previous['manager_bits'],'line component changed prior six fragments camera or empty managers');plain=deepcopy(request);plain['line_input']={'PatternValues':[],'BindingValues':[]};base_input={k:v for k,v in plain.items() if k!='line_input'};base=execute(name+'/DefaultBaseline','build',base_input,True);fresh=execute(name+'/DefaultCandidate','build',plain);require(base=={k:v for k,v in fresh.items() if k!='line_bits'},'empty line semantic inputs change old full Definition or owner bytes');require(base['definition']==previous['definition'],'old source empty-manager Definition changed');sources[name]=request;builds[name]=first;positive.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':source['document_sha256'],'source_patterns':first['line_bits']['style_count'],'source_font_bindings':first['line_bits']['font_count'],'source_field_bit_identity':True,'constructor_and_readback_object_identity_exact':True,'seven_fragment_round_trips':True,'six_prior_fragments_exact':True,'camera_empty_manager_state_exact':True,'old_definition_exact':True,'full_source_refusal_unchanged':True,'remaining_definition_frontiers':6,'remaining_manager_frontiers':29})
variants=[]
for index in range(6):
 keys=['Case','case','café_'+str(index),'layer_長さ_'+str(index),'astral_\U0001f984_'+str(index),'long_category_'+str(index)+'_abcdefghijklmnopqrstuv']
 if index==1:keys.reverse()
 if index==2:keys=keys[2:]+keys[:2]
 if index==3:keys=[]
 if index==4:keys=['unlisted_font_selector']
 if index==5:
  trial=[{'CategoryValue':'collision_'+str(i)} for i in range(200)];buckets={}
  for row in trial:
   key=row['CategoryValue'];raw=key.encode('utf-16-le');h=2166136261;units=[raw[i]|raw[i+1]<<8 for i in range(0,len(raw),2)]
   for unit in units[::len(units)//10+1]:h=((h*16777619)&4294967295)^unit
   buckets.setdefault(h%17,[]).append(key)
  keys=next(values[:5] for values in buckets.values() if len(values)>=5)
 patterns=[] if index==3 else [{'NameValue':'authored_pattern_'+str(index),'CaptionValue':'analytic style '+str(index),'SegmentsValue':[.00125*(index+1),-.000375,0.0,.0000625],'ThickThinValue':index%2==1},{'NameValue':'secondary_'+str(index),'CaptionValue':'\u9577\u3055 secondary '+str(index),'SegmentsValue':[.000875,-.000125],'ThickThinValue':False}]
 bindings=[{'CategoryValue':key,'FontName':'independently_unlisted_selector' if index in (1,4) else patterns[0]['NameValue'],'WeightValue':i%3,'EndCapValue':2 if i%2 else 0} for i,key in enumerate(keys)];variants.append({'PatternValues':patterns,'BindingValues':bindings})
for index,line_input in enumerate(variants,1):
 request=deepcopy(sources['D01']);request['line_input']=line_input;first=execute('Independent'+str(index)+'/BuildA','build',request);second=execute('Independent'+str(index)+'/BuildB','build',request);require(first==second,'independent authored line graph is not deterministic');read=execute('Independent'+str(index)+'/Readback','audit',dict(request,payloads=first['payloads'],definition_payload=first['definition_payload']));require(all(first[key]==read[key] for key in ('definition','fragments','pair_bits','manager_bits','line_bits')),'independent semantic wire changed');require(first['grammar']['factory_owner_checked'] is True and read['grammar']['factory_owner_checked'] is False and first['grammar']==dict(read['grammar'],factory_owner_checked=True),'independent factory and wire proof contexts differ');bits=first['line_bits'];require(bits['patterns']==line_input['PatternValues'] and bits['bindings']==predicted_bindings(line_input['BindingValues']),'independent authored semantic predictor differs');require(bits['style_count']==bits['style_nodes']==len(line_input['PatternValues']) and bits['font_count']==bits['font_nodes']==len(line_input['BindingValues']),'fresh row counts or distinct object identities differ');require(first['fragments']==builds['D01']['fragments'],'independent line values altered six prior fragments');positive.append({'case':'independent_'+str(index),'pattern_count':bits['style_count'],'category_count':bits['font_count'],'seven_fragment_round_trips':True,'map_order_predicted':True,'new_objects_distinct':True,'prior_six_fragments_exact':True})
source_probes=('font_wrong_class','font_wrong_schema','font_unknown_field','font_count_mismatch','font_boolean_count','font_missing','font_unknown_row','font_config_wrong_class','font_config_wrong_schema','font_config_unknown_field','font_config_alias','font_duplicate_category','font_star_category','font_nul_category','font_custom_width','font_width_unknown_field','font_weight','font_weight_boolean','font_end_cap','font_end_cap_boolean','font_reordered','style_unknown_field','style_count_mismatch','style_boolean_count','style_missing','style_unknown_row','style_config_alias','style_wrong_class','style_wrong_schema','style_unknown_node_field','style_duplicate_name','style_segment_count','style_segment_boolean','style_segment_unknown','style_zero_period','style_nonfinite','style_thick_thin','style_thick_boolean','wrong_schema','wrong_class','wrong_version')
source_input={k:inputs['inputs'][0][k] for k in ('name','path','sha256')}
for probe in source_probes:execute('SourceRejects/'+probe,'source',dict(source_input,probe=probe),expected=False)
input_probes=('category_empty','category_star','category_nul','category_surrogate','category_duplicate','font_name_empty','font_name_nul','weight_boolean','weight_unqualified','endcap_boolean','endcap_unqualified','pattern_name_empty','pattern_caption_empty','pattern_duplicate','pattern_empty_segments','pattern_zero_period','pattern_boolean_segment','pattern_thick_integer','wrong_type')
for probe in input_probes:
 request=deepcopy(sources['D01']);value=request['line_input'];binding=value['BindingValues'][0];pattern=value['PatternValues'][0]
 if probe=='category_empty':binding['CategoryValue']=''
 elif probe=='category_star':binding['CategoryValue']='persistent*temporary'
 elif probe=='category_nul':binding['CategoryValue']='persistent\0hidden'
 elif probe=='category_surrogate':binding['CategoryValue']='unpaired_\ud800'
 elif probe=='category_duplicate':value['BindingValues'][1]['CategoryValue']=binding['CategoryValue']
 elif probe=='font_name_empty':binding['FontName']=''
 elif probe=='font_name_nul':binding['FontName']='font\0hidden'
 elif probe=='weight_boolean':binding['WeightValue']=True
 elif probe=='weight_unqualified':binding['WeightValue']=10
 elif probe=='endcap_boolean':binding['EndCapValue']=False
 elif probe=='endcap_unqualified':binding['EndCapValue']=1
 elif probe=='pattern_name_empty':pattern['NameValue']=''
 elif probe=='pattern_caption_empty':pattern['CaptionValue']=''
 elif probe=='pattern_duplicate':value['PatternValues'][1]['NameValue']=pattern['NameValue'].lower()
 elif probe=='pattern_empty_segments':pattern['SegmentsValue']=[]
 elif probe=='pattern_zero_period':pattern['SegmentsValue']=[0.0,0.0]
 elif probe=='pattern_boolean_segment':pattern['SegmentsValue']=[True,.001]
 elif probe=='pattern_thick_integer':pattern['ThickThinValue']=1
 elif probe=='pattern_extra':pattern['FutureMode']=0
 elif probe=='binding_extra':binding['FutureMode']=0
 elif probe=='input_extra':value['FutureMode']=0
 elif probe=='wrong_type':request['input_probe']='wrong_type'
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
  output=out/'FullCompatibility'/(label+str(variant)+'.json');argv=[str(args.python),'-B',str(root/label/'re/tooling/sw2026/throughpresentation/Compat.py'),'--root',str(root/label),'--variant',str(variant),'--output',str(output)];pair.append(execute('FullCompatibility/'+label+str(variant),'compat',None,command=argv))
 require(pair[0]==pair[1],'existing complete container or public reader changed')
verify();report={'schema':'kit.sw2026.throughall-line-presentation-process.v1','passed':True,'source_manifest_sha256':digest(root/'SourceManifest02.json'),'fresh_process_count':len(records),'negative_process_count':len(source_probes)+len(input_probes)+3,'positive_cases':positive,'independent_seven_fragment_round_trips':7*(len(inputs['inputs'])+len(variants)),'owner_inventory_stream_round_trips':4*len(inputs['inputs']),'source_line_tables_retained':len(inputs['inputs']),'independent_authored_variants':len(variants),'old_empty_manager_definition_pairs':len(inputs['inputs']),'old_member_fragment_pairs':len(inputs['inputs']),'old_complete_container_pairs':2,'runtime_input_reads_during_construction':0,'heldout_inputs_read':0,'native_processes':0,'new_complete_native_outputs':0,'complete_source_preparation':False,'public_activation':False,'records':records};target=out/'Replay.json';target.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_process_count':report['negative_process_count'],'sha256':digest(target)}))
