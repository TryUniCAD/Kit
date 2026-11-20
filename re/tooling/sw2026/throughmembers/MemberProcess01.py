import argparse
from base64 import b64decode,b64encode
from codecs import lookup
from dataclasses import asdict,replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--phase',required=True);args=parser.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(args.sdk/'src'));sys.path.insert(0,str(args.sdk/'re/tooling/sw2026/throughowners'))
from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectThruSrc import ProjectThruSrc
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.RequireThruFull import RequireThruFull
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruIntent import ReadThruIntent
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruConfig import MakeThruConfig
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import ThruCfgIntent
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Chronology.HeaderClocks import HeaderClocks
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import RevisionBook
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import RevisionLog
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import RevisionEvent
from convert.adapters.solidworks.Archive.Construction.Chronology.CheckLogOwners import CheckLogOwners
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeIntentHead import MakeIntentHead
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MakeThruOwners import MakeThruOwners
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from OwnerDto import canonical,encode,decode,settings,require,safe_tree
from OwnerFragments import emit,identities,encode_fragments,decode_fragments,readback
from OwnerInspect import inspect
from OwnerGuard import OwnerGuard
if args.phase!='legacy':
 from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import MemberInput
 from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
 from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import NotesInput
 from convert.adapters.solidworks.Archive.Construction.System.Members.AttachMembers import AttachMembers
 from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadThruMembers import ReadThruMembers
 from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import ReadNotesInput
 from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
for codec in ('ascii','utf-8','utf-16-le','utf-16-be','latin-1'):lookup(codec)
for name in ('interchange.document.Behavior.DocumentIo','interchange.document.Models.DocumentProvenance'):import_module(name)
guard=OwnerGuard();sys.addaudithook(guard.inspect);sys.setprofile(guard.profile)
def extra(event,arguments):
 if guard.active and event in ('ctypes.dlopen','ctypes.dlsym','socket.bind'):
  guard.denied.append(event);raise PermissionError('member proof attempted external runtime access')
sys.addaudithook(extra);request=json.load(sys.stdin)

def intent(value):
 require(set(value)=={'ModelName','ManagerValue','DefinitionValue','DensityValue'},'unknown configuration intent')
 m=dict(value['ManagerValue']);m['ConfigValues']=tuple(ConfigSpec(**x) for x in m['ConfigValues']);d=dict(value['DefinitionValue']);d['DisplayBits']=tuple(d['DisplayBits']);d['Tessellation']=tuple(d['Tessellation'])
 return ThruCfgIntent(value['ModelName'],ManagerInput(**m),ModelDefInput(**d),value['DensityValue'])

def members(value):
 require(set(value)=={'InputValue','NoteIds','LightIds'},'unknown member plan fields');safe_tree(value);x=value['InputValue'];require(set(x)=={'NotesValue','LightValues'},'unknown member input fields');notes=dict(x['NotesValue']);notes['HeadCreated']=FeatureInstant(**notes['HeadCreated']);notes['EndCreated']=FeatureInstant(**notes['EndCreated']);lights=[]
 for entry in x['LightValues']:
  light=dict(entry);light['CreatedValue']=FeatureInstant(**light['CreatedValue']);light['DirectionValue']=None if light['DirectionValue'] is None else tuple(light['DirectionValue']);lights.append(LightInput(**light))
 ids=tuple(value['NoteIds'])+tuple(value['LightIds']);require(len(value['NoteIds'])==2 and len(value['LightIds'])==len(lights) and len(set(ids))==len(ids) and all(type(x) is str and x for x in ids),'source member correspondence lost actual distinct identities')
 return MemberInput(NotesInput(**notes),tuple(lights))

def refs(link):
 result={};root=link.ConfigValue.RootValue
 for node in (root,*link.ResolvedValue.RootsValue):
  key=node.FieldsValue['f08'];require(key not in result,'source roots have ambiguous IDs');result[key]=node
  if node.ClassValue.NameValue in ('moDetailCabinet_c','moEnvFolder_c'):
   for child in ReadChildren(node):require(child.FieldsValue['f08'] not in result,'source child identity collides');result[child.FieldsValue['f08']]=child
 return result

def text(value):return value if type(value) is str else value.TextValue

