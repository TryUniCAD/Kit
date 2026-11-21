import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--python',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.root.resolve();tool=Path(__file__).resolve().parent;out=args.output;out.mkdir(exist_ok=False);records=[]
def digest(path):return sha256(path.read_bytes()).hexdigest()
def require(value,message):
 if not value:raise ValueError(message)
def verify():
 manifest=json.loads((root/'SourceManifest01.json').read_text())
 for key,label in (('baseline','BaseRoot'),('candidate','Code01')):
  observed={str(x.relative_to(root/label)):digest(x) for x in sorted((root/label).rglob('*')) if x.is_file() and not any(y in str(x) for y in ('__pycache__','.mypy_cache','.ruff_cache'))};require(observed==manifest[key],'source closure changed: '+label)
 for name,wanted in manifest['tools'].items():require(digest(tool/name)==wanted,'tool closure changed: '+name)
 require(digest(root/'Inputs01.json')==manifest['inputs_sha256'],'disclosed input metadata changed')
 return manifest
manifest=verify()
def execute(label,phase,request,base=False,expected=True,custom=None):
 sdk=root/('BaseRoot' if base else 'Code01');command=custom or [str(args.python),'-B',str(tool/'MemberProcess01.py'),'--sdk',str(sdk),'--phase',phase]
 process=subprocess.run(command,input=json.dumps(request,allow_nan=False) if request is not None else None,text=True,capture_output=True,timeout=120);file=out/(label+'.json');file.parent.mkdir(parents=True,exist_ok=True);file.write_text(process.stdout);file.with_suffix('.stderr.txt').write_text(process.stderr);require(bool(process.stdout),'worker produced no structured record '+label);value=json.loads(process.stdout);require((process.returncode==0)==expected and value.get('passed',True)==expected,'unexpected worker result '+label+' '+str(value)[:1500]);require(not value.get('denied_events'),'forbidden runtime access '+label)
 if not expected:
  require(value['error_type'] in ('ValueError','TypeError','BodyUnsupported','ArchiveError'),'observer setup error counted as product refusal '+label)
  require(any(x['file']!='MemberProcess01.py' for x in value.get('trace',[])),'refusal did not reach SDK '+label)
 records.append({'label':label,'exit':process.returncode,'record_sha256':digest(file),'error_type':value.get('error_type'),'error':value.get('error')});return value
source={};builds={};positives=[]
for row in json.loads((root/'Inputs01.json').read_text())['inputs']:
 require(digest(Path(row['path']))==row['sha256'],'source hash differs');name=row['name'];source[name]=execute(name+'/Source','source',row);request=source[name];first=execute(name+'/BuildA','build',request);second=execute(name+'/BuildB','build',request);require(first==second,'member construction is not deterministic');audit=execute(name+'/Readback','audit',dict(request,payloads=first['payloads']));require(first['fragments']==audit['fragments'],'independent member fragment bytes differ');require(first['allocator_after']-first['allocator_before']==6 and first['members']['member_count']==6 and first['resolved_root_count']==21,'source member ownership or allocation differs');require([x['logs'] for x in first['revision_headers']]==[28,28],'source logs do not bind all actual target owners');require(request['source_ambient_kept_in_scene'] is False and request['external_id_duplicates_allowed'],'semantic source light policy or nonunique external ID observation differs');builds[name]=first
 old=execute(name+'/LegacyBaseline','legacy',request,True);new=execute(name+'/LegacyCandidate','legacy',request);require(old==new,'unchanged source-owner component bytes changed');positives.append({'case':name,'source_sha256':row['sha256'],'source_document_sha256':request['document_sha256'],'source_member_count':6,'allocation':{'before':first['allocator_before'],'after':first['allocator_after']},'previous_ids_unchanged':first['previous_ids_unchanged'],'owner_flags_unchanged':first['owner_flags_unchanged'],'note_ids':first['members']['notes'],'light_ids':first['members']['lights'],'revision_header_logs':[28,28],'wire_round_trips':6,'legacy_fragments_exact':True,'full_source_refusal_retained':bool(request['full_refusal'])})
