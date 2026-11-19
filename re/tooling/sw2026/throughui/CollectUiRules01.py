import argparse
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from
import subprocess
import sys

parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--binaries',type=Path,required=True);parser.add_argument('--llvm',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(args.repo/'re/tooling/sw2026'));sys.path.insert(0,str(args.repo/'re/tooling/sw2026/freecad_cylinder'))
from CollectDrawingViewSupportEvidence import Image
from NativeNamePe import NativeNamePe,require

require(not args.output.exists(),'choose an unused scalar source receipt')
pins={'slduiu.dll':'025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7','sldappu.dll':'50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf','sldprtu.dll':'54c079c8bbbe13582d062787c07a13f91d91f2d7972715e5d647bb8a1802d494','sldmgu.dll':'99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c'};images={name:Image(args.binaries/name) for name in pins}
for name,image in images.items():require(sha256(image.data).hexdigest()==pins[name] and image.machine==0x8664,'pinned original module differs '+name)
ui=images['slduiu.dll'];app=images['sldappu.dll'];part=images['sldprtu.dll'];geometry=images['sldmgu.dll'];res=NativeNamePe((args.binaries/'sldresu.dll').read_bytes());require(res.sha256=='531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111','pinned original English vocabulary differs');rows=[]
for role,image,start,end,prefix,tokens in (
 ('quality_named_getter',app,0x456fa890,0x456fa897,'?hlrDisplayQuality@uiBaseView_c@@',('0x170(', 'retq')),
 ('quality_named_setter',app,0x459a1270,0x459a1297,'?setHlrDisplayQuality@uiBaseView_c@@',('0x228(', '0x170(', '0x174(', '0xffff')),
 ('quality_and_display_capture',ui,0x49701416,0x4970143e,None,('0x493b5c80','0x148(', '0xacc(', '0x170(', '0xad0(')),
 ('quality_grid_store',ui,0x4970146e,0x4970148e,None,('0xad0(', '0xad4(', '0x4a474590', '0x4a4740e8')),
 ('constructor_grid_mask',ui,0x49748c3c,0x49748c46,None,('0x3, 0xad4(',)),
 ('grid_getter',ui,0x497872b0,0x497872d1,'?getDisplayGrid@uiModelDoc_c@@',('0xad4(', '0x1, %eax')),
 ('grid_setter',ui,0x497b9280,0x497b929f,'?setDisplayGrid@uiModelDoc_c@@',('0xad4(', '0x1,', '-0x2')),
 ('default_context_getter',ui,0x49786f80,0x49787040,'?getDefaultContextMode@uiModelDoc_c@@',('0x12c8(', '0xb00(', '0xb04(', '0xb08(', '0x8c8(')),
 ('default_context_setter',ui,0x497b9060,0x497b9132,'?setDefaultContextMode@uiModelDoc_c@@',('0x12c8(', '0xb00(', '0xb04(', '0xb08(', '0x8d0(')),
 ('context_before_store_confirmation',ui,0x497018d7,0x4970191a,None,('0xb00(', '0xb04(', '0x2ed0(', '0x4a474590')),
 ('context_after_load_confirmation',ui,0x49703390,0x497033da,None,('0xb00(', '0xb04(', '0x2ed0(', '0x4a474578')),
 ('part_context_confirmation',part,0x3338bcd0,0x3338bce3,'?iConfirmDocContextModes@uiPartDoc_c@@',('0x1, (%rdx)', '0x0, (%r8)')),
 ('part_constructor_primary',part,0x3337498c,0x333749a0,None,('0x3346f4d0','0x3349e068','(%rdi)')),
 ('environment_store_capture_and_count',ui,0x4970166b,0x497017a0,None,('0xaf8(', '0x49781340','0x698(', '0x3d0(', '0x497d5740','0x497d62f0','0x4a471648','0x497d5950')),
 ('environment_read_count_and_objects',ui,0x497029e0,0x49702a52,None,('0x4a474578','0x49702bcc','0xaf8(', '0x497d58d0')),
 ('environment_load_null_duplicate_filter',ui,0x49702b64,0x49702bb6,None,('0x49781340','0x497d6bc0','0x8(%rax)')),
 ('dynamic_array_count',geometry,0x31deec50,0x31deec54,'amDynamicArrayCount',('-0x10(%rcx)', 'retq')),
 ('toolbar_group_dispatch',ui,0x497c326e,0x497c3296,None,('0x88(%rsp)','0x80(%rsp)','0x4a4679f0')),
 ):
 if prefix:require(any(name.startswith(prefix) for name in image.exports.get(start,())),'semantic export differs '+role)
 listing=subprocess.run([str(args.llvm),'-d','--no-show-raw-insn','--start-address='+hex(start),'--stop-address='+hex(end),str(image.path)],capture_output=True,text=True,check=True).stdout;require(all(token in listing for token in tokens),'source operands differ '+role);rows.append({'role':role,'module':image.path.name,'start':hex(start),'end_exclusive':hex(end),'bytes':end-start,'sha256':sha256(image.bytes(start,end)).hexdigest(),'semantic_export_prefix':prefix,'operand_facts':list(tokens)})
vtable=0x3349e068;bindings={}
for role,slot in (('is_opened_hidden',0x698),('is_editing_self',0x12c8),('confirm_context',0x2ed0)):
 target=unpack_from('<Q',part.data,part.offset(vtable+slot-part.base))[0];entry={'slot':hex(slot),'cell':hex(vtable+slot),'target':hex(target)}
 if role!='confirm_context':
  raw=part.bytes(target,target+6);require(raw[:2]==bytes((255,37)),'part context thunk differs');cell=target+6+unpack_from('<i',raw,2)[0];entry.update(import_cell=hex(cell),imported=part.imports[cell])
 bindings[role]=entry