def source_books(archive,link):
 byid=refs(link);result=[]
 for stream in ('Contents/Config-0-ModelHeader','Header2'):
  h=ReadHeaderGraph(archive.require(stream),19000);f=h.FieldsValue;users=[text(x) for x in f['f10'].FieldsValue['values']];companies=[text(x) for x in f['f18'].FieldsValue['values']];logs=[]
  for log in ReadLogItems(f['f20'],'moLogs_c'):
   field=log.FieldsValue;node=byid[field['f48']];key='$model' if node is link.ConfigValue.RootValue else 'sldprt:feature:'+str(node.FieldsValue['f08']);events=[]
   for event in ReadLogItems(log,'moStamp_c'):
    v=event.FieldsValue;operation={0:'created',1:'modified'}.get(v['f08']);require(operation is not None,'source log operation outside mapped scope');events.append(asdict(RevisionEvent(operation,users[v['f0c']],companies[v['f10']],v['f18'],text(v['f20']))))
   logs.append({'source_id':key,'caption':text(field['f50']),'events':events})
  require(len(logs)==len(byid)==28,'source revisions do not cover all actual ordinary owners');result.append({'clocks':{'CreatedAt':f['f70'],'ArchiveAt':f['f50'],'UpdatedAt':f['f48']},'users':users,'companies':companies,'logs':logs})
 return result

def source():
 path=Path(request['path']);raw=path.read_bytes();require(sha256(raw).hexdigest()==request['sha256'],'disclosed source custody changed');doc=open_document(path);before=doc.to_json();archive=SldprtArchive.from_bytes(raw);link=ReadNativeLink(archive,0);rootnodes=refs(link);cabinet=next(x for x in link.ResolvedValue.RootsValue if x.ClassValue.NameValue=='moDetailCabinet_c');env=next(x for x in link.ResolvedValue.RootsValue if x.ClassValue.NameValue=='moEnvFolder_c');notes=ReadChildren(cabinet);lights=ReadChildren(env)
 probe=request.get('probe')
 if probe=='notes_reverse':cabinet.FieldsValue['f60']['list']['items']=list(reversed(cabinet.FieldsValue['f60']['list']['items']))
 elif probe=='notes_foreign_partner':notes[0].FieldsValue['f388']=replace(notes[1])
 elif probe=='notes_wrong_marker':notes[1].FieldsValue['f37c']=1
 elif probe=='notes_contents':notes[0].FieldsValue['f60']={'list':{'n':1,'items':[{'o':link.ResolvedValue.RootsValue[-1]}]},'tail':0}
 elif probe=='foreign_environment':link.ConfigValue.RootValue.FieldsValue['f1e0']=replace(env)
 elif probe=='light_unknown_kind':lights[1].ClassValue=replace(lights[1].ClassValue,NameValue='moPointLight_c')
 elif probe=='light_boolean':lights[0].FieldsValue['f388']=2
 elif probe=='light_state':lights[0].FieldsValue['state']=1
 elif probe=='light_view_space':lights[0].FieldsValue['f428']=0
 elif probe=='light_duplicate_word':lights[0].FieldsValue['f384#0']=1
 elif probe=='light_user_property':lights[0].FieldsValue['f500']={'n':1,'props':[{}]}
 elif probe=='light_zero_direction':lights[1].FieldsValue['f3b0']={'x':0.0,'y':0.0,'z':0.0}
 elif probe=='light_stale_identity':lights[1].FieldsValue['f08']+=100
 elif probe=='light_order':env.FieldsValue['f60']['list']['items']=list(reversed(env.FieldsValue['f60']['list']['items']))
 elif probe=='note_unset_time':notes[0].FieldsValue.update(f2a0=0,f2a4=0)
 elif probe is not None:raise ValueError('unknown source member probe')
 guard.active=True
 plan=ProjectThruSrc(doc,'Member'+request['name']);cfg=ReadThruIntent(doc,link,ReadCmgrMut(archive.require('Contents/CMgr'),19000).RootValue,ReadModelDef(archive.require('Contents/Definition'),19000).GraphValue);memberplan=ReadThruMembers(doc,link)
 try:RequireThruFull(plan.EnvelopeValue)
 except ValueError as error:refusal=str(error)
 else:raise ValueError('incomplete source was admitted')
 require(doc.to_json()==before,'source member projection changed complete source metadata')
 return {'owner_input':encode(plan.InputValue),'config_intent':asdict(cfg),'members':asdict(memberplan),'books':source_books(archive,link),'root_roles':[{'source_id':'sldprt:feature:'+str(node.FieldsValue['f08']),'class':node.ClassValue.NameValue} for node in link.ResolvedValue.RootsValue],'document_sha256':sha256(before.encode()).hexdigest(),'full_refusal':refusal,'source_member_count':len(notes)+len(lights),'source_ambient_kept_in_scene':memberplan.InputValue.LightValues[0].KeepInScene,'external_id_duplicates_allowed':len({x.ExternalName for x in memberplan.InputValue.LightValues})<len(memberplan.InputValue.LightValues)}

