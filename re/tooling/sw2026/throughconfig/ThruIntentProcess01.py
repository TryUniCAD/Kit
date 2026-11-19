import argparse
from base64 import b64decode,b64encode
from codecs import lookup
from dataclasses import asdict,replace,fields
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--phase',required=True);args=parser.parse_args()
sys.dont_write_bytecode=True;sys.path.insert(0,str(args.sdk/'src'));sys.path.insert(0,str(args.sdk/'re/tooling/sw2026/throughowners'))
from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectThruSrc import ProjectThruSrc
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.RequireThruFull import RequireThruFull
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Construction.Configuration.ReadMgrIntent import ReadMgrIntent
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings
from convert.adapters.solidworks.Core.Preparation.Revolve.Source.ReadRevUi import ReadRevUi
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MakeThruOwners import MakeThruOwners
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from OwnerDto import encode,decode,settings,canonical,require,safe_tree
from OwnerFragments import emit,identities,encode_fragments,decode_fragments,readback
from OwnerInspect import inspect
from OwnerGuard import OwnerGuard
if args.phase not in ('legacy','baseline'):
 from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import ThruCfgIntent
 from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruConfig import MakeThruConfig
 from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruIntent import ReadThruIntent
for encoding in ('utf-16-le','utf-16-be','utf-8','latin-1','ascii'):lookup(encoding)
for name in ('interchange.document.Behavior.DocumentIo','interchange.document.Models.DocumentProvenance'):import_module(name)
guard=OwnerGuard();sys.addaudithook(guard.inspect);sys.setprofile(guard.profile)
def extra_audit(event,arguments):
 if guard.active and event in ('ctypes.dlopen','ctypes.dlsym','os.exec','os.posix_spawn','os.fork','socket.bind'):
  guard.denied.append(event);raise PermissionError('source component attempted external runtime access: '+event)
sys.addaudithook(extra_audit)
request=json.load(sys.stdin)

def walk(value,seen=None):
 if seen is None:seen=set()
 if id(value) in seen:return
 seen.add(id(value))
 if hasattr(value,'FieldsValue'):
  yield value;yield from walk(value.FieldsValue,seen)
 elif isinstance(value,dict):
  for child in value.values():yield from walk(child,seen)
 elif isinstance(value,(tuple,list)):
  for child in value:yield from walk(child,seen)

def intent_decode(value):
 require(set(value)=={'ModelName','ManagerValue','DefinitionValue','DensityValue'},'intent transport has unknown or missing fields');safe_tree(value)
 manager=dict(value['ManagerValue']);manager['ConfigValues']=tuple(ConfigSpec(**x) for x in manager['ConfigValues']);manager=ManagerInput(**manager)
 definition=dict(value['DefinitionValue']);definition['DisplayBits']=tuple(definition['DisplayBits']);definition['Tessellation']=tuple(definition['Tessellation'])
 return ThruCfgIntent(value['ModelName'],manager,ModelDefSettings(**definition),value['DensityValue'])

def full_refusal(plan):
 reasons=[]
 for env in (plan.EnvelopeValue,replace(plan.EnvelopeValue,UnmappedPaths=())):
  try:RequireThruFull(env)
  except ValueError as error:reasons.append(str(error))
  else:raise ValueError('incomplete original source was admitted')
 return reasons

def inventory_headers(archive,link):
 nodes=list(walk((link.ConfigValue.RootValue,link.ResolvedValue.RootsValue)));byid={n.FieldsValue['f08']:n for n in nodes if 'f2a0' in n.FieldsValue and type(n.FieldsValue.get('f08')) is int and n.FieldsValue['f08']>=0};byid[link.ConfigValue.RootValue.FieldsValue['f08']]=link.ConfigValue.RootValue
 output=[]
 for stream in ('Contents/Config-0-ModelHeader','Header2'):
  header=ReadHeaderGraph(archive.require(stream),19000);logs=ReadLogItems(header.FieldsValue['f20'],'moLogs_c');require(WriteHeadGraph(header,19000)==archive.require(stream),'source header round trip differs')
  members=[]
  for log in logs:
   owner=byid[log.FieldsValue['f48']]
   if owner.ClassValue.NameValue in ('moNotesAreaFtrFolder_c','moAmbientLight_c','moDirectionLight_c'):members.append({'source_id':owner.FieldsValue['f08'],'class':owner.ClassValue.NameValue,'events':len(ReadLogItems(log,'moStamp_c'))})
  output.append({'stream':stream,'log_count':len(logs),'unconstructed_log_owners':members,'exact_source_reemission':True})
 return output

