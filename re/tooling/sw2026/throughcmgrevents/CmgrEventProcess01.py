import argparse
from base64 import b64decode,b64encode
from copy import deepcopy
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
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectThruSrc import ProjectThruSrc
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.RequireThruFull import RequireThruFull
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruIntent import ReadThruIntent
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadThruMembers import ReadThruMembers
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruConfig import MakeThruConfig
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import ThruCfgIntent
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput
from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import MemberInput
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import NotesInput
from convert.adapters.solidworks.Archive.Construction.System.Members.AttachMembers import AttachMembers
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from OwnerDto import encode,decode,settings,require,safe_tree
from OwnerFragments import emit,identities,encode_fragments,decode_fragments,readback
from OwnerInspect import inspect
from OwnerGuard import OwnerGuard
from convert.adapters.solidworks.Archive.Views.ReadViewPair import ReadViewPair
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruView import ReadThruView
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruView import MakeThruView
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import EmptyMgrInput
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import ReadEmptyMgrs
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruMgrs import ReadThruMgrs
from convert.adapters.solidworks.Archive.Definition.LineTables.LinePattern import LinePattern
from convert.adapters.solidworks.Archive.Definition.LineTables.FontBinding import FontBinding
from convert.adapters.solidworks.Archive.Definition.LineTables.LineTableInput import LineTableInput
from convert.adapters.solidworks.Archive.Definition.LineTables.OrderFontBinds import OrderFontBinds
from convert.adapters.solidworks.Archive.Definition.LineTables.ReadLineTables import ReadLineTables
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruLines import ReadThruLines
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruLines import MakeThruLines
from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import AppearanceState
from convert.adapters.solidworks.Archive.Definition.PartUi.PartUiInput import PartUiInput
from convert.adapters.solidworks.Archive.Definition.PartUi.ReadPartUi import ReadPartUi
from convert.adapters.solidworks.Archive.Definition.PartUi.CountPartEnvs import CountPartEnvs
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruUi import ReadThruUi
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruUi import MakeThruUi
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.ConfigEvent import ConfigEvent
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.CmgrEvents import CmgrEvents
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.RequireCmgr import RequireCmgr
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.ApplyCmgrMut import ApplyCmgrMut
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.Events.ReadCfgEvent import ReadCfgEvent
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.Events.ReadThruEvents import ReadThruEvents
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.Events.MakeThruEvents import MakeThruEvents
for codec in ('ascii','utf-8','utf-16-le','utf-16-be','latin-1'):lookup(codec)
for name in ('interchange.document.Behavior.DocumentIo','interchange.document.Models.DocumentProvenance'):import_module(name)
guard=OwnerGuard();sys.addaudithook(guard.inspect);sys.setprofile(guard.profile)
def extra(event,arguments):
 if guard.active and event in ('ctypes.dlopen','ctypes.dlsym','socket.bind'):
  guard.denied.append(event);raise PermissionError('source view proof attempted external runtime access')
sys.addaudithook(extra);request=json.load(sys.stdin)

def intent(value):
 require(set(value)=={'ModelName','ManagerValue','DefinitionValue','DensityValue'},'unknown configuration intent');manager=dict(value['ManagerValue']);manager['ConfigValues']=tuple(ConfigSpec(**x) for x in manager['ConfigValues']);fields=dict(value['DefinitionValue']);fields['DisplayBits']=tuple(fields['DisplayBits']);fields['Tessellation']=tuple(fields['Tessellation']);return ThruCfgIntent(value['ModelName'],ManagerInput(**manager),ModelDefSettings(**fields),value['DensityValue'])

def members(value):
 require(set(value)=={'InputValue','NoteIds','LightIds'},'unknown member plan fields');safe_tree(value);scene=value['InputValue'];require(set(scene)=={'NotesValue','LightValues'},'unknown member input fields');notes=dict(scene['NotesValue']);notes['HeadCreated']=FeatureInstant(**notes['HeadCreated']);notes['EndCreated']=FeatureInstant(**notes['EndCreated']);lights=[]
 for entry in scene['LightValues']:
  light=dict(entry);light['CreatedValue']=FeatureInstant(**light['CreatedValue']);light['DirectionValue']=None if light['DirectionValue'] is None else tuple(light['DirectionValue']);lights.append(LightInput(**light))
 return MemberInput(NotesInput(**notes),tuple(lights))