base=deepcopy(source['D01'])
for count in (2,5):
 request=deepcopy(base);member=request['members'];entry=member['InputValue']['LightValues'][0];lights=[]
 for i in range(count):
  light=deepcopy(entry);light.update(KindValue='ambient' if i==0 else 'directional',NameValue='Independent light '+str(i),ExternalName='shared external identifier',AmbientValue=.375 if i==0 else 0.,DiffuseValue=.263+i*.031,SpecularValue=.527,ColourValue=0x172B8A,KeepInScene=True,EnabledInPv=True,UseCartesian=False,PvBrightness=.825,PvShadows=False,PvQuality=12.5,DirectionValue=None if i==0 else [2.3,-.7,.2+i*.113],ShadowSoftness=None if i==0 else .043,CreatedValue={'SecondsValue':1795108000+i,'FractionTicks':173+i});lights.append(light)
 member['InputValue']['LightValues']=lights;member['InputValue']['NotesValue']={'HeadName':'Independent notes','EndName':'Independent notes1___EndTag___','HeadCreated':{'SecondsValue':1795108101,'FractionTicks':57},'EndCreated':{'SecondsValue':1795108101,'FractionTicks':113}};member['NoteIds']=['neutral:notes/head','neutral:notes/end'];member['LightIds']=['neutral:light/'+str(i) for i in range(count)];request['config_intent']['ModelName']='IndependentScene'+str(count)
 books=[]
 for _ in range(2):
  ids=['$model',*[x['source_id'] for x in request['root_roles']],*member['NoteIds'],*member['LightIds']];books.append({'clocks':{'CreatedAt':1795107901,'ArchiveAt':1795108201,'UpdatedAt':1795108201},'users':['Independent author'],'companies':['Independent company'],'logs':[{'source_id':idvalue,'caption':'Authored revision '+str(i),'events':[{'OperationValue':'created','UserName':'Independent author','CompanyName':'Independent company','EventAt':1795107901+i,'CommentText':'Independently authored event'}]} for i,idvalue in enumerate(ids)]})
 request['books']=books;first=execute('Independent'+str(count)+'/BuildA','build',request);second=execute('Independent'+str(count)+'/BuildB','build',request);require(first==second,'independent scene is not deterministic');audit=execute('Independent'+str(count)+'/Readback','audit',dict(request,payloads=first['payloads']));require(first['fragments']==audit['fragments'],'independent scene wire differs');require(first['allocator_after']-first['allocator_before']==count+2 and first['members']['member_count']==count+2,'member allocation used a fixed six child recipe');require(first['members']['directions'][1]==lights[1]['DirectionValue'],'direction setter path normalized an authored vector');positives.append({'case':'independent_scene_'+str(count),'member_count':count+2,'revision_header_logs':[24+count]*2,'wire_round_trips':6,'explicit_nonunit_vector_retained':True,'external_ids_intentionally_shared':True})
source_probes=('notes_reverse','notes_foreign_partner','notes_wrong_marker','notes_contents','foreign_environment','light_unknown_kind','light_boolean','light_state','light_view_space','light_duplicate_word','light_user_property','light_zero_direction','light_stale_identity','light_order','note_unset_time')
row=json.loads((root/'Inputs01.json').read_text())['inputs'][0]
for probe in source_probes:execute('SourceRejects/'+probe,'source',dict(row,probe=probe),expected=False)
input_probes=('unknown_kind','negative_coefficient','boolean_colour','integer_keep','negative_brightness','negative_quality','missing_direction','ambient_direction','negative_softness','wrong_endtag','duplicate_caption','bad_fraction','empty_scene')
for probe in input_probes:
 request=deepcopy(base);scene=request['members']['InputValue'];lights=scene['LightValues']
 if probe=='unknown_kind':lights[1]['KindValue']='point'
 elif probe=='negative_coefficient':lights[0]['AmbientValue']=-.1
 elif probe=='boolean_colour':lights[0]['ColourValue']=True
 elif probe=='integer_keep':lights[0]['KeepInScene']=1
 elif probe=='negative_brightness':lights[0]['PvBrightness']=-1.0
 elif probe=='negative_quality':lights[0]['PvQuality']=-1.0
 elif probe=='missing_direction':lights[1]['DirectionValue']=None
 elif probe=='ambient_direction':lights[0]['DirectionValue']=[1.,0.,0.]
 elif probe=='negative_softness':lights[1]['ShadowSoftness']=-1.0
 elif probe=='wrong_endtag':scene['NotesValue']['EndName']='unrepresented partner caption'
 elif probe=='duplicate_caption':lights[1]['NameValue']=lights[0]['NameValue']
 elif probe=='bad_fraction':lights[0]['CreatedValue']['FractionTicks']=True
 elif probe=='empty_scene':scene['LightValues']=[];request['members']['LightIds']=[]
 execute('InputRejects/'+probe,'build',request,expected=False)
