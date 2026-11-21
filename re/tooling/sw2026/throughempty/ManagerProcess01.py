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
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectThruSrc import ProjectThruSrc
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.RequireThruFull import RequireThruFull
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruIntent import ReadThruIntent
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadThruMembers import ReadThruMembers
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruConfig import MakeThruConfig
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import ThruCfgIntent
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
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
if args.phase not in ('legacy','source_base'):
 from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import EmptyMgrInput
 from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import ReadEmptyMgrs
 from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.ReadThruMgrs import ReadThruMgrs
 from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruMgrs import MakeThruMgrs
from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import AppearanceState
for codec in ('ascii','utf-8','utf-16-le','utf-16-be','latin-1'):lookup(codec)
for name in ('interchange.document.Behavior.DocumentIo','interchange.document.Models.DocumentProvenance'):import_module(name)
guard=OwnerGuard();sys.addaudithook(guard.inspect);sys.setprofile(guard.profile)
def extra(event,arguments):
 if guard.active and event in ('ctypes.dlopen','ctypes.dlsym','socket.bind'):
  guard.denied.append(event);raise PermissionError('source view proof attempted external runtime access')
sys.addaudithook(extra);request=json.load(sys.stdin)

def intent(value):
 require(set(value)=={'ModelName','ManagerValue','DefinitionValue','DensityValue'},'unknown configuration intent');manager=dict(value['ManagerValue']);manager['ConfigValues']=tuple(ConfigSpec(**x) for x in manager['ConfigValues']);fields=dict(value['DefinitionValue']);fields['DisplayBits']=tuple(fields['DisplayBits']);fields['Tessellation']=tuple(fields['Tessellation']);return ThruCfgIntent(value['ModelName'],ManagerInput(**manager),ModelDefInput(**fields),value['DensityValue'])

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
 if probe=='bom_wrong_class':fields['fab8'].ClassValue=RuntimeClass('moBomInfo_c',1)
 elif probe=='bom_wrong_schema':fields['fab8'].ClassValue=RuntimeClass('moBomInfoMgr_c',2)
 elif probe=='bom_populated':fields['fab8'].FieldsValue.update(n=1,f08=[{'o':None}])
 elif probe=='bom_count_mismatch':fields['fab8'].FieldsValue['n']=1
 elif probe=='bom_hidden_row':fields['fab8'].FieldsValue['f08']=[{'o':None}]
 elif probe=='bom_boolean_count':fields['fab8'].FieldsValue['n']=False
 elif probe=='bom_unknown_field':fields['fab8'].FieldsValue['unmapped_child']=None
 elif probe=='bom_missing_pointer':fields.pop('fab8')
 elif probe=='appearance_populated':fields['f1110']['list']={'n':1,'items':[{'o':None}]}
 elif probe=='appearance_hidden_row':fields['f1110']['list']['items']=[{'o':None}]
 elif probe=='appearance_count_mismatch':fields['f1110']['list']['n']=1
 elif probe=='appearance_boolean_count':fields['f1110']['list']['n']=False
 elif probe=='appearance_unknown_field':fields['f1110']['future_state']=1
 elif probe=='appearance_unknown_list':fields['f1110']['list']['future_state']=1
 elif probe=='appearance_missing_body':fields.pop('f1110')
 elif probe=='appearance_missing_low':fields['f1110'].pop('f08')
 elif probe=='appearance_missing_high':fields['f1110'].pop('f0c')
 elif probe=='appearance_low_outside':fields['f1110']['f08']=1<<31
 elif probe=='appearance_high_outside':fields['f1110']['f0c']=-(1<<31)-1
 elif probe=='appearance_boolean_word':fields['f1110']['f08']=True
 elif probe=='appearance_bad_presence':fields['has_pwmaterial']=2
 elif probe=='appearance_boolean_presence':fields['has_pwmaterial']=True
 elif probe=='appearance_absent_with_body':fields['has_pwmaterial']=0
 elif probe=='wrong_schema':definition.DocumentValue.ClassValue=RuntimeClass('uiPartDoc_c',2)
 elif probe=='wrong_class':definition.DocumentValue.ClassValue=RuntimeClass('uiAssemblyDoc_c',1)
 elif probe=='wrong_version':definition=replace(definition,VersionValue=18000)
 elif probe is not None:raise ValueError('unknown empty manager source probe')
 guard.active=True;plan=ProjectThruSrc(document,'Member'+request['name']);cfg=ReadThruIntent(document,link,manager,definition);scene=ReadThruMembers(document,link)
 try:RequireThruFull(plan.EnvelopeValue)
 except ValueError as error:refusal=str(error)
 else:raise ValueError('incomplete original source was admitted')
 camera=asdict(ReadThruView(document,link,definition));manager_input=None if args.phase=='source_base' else asdict(ReadThruMgrs(document,link,definition));require(document.to_json()==before,'source view projection changed complete source metadata')
 return {'owner_input':encode(plan.InputValue),'config_intent':asdict(cfg),'members':asdict(scene),'view_input':camera,'manager_input':manager_input,'source_pair_bits':pair_bits(fields),'document_sha256':sha256(before.encode()).hexdigest(),'full_refusal':refusal,'source_manager_definition_round_trips':2}