require(bindings['confirm_context']['target']=='0x3338bcd0' and bindings['is_opened_hidden']['imported']['symbol']=='?isOpenedHidden@uiBaseDoc_c@@UEBAHXZ' and bindings['is_editing_self']['imported']['symbol']=='?isEditingSelf@uiModelDoc_c@@UEAAHXZ','selected part virtual owners differ')
col=unpack_from('<Q',part.data,part.offset(vtable-8-part.base))[0];typedesc=part.base+unpack_from('<I',part.data,part.offset(col-part.base)+12)[0];rtti=part.string(typedesc-part.base+16);require(rtti=='.?AVuiPartDoc_c@@','part primary class differs')
imports={hex(address):ui.imports[address] for address in (0x4a471648,0x4a471650,0x4a4679f0,0x4a446000,0x4a45fab0,0x4a465618,0x4a465610)};require(imports['0x4a471648']['symbol']=='amDynamicArrayCount' and imports['0x4a446000']['symbol']=='GetUserNameW' and imports['0x4a4679f0']['symbol']=='?setContextToolbarMode@uiToolBarManager_c@@QEAAHHW4swContextType_e@@HHH@Z','count or group import differs')
vocabulary={}
for number,wanted in ((38283,'Drawing commands\nDrawings'),(38284,'Feature commands\nFeatures')):
 values=res.resource(number);require(len(values)==1 and values[0]['language_id']==1033 and values[0]['value']==wanted,'exact command group resource differs');vocabulary[str(number)]=values[0]
full={role:{'module':image.path.name,**image.function(address)} for role,image,address in (('model_ui_serializer',ui,0x497011e0),('get_default_context',ui,0x49786f80),('set_default_context',ui,0x497b9060),('is_editing_self',ui,0x497a47f0),('update_context_toolbar',ui,0x497c30b0),('toolbar_manager_set_context',app,0x45b82730),('find_user_environment',ui,0x49781340),('environment_constructor',ui,0x497d5740),('environment_serializer',ui,0x497d5ee0),('splitter_constructor',ui,0x497d5600),('splitter_serializer',ui,0x497d5b00))}
result={'schema':'kit.sw2026.part-ui-scalar-and-environment-count-rules.v1','modules':[{'name':name,'sha256':pins[name],'bytes':len(image.data),'base':hex(image.base),'machine':hex(image.machine)} for name,image in images.items()]+[{'name':'sldresu.dll','sha256':res.sha256,'bytes':len(res.data),'base':hex(res.base),'machine':hex(res.machine)}],'bounded_ranges':rows,'complete_functions':full,'part_primary':{'address':hex(vtable),'rtti':rtti,'constructor':'0x33374980','virtual_bindings':bindings},'imports':imports,'command_group_vocabulary':vocabulary,'rules':{'fad0':'Persisted u16 of active Brep view uiBaseView+0x170, named hlrDisplayQualityType; ordinary source component only admits codes0/1 with facc3. Setter caches old quality at+174, is disabled by a nonzero+228 lock, and maps sentinel65535 to0. Other domains and live lock state are not generated.','fad4':'UI constructor stores3. Named document getter reads bit0 after actual-sketch callback, setter changes bit0 only. The source component derives2|int(DisplayGrid) and refuses all other bits. This reuses the existing drawing toggle owner; it does not transfer drawing-specific annotation-mask merges.','fb00_fb04':'Native default-context type and command group occupy UI runtime+b00/+b04; third flags argument+b08 has no adjacent wire field. Named getter/setter return/store these only in isEditingSelf context, otherwise delegate through edit-target ModelContext.Document. Current serialize copies the first two to locals, invokes virtual+2ed0, and emits low u16 words. Current load zero-extends words then invokes the same validator. The actual part validator makes type1 and group0 whenever the supplied type is not1; type1 preserves group.','command_group':'Typed features selection uses exact resourceID38284 from the unrelated installed Feature commands vocabulary and the named toolbar context owner. Zero is the explicit cleared/unspecified group, independently written by the part validator. Drawing group38283 and other groups remain outside this component.','nenv':'Not a Boolean presence word. Store creates an empty array wrapper if missing, then searches current-user environment. When actual isOpenedHidden is false and document+3d0 equals0, it creates a new environment plus captures settings or updates the existing entry. It then emits zero for null buffer or low u16 of amDynamicArrayCount(buffer), followed by that many typed objects. The helper reads signed32 count at buffer-16. Current read consumes the declared u16 loop. Nulls and duplicate environment names can be filtered before live insertion, with additional path-dependent compatibility handling; raw typed readback does not execute these UI changes.','environment_bound':'These plain part environments have both f10 and fe0 splitters. The drawing context omits f10 through its separate context predicates. Count/class audit does not construct or declare the actual window/splitter geometry disposable. Two source window frontiers remain open.'},'source_component_fields':['fad0','fad4','fb00','fb04'],'environment_construction':False,'complete_source_preparation':False,'public_activation':False,'native_acceptance':False,'native_processes':0,'heldout_inputs_read':0,'persistent_analysis_target_opened':False,'vendor_bytes_or_listing_in_delivery':False,'tools':{'collector_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'llvm_sha256':sha256(args.llvm.read_bytes()).hexdigest(),'dependencies':{str(p.relative_to(args.repo)):sha256(p.read_bytes()).hexdigest() for p in (args.repo/'re/tooling/sw2026/CollectDrawingViewSupportEvidence.py',args.repo/'re/tooling/sw2026/freecad_cylinder/NativeNamePe.py')}}}
args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest(),'bounded_ranges':len(rows)}))