def view(value):
 require(set(value)=={'MatrixValues','ShiftValues','ScaleValue'},'unknown view semantic input fields');return ViewInput(tuple(value['MatrixValues']),tuple(value['ShiftValues']),value['ScaleValue'])

def managers(value):
 require(set(value)=={'BomOnWire','AppearanceValue'},'unknown empty manager semantic inputs');return EmptyMgrInput(value['BomOnWire'],AppearanceState(**value['AppearanceValue']))

def manager_bits(fields):
 bom=fields['fab8'];result={'bom_present':bom is not None,'bom_class':None if bom is None else bom.ClassValue.NameValue,'bom_count':None if bom is None else bom.FieldsValue['n'],'bom_rows':None if bom is None else len(bom.FieldsValue['f08']),'appearance_present':fields['has_pwmaterial']}
 if fields['has_pwmaterial']:
  value=fields['f1110'];result.update(appearance_low=value['f08'],appearance_high=value['f0c'],appearance_count=value['list']['n'],appearance_rows=len(value['list']['items']))
 return result

def pair_bits(fields):
 result=[]
 for key in ('fae8','faf0'):
  row=fields[key];result.append({'matrix_present':row['has_matrix'],'matrix':[float(row['f08']['m'+str(i)]).hex() for i in range(9)] if row['has_matrix'] else None,'translation':[float(row[x]).hex() for x in ('f58','f60','f68')],'scale':float(row['f70']).hex(),'flags':row['f78']})
 return result

def source():
 path=Path(request['path']);raw=path.read_bytes();require(sha256(raw).hexdigest()==request['sha256'],'disclosed source custody differs');document=open_document(path);before=document.to_json();archive=SldprtArchive.from_bytes(raw);link=ReadNativeLink(archive,0);definition=ReadModelDef(archive.require('Contents/Definition'),19000).GraphValue;manager=ReadCmgrMut(archive.require('Contents/CMgr'),19000).RootValue;require(WriteModelDef(definition).OutputValue==archive.require('Contents/Definition') and WriteCmgrMut(manager,19000)==archive.require('Contents/CMgr'),'source typed stream round trips differ');fields=definition.DocumentValue.FieldsValue;probe=request.get('probe')
 if probe is not None:mutate_events(manager,probe)
 guard.active=True;plan=ProjectThruSrc(document,'Member'+request['name']);cfg=ReadThruIntent(document,link,manager,definition);scene=ReadThruMembers(document,link)
 try:RequireThruFull(plan.EnvelopeValue)
 except ValueError as error:refusal=str(error)
 else:raise ValueError('incomplete original source was admitted')
 event_input=asdict(ReadThruEvents(document,link,manager));camera=asdict(ReadThruView(document,link,definition));manager_input=asdict(ReadThruMgrs(document,link,definition));line_input=asdict(ReadThruLines(document,link,definition));ui_input=asdict(ReadThruUi(document,link,definition));env_count=CountPartEnvs(definition);require(document.to_json()==before,'source view projection changed complete source metadata')
 return {'events':event_input,'source_event_bits':event_bits(manager),'owner_input':encode(plan.InputValue),'config_intent':asdict(cfg),'members':asdict(scene),'view_input':camera,'manager_input':manager_input,'line_input':line_input,'ui_input':ui_input,'source_ui_bits':ui_bits(fields),'source_env_count':env_count,'source_line_bits':line_bits(fields),'source_pair_bits':pair_bits(fields),'document_sha256':sha256(before.encode()).hexdigest(),'full_refusal':refusal,'source_manager_definition_round_trips':2}

def lines(value):
 require(set(value)=={'PatternValues','BindingValues'},'unknown line semantic fields');patterns=[]
 for row in value['PatternValues']:
  part=dict(row);part['SegmentsValue']=tuple(part['SegmentsValue']);patterns.append(LinePattern(**part))
 return LineTableInput(tuple(patterns),tuple(FontBinding(**row) for row in value['BindingValues']))