def build():
 guard.active=True;require(set(request)<= {'owner_input','config_intent','members','view_input','manager_input','input_probe'},'unknown builder request fields');value=decode(request['owner_input']);target=settings(value,1795107901);config=intent(request['config_intent']);scene=members(request['members']);camera=view(request['view_input']);manager_input=None if args.phase=='legacy' else managers(request['manager_input']);probe=request.get('input_probe')
 if probe=='wrong_type':manager_input=request['manager_input']
 elif probe is not None:raise ValueError('unknown empty manager input probe')
 graph=MakeThruView(value,target,config,camera) if args.phase=='legacy' else MakeThruMgrs(value,target,config,camera,manager_input);owners=graph.OwnersValue;AttachMembers(owners.SystemValue,scene,target.TargetValue,owners.IdsValue);data,parsed,resolved=emit(owners,target);grammar=inspect(value,parsed,resolved,True);wire=WriteModelDef(graph.DefinitionValue).OutputValue;decoded=ReadModelDef(wire,19000);require(WriteModelDef(decoded.GraphValue).OutputValue==wire,'fresh source camera Definition does not reemit');actual=pair_bits(decoded.GraphValue.DocumentValue.FieldsValue)
 if args.phase!='legacy':require(ReadEmptyMgrs(decoded.GraphValue)==manager_input,'source empty manager semantic values changed')
 return {'fragments':identities(data),'payloads':encode_fragments(data),'definition':{'sha256':sha256(wire).hexdigest(),'bytes':len(wire)},'definition_payload':b64encode(wire).decode(),'pair_bits':actual,'manager_bits':manager_bits(decoded.GraphValue.DocumentValue.FieldsValue),'grammar':grammar}

def audit():
 guard.active=True;data=decode_fragments(request['payloads']);config,resolved,_,_=readback(data);value=decode(request['owner_input']);grammar=inspect(value,config,resolved);wire=b64decode(request['definition_payload'],validate=True);definition=ReadModelDef(wire,19000);require(WriteModelDef(definition.GraphValue).OutputValue==wire,'independent source camera Definition wire changed');fields=definition.GraphValue.DocumentValue.FieldsValue;actual=ReadViewPair(fields['fae8'],fields['faf0']);require(actual==view(request['view_input']),'independent source camera input differs');require(ReadEmptyMgrs(definition.GraphValue)==managers(request['manager_input']),'independent empty manager semantic state differs');return {'fragments':identities(data),'definition':{'sha256':sha256(wire).hexdigest(),'bytes':len(wire)},'pair_bits':pair_bits(fields),'manager_bits':manager_bits(fields),'grammar':grammar,'round_trips':7}

try:
 result=source() if args.phase in ('source','source_base') else audit() if args.phase=='audit' else build();result.update(passed=True,phase=args.phase,denied_events=guard.denied,guarded_input_reads=0,heldout_inputs_read=0,native_processes=0,complete_source_preparation=False,new_complete_native_outputs=0,public_activation=False);code=0
except Exception as error:
 trace=[];tb=error.__traceback__
 while tb is not None:trace.append({'file':tb.tb_frame.f_code.co_filename.rsplit('/',1)[-1],'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno,'sdk_module':str(args.sdk/'src') in tb.tb_frame.f_code.co_filename});tb=tb.tb_next
 result={'passed':False,'phase':args.phase,'error_type':type(error).__name__,'error':str(error),'trace':trace,'denied_events':guard.denied};code=3
finally:guard.active=False;sys.setprofile(None)
print(json.dumps(result,sort_keys=True,allow_nan=False));raise SystemExit(code)