def differing_paths(left,right,prefix='',seen=None):
 if seen is None:seen=set()
 if (id(left),id(right)) in seen:return []
 seen.add((id(left),id(right)))
 if hasattr(left,'FieldsValue') and hasattr(right,'FieldsValue'):
  if left.ClassValue!=right.ClassValue:return [prefix+'/@class']
  return differing_paths(left.FieldsValue,right.FieldsValue,prefix,seen)
 if isinstance(left,dict) and isinstance(right,dict):
  result=[]
  for key in sorted(set(left)|set(right)):
   if key not in left or key not in right:result.append(prefix+'/'+str(key))
   else:result.extend(differing_paths(left[key],right[key],prefix+'/'+str(key),seen))
  return result
 if isinstance(left,(tuple,list)) and isinstance(right,(tuple,list)):
  if len(left)!=len(right):return [prefix+'/@length']
  return [path for i,(a,b) in enumerate(zip(left,right,strict=True)) for path in differing_paths(a,b,prefix+'/'+str(i),seen)]
 return [] if left==right else [prefix]

def source_phase():
 path=Path(request['source']);raw=path.read_bytes();require(sha256(raw).hexdigest()==request['sha256'],'source custody differs');document=open_document(path);before=document.to_json();archive=SldprtArchive.from_bytes(raw);link=ReadNativeLink(archive,0);manager=ReadCmgrMut(archive.require('Contents/CMgr'),19000).RootValue;definition=ReadModelDef(archive.require('Contents/Definition'),19000).GraphValue
 probe=request.get('probe')
 if probe=='foreign_selector':manager.FieldsValue['f368']=replace(manager.FieldsValue['f360'])
 elif probe=='missing_manager_name':manager.FieldsValue.pop('f18')
 elif probe=='empty_manager_name':manager.FieldsValue['f18']=link.ConfigValue.RootValue.FieldsValue['f18'];manager.FieldsValue['f18'].FieldsValue['f08']=''
 elif probe=='wrong_manager_schema':manager=replace(manager,ClassValue=replace(manager.ClassValue,SchemaValue=0))
 elif probe=='directory_count':manager.FieldsValue['f370']['n']+=1
 elif probe=='configuration_epoch':manager.FieldsValue['f360'].FieldsValue['f678']=-1
 elif probe=='stale_public_configuration':document=replace(document,configurations=(replace(document.configurations[0],name='Foreign config'),))
 elif probe=='wrong_link_version':link=replace(link,ConfigValue=replace(link.ConfigValue,VersionValue=18000))
 elif probe=='root_order':link=replace(link,ResolvedValue=replace(link.ResolvedValue,RootsValue=tuple(reversed(link.ResolvedValue.RootsValue))))
 elif probe=='changed_root_caption':link.ResolvedValue.RootsValue[-1].FieldsValue['f18'].FieldsValue['f08']='Foreign cut'
 elif probe=='ui_bool':definition.DocumentValue.FieldsValue['fa64']=2
 elif probe=='ui_density':definition.DocumentValue.FieldsValue['f1688']=-1.0
 elif probe=='ui_display_word':definition.DocumentValue.FieldsValue['fad8_0']=1<<40
 elif probe=='ui_journal':NativeRecord(definition.DocumentValue.FieldsValue['ffd8'])['f18'].FieldsValue['f08']=''
 elif probe is not None:raise ValueError('unknown source probe')
 guard.active=True
 plan=ProjectThruSrc(document,'Independent'+request['name']+'Destination')
 refusal=full_refusal(plan)
 result={'document_sha256':sha256(document.to_json().encode()).hexdigest(),'full_refusal':refusal,'unmapped':plan.EnvelopeValue.UnmappedPaths,'source_headers':inventory_headers(archive,link),'owner_input':encode(plan.InputValue),'source_document_retained':plan.EnvelopeValue.DocumentValue is document}
 if args.phase=='source':
  intent=ReadThruIntent(document,link,manager,definition);result['intent']=asdict(intent)
  generated=MakeThruConfig(plan.InputValue,settings(plan.InputValue,1795106201),intent)
  result['remaining_definition_difference_paths']=differing_paths(definition.DocumentValue,ReadModelDef(WriteModelDef(generated.DefinitionValue).OutputValue,19000).GraphValue.DocumentValue,'Definition')
  result['remaining_manager_difference_paths']=differing_paths(manager,ReadCmgrMut(WriteCmgrMut(generated.OwnersValue.SystemValue.ManagerValue,19000),19000).RootValue,'CMgr')
  require(result['remaining_definition_difference_paths'] and result['remaining_manager_difference_paths'],'partial source fields were presented as complete native owners')
  require(document.to_json()==before,'source projection mutated the complete document')
 require(WriteCmgrMut(manager,19000)==archive.require('Contents/CMgr'),'source manager re-emission differs')
 require(WriteModelDef(definition).OutputValue==archive.require('Contents/Definition'),'source Definition re-emission differs')
 result['source_manager_definition_round_trips']=2
 return result