def line_bits(fields):
 style=fields['f878'];font=fields['f870'];return {'style_count':style['n'],'font_count':font.FieldsValue['n'],'style_nodes':len({id(row['o']) for row in style['styles']}),'font_nodes':len({id(row['cfg']) for row in font.FieldsValue['f10']}),'patterns':[{'NameValue':row['o'].FieldsValue['f08'],'CaptionValue':row['o'].FieldsValue['f10'],'SegmentsValue':[value['seg'] for value in row['o'].FieldsValue['f18']],'ThickThinValue':bool(row['o'].FieldsValue['f20'])} for row in style['styles']],'bindings':[{'CategoryValue':row['key'],'FontName':row['cfg'].FieldsValue['f08'],'WeightValue':row['cfg'].FieldsValue['f10']['f06'],'EndCapValue':row['cfg'].FieldsValue['f18']} for row in font.FieldsValue['f10']]}

def ui_bits(fields):
 return {key:fields[key] for key in ('fad0','fad4','fb00','fb04')}

def prior_mutate_source(graph,probe):
 fields=graph.DocumentValue.FieldsValue;rows=fields['faf8'];env=rows[0]['o']
 if probe=='quality_reserved':fields['fad0']=65535
 elif probe=='quality_unqualified':fields['fad0']=2
 elif probe=='quality_boolean':fields['fad0']=True
 elif probe=='quality_missing':fields.pop('fad0')
 elif probe=='grid_unsupported_bits':fields['fad4']=6
 elif probe=='grid_missing_seed':fields['fad4']=0
 elif probe=='grid_boolean':fields['fad4']=True
 elif probe=='grid_missing':fields.pop('fad4')
 elif probe=='context_unconfirmed':fields['fb00']=0
 elif probe=='context_assembly':fields['fb00']=2
 elif probe=='context_drawing':fields['fb00']=3
 elif probe=='context_boolean':fields['fb00']=True
 elif probe=='context_missing':fields.pop('fb00')
 elif probe=='group_drawing':fields['fb04']=38283
 elif probe=='group_unqualified':fields['fb04']=12345
 elif probe=='group_boolean':fields['fb04']=False
 elif probe=='group_missing':fields.pop('fb04')
 elif probe=='display_mode':fields['facc']=2
 elif probe=='display_boolean':fields['facc']=True
 elif probe=='count_mismatch':fields['nenv']+=1
 elif probe=='count_boolean':fields['nenv']=True
 elif probe=='count_negative':fields['nenv']=-1
 elif probe=='count_overflow':fields['nenv']=65536
 elif probe=='count_missing':fields.pop('nenv')
 elif probe=='environment_rows_missing':fields.pop('faf8')
 elif probe=='environment_unknown_row':rows[0]['unmodeled']=0
 elif probe=='environment_alias':rows.append({'o':env});fields['nenv']=2
 elif probe=='environment_null':rows[0]['o']=None
 elif probe=='environment_wrong_class':env.ClassValue=RuntimeClass('uiLineFontMgr_c',1)
 elif probe=='environment_wrong_schema':env.ClassValue=RuntimeClass('uiUserModelEnv_c',2)
 elif probe=='wrong_schema':graph.DocumentValue.ClassValue=RuntimeClass('uiPartDoc_c',2)
 elif probe=='wrong_class':graph.DocumentValue.ClassValue=RuntimeClass('uiAssemblyDoc_c',1)
 elif probe=='wrong_version':object.__setattr__(graph,'VersionValue',18000)
 else:raise ValueError('unknown part ui source probe')

def event_input(value):
 require(type(value) is dict and set(value)=={'ManagerValue','ActiveValue'},'unknown event transport fields')
 def single(row):
  require(set(row)=={'MomentValue','CreatedBy'},'unknown single event transport fields');return ConfigEvent(FeatureInstant(**row['MomentValue']),FeatureTarget(**row['CreatedBy']))
 return CmgrEvents(single(value['ManagerValue']),single(value['ActiveValue']))

def event_words(node):
 keys=('f29c','f2a0','f2a4','f2b0','f2b4','f2ac','f300','f301','f2b8','f2bc');return {key:node.FieldsValue.get(key) for key in keys}