def owners_by_source(owners,membergraph):
 result={'$model':owners.SystemValue.RootValue};result.update({x.SourceId:x.Value for x in owners.BindValues if isinstance(x.Value,ArchiveNode)})
 unique={x.ClassValue.NameValue:x for x in owners.SystemValue.FeatureValues if x.ClassValue.NameValue!='moRefPlane_c'}
 for item in request['root_roles']:
  key=item['source_id']
  if key not in result:
   require(item['class'] in unique,'source revision root has no constructed role');result[key]=unique[item['class']]
 for key,node in zip(request['members']['NoteIds'],(membergraph.NotesValue.HeadValue,membergraph.NotesValue.EndValue),strict=True):result[key]=node
 for key,node in zip(request['members']['LightIds'],membergraph.LightValues,strict=True):result[key]=node
 return result

def revision_check(owners,membergraph):
 mapping=owners_by_source(owners,membergraph);outputs=[]
 for index,book in enumerate(request['books']):
  require(set(book)=={'users','companies','clocks','logs'},'unknown revision intent fields')
  require(all(set(entry)=={'source_id','caption','events'} for entry in book['logs']),'unknown revision owner intent')
  value=RevisionBook(tuple(book['users']),tuple(book['companies']),tuple(RevisionLog(mapping[x['source_id']],x['caption'],tuple(RevisionEvent(**e) for e in x['events'])) for x in book['logs']))
  probe=request.get('book_probe')
  if probe=='missing_member':
   env=owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'];env.FieldsValue['f60']['list']['items'].pop();env.FieldsValue['f60']['list']['n']-=1
  elif probe=='foreign_member_owner':membergraph.LightValues[0].FieldsValue['owner']=replace(owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'])
  elif probe=='foreign_environment':owners.SystemValue.RootValue.FieldsValue['f1e0']=replace(owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'])
  elif probe=='lost_parent_log':value=replace(value,LogsValue=tuple(x for x in value.LogsValue if x.OwnerValue is not owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c']))
  elif probe=='duplicate_owner_log':value=replace(value,LogsValue=(*value.LogsValue,value.LogsValue[-1]))
  elif probe=='unsupported_owner_path':membergraph.NotesValue.HeadValue.FieldsValue['owner']=owners.StockValue.FeatureValue
  elif probe is not None:raise ValueError('unknown revision probe')
  CheckLogOwners(owners.SystemValue.RootValue,value);header=MakeIntentHead(owners.SystemValue.RootValue,HeaderClocks(**book['clocks']),value,owners.IdsValue,index==0);wire=WriteHeadGraph(header,19000);decoded=ReadHeaderGraph(wire,19000);require(WriteHeadGraph(decoded,19000)==wire,'generated revision Header does not reemit');actual=ReadLogItems(decoded.FieldsValue['f20'],'moLogs_c');expected=tuple((mapping[x['source_id']].FieldsValue['f08'],x['caption']) for x in book['logs']);require(tuple((x.FieldsValue['f48'],text(x.FieldsValue['f50'])) for x in actual)==expected,'revision logs copied old source ids instead of actual target owners');outputs.append({'sha256':sha256(wire).hexdigest(),'bytes':len(wire),'logs':len(actual),'actual_target_ids':tuple(x.FieldsValue['f48'] for x in actual),'role':'model' if index==0 else 'top','round_trip':True,'native_chronology_qualification':False})
 return outputs

def inspect_members(system,expected):
 cabinet=system.SystemValues.CabinetValue;env=system.SystemValues.FolderValues['moEnvFolder_c'];notes=ReadChildren(cabinet);lights=ReadChildren(env);require(ReadNotesInput(notes)==expected.NotesValue and tuple(ReadLightInput(x) for x in lights)==expected.LightValues,'generated semantic member read differs');require(notes[0].FieldsValue['f388'] is notes[1] and notes[1].FieldsValue['f388'] is notes[0],'note partners lost reciprocal identity');return {'notes':tuple(x.FieldsValue['f08'] for x in notes),'lights':tuple(x.FieldsValue['f08'] for x in lights),'member_count':len(notes)+len(lights),'ambient_kept_in_scene':expected.LightValues[0].KeepInScene,'external_names':tuple(x.ExternalName for x in expected.LightValues),'directions':tuple(x.DirectionValue for x in expected.LightValues),'typed_input':asdict(expected)}

def build():
 guard.active=True
 value=decode(request['owner_input']);target=settings(value,1795107901)
 if args.phase=='legacy':
  owners=MakeThruOwners(value,target);data,config,resolved=emit(owners,target);return {'fragments':identities(data),'grammar':inspect(value,config,resolved,True)}
 configured=MakeThruConfig(value,target,intent(request['config_intent']));owners=configured.OwnersValue;expected=members(request['members']);before={(id(node),field):node.FieldsValue[field] for node,field in owners.IdsValue.Allocations};start=owners.IdsValue.NextValue;flags=(owners.SystemValue.RootValue.FieldsValue['f0c'],owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'].FieldsValue['f0c'])
 probe=request.get('member_probe')
 if probe=='nonfinite_coefficient':expected=replace(expected,LightValues=(replace(expected.LightValues[0],AmbientValue=float('nan')),*expected.LightValues[1:]))
 elif probe=='nonfinite_direction':expected=replace(expected,LightValues=(expected.LightValues[0],replace(expected.LightValues[1],DirectionValue=(float('nan'),1.0,0.0)),*expected.LightValues[2:]))
 elif probe is not None:raise ValueError('unknown member probe')
 probe=request.get('attach_probe')
 if probe=='foreign_environment':owners.SystemValue.RootValue.FieldsValue['f1e0']=replace(owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'])
 elif probe=='foreign_cabinet':owners=replace(owners,SystemValue=replace(owners.SystemValue,SystemValues=replace(owners.SystemValue.SystemValues,CabinetValue=replace(owners.SystemValue.SystemValues.CabinetValue))))
 elif probe=='existing_members':owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'].FieldsValue['f60']={'list':{'n':1,'items':[{'o':owners.StockValue.FeatureValue}]},'tail':0}
 elif probe=='configuration_alias':owners.SystemValue.ManagerValue.FieldsValue['f368']=replace(owners.SystemValue.ConfigValues[0])
 elif probe=='multiple_configurations':owners=replace(owners,SystemValue=replace(owners.SystemValue,ConfigValues=(*owners.SystemValue.ConfigValues,replace(owners.SystemValue.ConfigValues[0]))))
 elif probe is not None:raise ValueError('unknown attachment probe')
 graph=AttachMembers(owners.SystemValue,expected,target.TargetValue,owners.IdsValue);require(owners.IdsValue.NextValue==start+len(expected.LightValues)+2,'member counter does not derive from actual cardinality');require(all(node.FieldsValue[field]==before[(id(node),field)] for node,field in owners.IdsValue.Allocations if (id(node),field) in before),'member insertion changed previous geometry identities');require(flags==(owners.SystemValue.RootValue.FieldsValue['f0c'],owners.SystemValue.SystemValues.FolderValues['moEnvFolder_c'].FieldsValue['f0c']),'member construction suppressed part or environment update state')
 info=inspect_members(owners.SystemValue,expected);data,config,resolved=emit(owners,target);grammar=inspect(value,config,resolved,True);books=revision_check(owners,graph)
 return {'fragments':identities(data),'payloads':encode_fragments(data),'grammar':grammar,'members':info,'allocator_before':start,'allocator_after':owners.IdsValue.NextValue,'previous_ids_unchanged':True,'owner_flags_unchanged':True,'revision_headers':books,'resolved_root_count':len(resolved.RootsValue),'root_model_name':ReadNodeName(owners.SystemValue.RootValue)}

def audit():
 guard.active=True
 expected=members(request['members']);data=decode_fragments(request['payloads']);config,resolved,_,_=readback(data);root=config.RootValue;cabinet=next(x for x in resolved.RootsValue if x.ClassValue.NameValue=='moDetailCabinet_c');env=next(x for x in resolved.RootsValue if x.ClassValue.NameValue=='moEnvFolder_c');require(root.FieldsValue['f1e0'] is env,'received environment lost the inherited Config alias');notes=ReadChildren(cabinet);lights=ReadChildren(env);require(ReadNotesInput(notes)==expected.NotesValue and tuple(ReadLightInput(x) for x in lights)==expected.LightValues,'wire read lost member semantics');require(len(resolved.RootsValue)==21,'members were appended as spurious resolved roots');require(notes[0].FieldsValue['f388'] is notes[1] and notes[1].FieldsValue['f388'] is notes[0],'wire note partners lost actual alias identity');return {'fragments':identities(data),'member_count':len(notes)+len(lights),'resolved_roots':21,'round_trips':6,'light_ids':[x.FieldsValue['f08'] for x in lights],'note_ids':[x.FieldsValue['f08'] for x in notes]}

try:
 result=source() if args.phase=='source' else audit() if args.phase=='audit' else build();result.update(passed=True,phase=args.phase,denied_events=guard.denied,guarded_input_reads=0,heldout_inputs_read=0,native_processes=0,complete_source_preparation=False,full_native_outputs=0);code=0
except Exception as error:
 trace=[];tb=error.__traceback__
 while tb is not None:trace.append({'file':tb.tb_frame.f_code.co_filename.rsplit('/',1)[-1],'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno});tb=tb.tb_next
 result={'passed':False,'phase':args.phase,'error_type':type(error).__name__,'error':str(error),'trace':trace,'denied_events':guard.denied};code=3
finally:guard.active=False;sys.setprofile(None)
print(json.dumps(result,sort_keys=True,allow_nan=False));raise SystemExit(code)