def build_phase():
 guard.active=True
 value=decode(request['owner_input']);target=settings(value,request['written_at'])
 if args.phase=='legacy':
  owners=MakeThruOwners(value,target);definition=None
 else:
  intent=intent_decode(request['intent']);configured=MakeThruConfig(value,target,intent);owners=configured.OwnersValue;definition=configured.DefinitionValue
 fragments,config,resolved=emit(owners,target);grammar=inspect(value,config,resolved,True)
 result={'fragments':identities(fragments),'payloads':encode_fragments(fragments),'grammar':grammar,'root_name':ReadNodeName(owners.SystemValue.RootValue),'manager_intent':asdict(ReadMgrIntent(owners.SystemValue.ManagerValue)),'binding_count':len(owners.BindValues)}
 if definition is not None:
  wire=WriteModelDef(definition);reread=ReadModelDef(wire.OutputValue,19000);require(WriteModelDef(reread.GraphValue).OutputValue==wire.OutputValue,'generated Definition changed on readback');require(asdict(ReadRevUi(reread.GraphValue))=={'SettingsValue':asdict(intent.DefinitionValue),'DensityValue':intent.DensityValue},'generated document settings differ')
  result.update(definition_payload=b64encode(wire.OutputValue).decode(),definition={'sha256':sha256(wire.OutputValue).hexdigest(),'bytes':len(wire.OutputValue)},definition_intent=asdict(ReadRevUi(reread.GraphValue)))
  require(ReadNodeName(owners.SystemValue.RootValue)==intent.ModelName and ReadMgrIntent(owners.SystemValue.ManagerValue)==intent.ManagerValue,'constructed source identity or configuration intent differs')
 return result

def read_phase():
 guard.active=True
 expected=intent_decode(request['intent']);value=decode(request['owner_input']);fragments=decode_fragments(request['payloads']);config,resolved,manager,_=readback(fragments);grammar=inspect(value,config,resolved)
 actual=ReadMgrIntent(manager.RootValue);require(actual==expected.ManagerValue,'independently read manager intent differs');require(ReadNodeName(config.RootValue)==expected.ModelName,'source model identity was replaced by physical output title')
 data=b64decode(request['definition_payload'],validate=True);definition=ReadModelDef(data,19000);require(WriteModelDef(definition.GraphValue).OutputValue==data,'Definition independently re-emitted differently');ui=ReadRevUi(definition.GraphValue);require(ui.SettingsValue==expected.DefinitionValue and ui.DensityValue==expected.DensityValue,'source document preferences were defaulted')
 return {'fragments':identities(fragments),'definition':{'sha256':sha256(data).hexdigest(),'bytes':len(data)},'manager_intent':asdict(actual),'root_name':ReadNodeName(config.RootValue),'grammar':grammar,'round_trips':7}

try:
 result=source_phase() if args.phase in ('source','baseline') else read_phase() if args.phase=='readback' else build_phase()
 result.update(passed=True,phase=args.phase,runtime_input_file_reads=0,denied_events=guard.denied,full_native_outputs=0,native_acceptance=False,complete_source_preparation=False,heldout_inputs_read=0)
 status=0
except Exception as error:
 result={'passed':False,'phase':args.phase,'error_type':type(error).__name__,'error':str(error),'denied_events':guard.denied};status=3
finally:guard.active=False;sys.setprofile(None)
print(json.dumps(result,sort_keys=True,allow_nan=False));raise SystemExit(status)