for probe in ('nonfinite_coefficient','nonfinite_direction'):execute('InputRejects/'+probe,'build',dict(base,member_probe=probe),expected=False)
for probe in ('foreign_environment','foreign_cabinet','existing_members','configuration_alias','multiple_configurations'):execute('AttachRejects/'+probe,'build',dict(base,attach_probe=probe),expected=False)
for probe in ('missing_member','foreign_member_owner','foreign_environment','lost_parent_log','duplicate_owner_log','unsupported_owner_path'):execute('RevisionRejects/'+probe,'build',dict(base,book_probe=probe),expected=False)
from base64 import b64decode,b64encode
for probe in ('config_trailer','resolved_map_base','truncated_manager'):
 request=deepcopy(base);request['payloads']=deepcopy(builds['D01']['payloads']);key={'config_trailer':'config','resolved_map_base':'resolved','truncated_manager':'manager'}[probe];data=b64decode(request['payloads'][key]);data=data+b'\0' if probe=='config_trailer' else ((int.from_bytes(data[:4],'little')+1).to_bytes(4,'little')+data[4:] if probe=='resolved_map_base' else data[:-1]);request['payloads'][key]=b64encode(data).decode();execute('WireRejects/'+probe,'audit',request,expected=False)
ambient={'owner_input':base['owner_input'],'light':{'NameValue':'Explicit ambient','ExternalName':'independent-id','AmbientValue':.173,'DiffuseValue':.487,'SpecularValue':.619,'ColourValue':0x38219B}}
pair=[]
for label in ('baseline','candidate'):
 sdk=root/('BaseRoot' if label=='baseline' else 'Code01');command=[str(args.python),'-B',str(tool/'AmbientPort01.py'),str(sdk),label];pair.append(execute('AmbientPort/'+label,'ambient',ambient,base=label=='baseline',custom=command))
require(pair[0]==pair[1],'port changed the independent source qualified ambient constructor bytes')
for variant in (0,1):
 pair=[]
 for label in ('BaseRoot','Code01'):
  output=out/'FullCompatibility'/(label+str(variant)+'.json');command=[str(args.python),'-B',str(root/label/'re/tooling/sw2026/throughpresentation/Compat.py'),'--root',str(root/label),'--variant',str(variant),'--output',str(output)];pair.append(execute('FullCompatibility/'+label+str(variant),'compat',None,custom=command))
 require(pair[0]==pair[1],'ordinary complete default container or public read changed')
verify()
for row in json.loads((root/'Inputs01.json').read_text())['inputs']:require(digest(Path(row['path']))==row['sha256'],'source changed during read only proof')
report={'schema':'kit.sw2026.throughall-system-members-process.v1','passed':True,'source_manifest_sha256':digest(root/'SourceManifest01.json'),'fresh_process_count':len(records),'negative_process_count':len(source_probes)+len(input_probes)+2+5+6+3,'positive_scenes':positives,'fragment_round_trips':30,'source_revision_headers_bound':6,'source_logs_per_header':28,'independent_dynamic_scene_sizes':[2,5],'old_ambient_six_fragment_identity':True,'old_default_fragment_pairs':3,'old_complete_container_pairs':2,'runtime_input_reads_during_construction':0,'heldout_inputs_read':0,'native_processes':0,'new_complete_native_outputs':0,'complete_source_preparation':False,'public_activation':False,'records':records};f=out/'Replay.json';f.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'negative_process_count':report['negative_process_count'],'sha256':digest(f)}))