def event_bits(manager):
 active=RequireCmgr(manager);rows=manager.FieldsValue['f370']['items'];return {'manager_class':manager.ClassValue.NameValue,'active_class':active.ClassValue.NameValue,'manager_native_id':manager.FieldsValue['f08'],'active_native_id':active.FieldsValue['f08'],'manager_words':event_words(manager),'active_words':event_words(active),'manager_event':asdict(ReadCfgEvent(manager)),'active_event':asdict(ReadCfgEvent(active)),'distinct_owners':manager is not active,'directory_alias':len(rows)==1 and rows[0]['o'] is active and manager.FieldsValue['f368'] is active}

def mutate_events(manager,probe):
 fields=manager.FieldsValue;active=fields['f360'];part=active.FieldsValue;scope,key,value=probe.split(':',2) if ':' in probe else ('','','')
 if scope in ('manager','active'):
  target=fields if scope=='manager' else part
  if value=='missing':target.pop(key)
  else:target[key]=json.loads(value)
 elif probe=='manager_class':manager.ClassValue=RuntimeClass('moPartConfiguration_c',1)
 elif probe=='manager_schema':manager.ClassValue=RuntimeClass('moConfigurationMgr_c',2)
 elif probe=='active_class':active.ClassValue=RuntimeClass('moConfigurationMgr_c',1)
 elif probe=='active_schema':active.ClassValue=RuntimeClass('moPartConfiguration_c',2)
 elif probe=='selector_copy':fields['f368']=deepcopy(active)
 elif probe=='row_copy':fields['f370']['items'][0]['o']=deepcopy(active)
 elif probe=='directory_count':fields['f370']['n']+=1
 elif probe=='allocation_count':fields['f40c']+=1
 elif probe=='extra_configuration':fields['f370']['items'].append({'o':deepcopy(active)});fields['f370']['n']+=1;fields['f40c']+=1
 elif probe=='configuration_name':part['f18'].FieldsValue['f08']='different source configuration'
 else:raise ValueError('unknown event source probe')

def mutate_fresh(system,probe,target):
 manager=system.ManagerValue;active=system.ConfigValues[0]
 if probe=='wrong_type':return
 if probe=='manager_owner':manager.FieldsValue['owner']=active
 elif probe=='active_owner':active.FieldsValue['owner']=manager
 elif probe=='foreign_selected':object.__setattr__(system,'ConfigValues',(deepcopy(active),))
 elif probe=='manager_stamped':manager.FieldsValue['f2a0']=1
 elif probe=='active_stamped':active.FieldsValue['f2a4']=1
 elif probe=='manager_update':manager.FieldsValue['f29c']=102
 elif probe=='active_update':active.FieldsValue['f2b8']=19000
 elif probe=='target_provenance':manager.FieldsValue['f301']=1
 elif probe=='selector_copy':manager.FieldsValue['f368']=deepcopy(active)
 else:raise ValueError('unknown fresh manager event probe')

def build():
 guard.active=True;require(set(request)<= {'owner_input','config_intent','members','view_input','manager_input','line_input','ui_input','events','input_probe'},'unknown builder request fields');value=decode(request['owner_input']);target=settings(value,1795107901);config=intent(request['config_intent']);scene=members(request['members']);camera=view(request['view_input']);manager_input=managers(request['manager_input']);line_input=lines(request['line_input']);ui_input=PartUiInput(**request['ui_input']);events=event_input(request['events']);probe=request.get('input_probe')
 if probe is None:graph=MakeThruEvents(value,target,config,camera,manager_input,line_input,ui_input,events)
 else:
  graph=MakeThruUi(value,target,config,camera,manager_input,line_input,ui_input);system=graph.OwnersValue.SystemValue;mutate_fresh(system,probe,target);before=event_words(system.ManagerValue);selected=system.ConfigValues[0];before_selected=event_words(selected)
  try:ApplyCmgrMut(system,request['events'] if probe=='wrong_type' else events,target.TargetValue)
  except Exception:
   require(before==event_words(system.ManagerValue) and before_selected==event_words(selected),'refused manager event partially changed feature fields');raise
 owners=graph.OwnersValue;system=owners.SystemValue;AttachMembers(system,scene,target.TargetValue,owners.IdsValue);data,parsed,resolved=emit(owners,target);grammar=inspect(value,parsed,resolved,True);wire=WriteModelDef(graph.DefinitionValue).OutputValue;decoded=ReadModelDef(wire,19000);require(WriteModelDef(decoded.GraphValue).OutputValue==wire,'fresh source Definition does not reemit');require(ReadEmptyMgrs(decoded.GraphValue)==manager_input,'source empty manager state changed');actual=ReadLineTables(decoded.GraphValue);require(actual.PatternValues==line_input.PatternValues and OrderFontBinds(actual.BindingValues)==OrderFontBinds(line_input.BindingValues),'source line semantics differ');require(ReadPartUi(decoded.GraphValue)==ui_input,'fresh part ui semantics differ')
 return {'event_bits':event_bits(system.ManagerValue),'fragments':identities(data),'payloads':encode_fragments(data),'definition':{'sha256':sha256(wire).hexdigest(),'bytes':len(wire)},'definition_payload':b64encode(wire).decode(),'pair_bits':pair_bits(decoded.GraphValue.DocumentValue.FieldsValue),'manager_bits':manager_bits(decoded.GraphValue.DocumentValue.FieldsValue),'line_bits':line_bits(decoded.GraphValue.DocumentValue.FieldsValue),'ui_bits':ui_bits(decoded.GraphValue.DocumentValue.FieldsValue),'env_count':CountPartEnvs(decoded.GraphValue),'grammar':grammar}

def audit():
 guard.active=True;data=decode_fragments(request['payloads']);config,resolved,manager,_=readback(data);value=decode(request['owner_input']);grammar=inspect(value,config,resolved);wire=b64decode(request['definition_payload'],validate=True);definition=ReadModelDef(wire,19000);require(WriteModelDef(definition.GraphValue).OutputValue==wire,'independent Definition wire changed');fields=definition.GraphValue.DocumentValue.FieldsValue;actual=ReadViewPair(fields['fae8'],fields['faf0']);require(actual==view(request['view_input']),'independent camera input differs');require(ReadEmptyMgrs(definition.GraphValue)==managers(request['manager_input']),'independent empty manager semantic state differs');read=ReadLineTables(definition.GraphValue);expected=lines(request['line_input']);require(read.PatternValues==expected.PatternValues and OrderFontBinds(read.BindingValues)==OrderFontBinds(expected.BindingValues),'independent line semantic values differ');require(ReadPartUi(definition.GraphValue)==PartUiInput(**request['ui_input']),'independent ui semantic values differ');require(asdict(CmgrEvents(ReadCfgEvent(manager.RootValue),ReadCfgEvent(RequireCmgr(manager.RootValue))))==request['events'],'independent manager feature events differ');return {'event_bits':event_bits(manager.RootValue),'fragments':identities(data),'definition':{'sha256':sha256(wire).hexdigest(),'bytes':len(wire)},'pair_bits':pair_bits(fields),'manager_bits':manager_bits(fields),'line_bits':line_bits(fields),'ui_bits':ui_bits(fields),'env_count':CountPartEnvs(definition.GraphValue),'grammar':grammar,'round_trips':7}

try:
 result=source() if args.phase=='source' else audit() if args.phase=='audit' else build();result.update(passed=True,phase=args.phase,denied_events=guard.denied,guarded_input_reads=0,heldout_inputs_read=0,native_processes=0,complete_source_preparation=False,new_complete_native_outputs=0,public_activation=False);code=0
except Exception as error:
 trace=[];tb=error.__traceback__
 while tb is not None:trace.append({'file':tb.tb_frame.f_code.co_filename.rsplit('/',1)[-1],'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno,'sdk_module':str(args.sdk/'src') in tb.tb_frame.f_code.co_filename});tb=tb.tb_next
 result={'passed':False,'phase':args.phase,'error_type':type(error).__name__,'error':str(error),'trace':trace,'denied_events':guard.denied};code=3
finally:guard.active=False;sys.setprofile(None)
print(json.dumps(result,sort_keys=True,allow_nan=False));raise SystemExit(code)
