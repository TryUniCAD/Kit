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
from PinCylinderNameResource import x64_target,arm_iat,arm_load_slot,window

require(not args.output.exists(),'choose an unused native-rule receipt')
ui=Image(args.binaries/'slduiu.dll');mfc=Image(args.binaries/'sldmfcu.dll');raw_mfc=NativeNamePe((args.binaries/'mfc140u.dll').read_bytes())
pins=((ui,'025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7'),(mfc,'af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735'))
for image,wanted in pins:require(sha256(image.data).hexdigest()==wanted and image.machine==0x8664,'original x64 source module differs')
require(raw_mfc.sha256=='88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1','original ARM64X MFC differs')
view,hybrid=raw_mfc.hybrid();require(view.sha256=='364d5bb2e7c7cb62bb8987047e71c848de3c8967a4d3b93bcf6611550fe0895f' and hybrid['fixups']==1735,'declared AMD64 view differs')
ranges=[]
for role,image,start,end,prefix,tokens in (
 ('named_pattern_constructor',mfc,0x3c870290,0x3c8702ff,'??0moLineStyle_c@@QEAA@PEB_W0@Z',('0x20(', '0x28(', '0x3c870950')),
 ('empty_pattern_constructor',mfc,0x3c870300,0x3c87035c,'??0moLineStyle_c@@QEAA@XZ',('0x20(', '0x28(', '0x3c870950')),
 ('append_signed_segment',mfc,0x3c870470,0x3c8704a9,'?addSegment@moLineStyle_c@@',('0x18(', '0x28(', '0x3cb24aa0')),
 ('clear_pattern_segments',mfc,0x3c8709a0,0x3c8709eb,'?initSegment@moLineStyle_c@@',('0x18(', '0x20(', '0x28(')),
 ('enable_thick_thin',mfc,0x3c7fa960,0x3c7fa968,'?setThickThin@moLineStyle_c@@',('0x20(',)),
 ('font_explicit_constructor',mfc,0x3c848610,0x3c848680,'??0uiLFConfig_c@@QEAA@AEBV',('0x18(', '0x1c(')),
 ('font_copy_or_null_constructor',mfc,0x3c848680,0x3c8486fd,'??0uiLFConfig_c@@QEAA@PEAV0@@Z',('0x18(%rdi)', 'movq', '0x3c84a8f0')),
 ('preset_width_constructor',mfc,0x3c84a8f0,0x3c84a904,'??0utLineWidth_c@@QEAA@W4swLineWeights_e@@@Z',('0xbf800000','0x6(')),
 ('unselected_width_constructor',mfc,0x3c84a910,0x3c84a921,'??0utLineWidth_c@@QEAA@XZ',('0xbf800000','0xffff')),
 ('font_end_cap_getter',mfc,0x3c74f9d0,0x3c74f9d4,'?getEndCap@uiLFConfig_c@@',('0x18(',)),
 ('font_end_cap_setter',mfc,0x3c7a5970,0x3c7a5974,'?setEndCap@uiLFConfig_c@@',('0x18(',)),
 ('font_runtime_emphasis_getter',mfc,0x3c74f9f0,0x3c74f9f4,'?isEmphasizedOutline@uiLFConfig_c@@',('0x1c(',)),
 ('ordered_style_prefix_lookup',mfc,0x3c849620,0x3c8496cc,'?getLineIndex@apLineStyleMgr_c@@',('0x3cb19c60','0xffffffff')),
 ('category_copy_ownership',ui,0x49d4bf50,0x49d4c007,'?setLineFont@uiLineFontMgr_c@@',('0x10, %rcx','0x20, %ecx','0x4a449bd8','0x4a447b50','0x48(')),
 ('manager_factory',ui,0x49ce4d20,0x49ce4d4e,None,('0x80','0x49d4b640')),
 ('manager_constructor',ui,0x49d4b640,0x49d4b6ae,None,('0x4a773008','0x10(','0x48(','0x4a3215e1')),
 ('current_manager_store',ui,0x49ce4e30,0x49ce4f44,None,('0x4a460c80','0x4a5d3028','0x4a32176d')),
 ):
 if prefix:require(any(name.startswith(prefix) for name in image.exports.get(start,())),'semantic export alias differs '+role)
 listing=subprocess.run([str(args.llvm),'-d','--no-show-raw-insn','--start-address='+hex(start),'--stop-address='+hex(end),str(image.path)],check=True,capture_output=True,text=True).stdout
 require(all(token in listing for token in tokens),'native operands differ '+role)
 ranges.append({'role':role,'module':image.path.name,'start':hex(start),'end_exclusive':hex(end),'bytes':end-start,'sha256':sha256(image.bytes(start,end)).hexdigest(),'semantic_export_prefix':prefix,'operand_facts':list(tokens)})
require(ui.imports[0x4a449bd8]['symbol']=='??0uiLFConfig_c@@QEAA@PEAV0@@Z' and ui.imports[0x4a447b50]['symbol']=='?copy@uiLFConfig_c@@QEAAXAEAV1@@Z' and ui.imports[0x4a460c80]=={'module':'mfc140u.dll','symbol':'#4511'},'UI binding import differs')
require(mfc.imports[0x3cb19c60]['symbol']=='_wcsnicmp','style prefix comparator differs')
ui_map_imports={}
for role,address,ordinal in (('constructor',0x4a3215e1,542),('lookup',0x4a320a8f,8205),('subscript',0x4a320a95,1636),('walk',0x4a32176d,5960)):
 code=ui.bytes(address,address+6);require(code[:2]==bytes((255,37)),'UI selected map thunk differs');slot=address+6+unpack_from('<i',code,2)[0];entry=ui.imports[slot];require(entry=={'module':'mfc140u.dll','symbol':'#'+str(ordinal)},'UI map ordinal route differs');ui_map_imports[role]={'thunk':hex(address),'slot':hex(slot),**entry}
require(unpack_from('<Q',ui.data,ui.offset(0x4a773008+0x28-ui.base))[0]==0x49ce4de0,'font manager serializer slot differs')
descriptor=ui.bytes(0x4aef4b78,0x4aef4ba8);require(unpack_from('<IIQ',descriptor,8)==(128,0x80000001,0x49ce4d20),'font runtime descriptor differs')
ordinals={}
for number,body,high,expected in (
 (4511,0x1803b12b0,0x1803b130c,'7096b0161306c0da304dd7140e921b72aed6adfd731adcdbc8d2a89c7507f003'),
 (8205,0x1805cbd40,0x1805cbd88,'60527ebb06948406288f96832ab76879c18c889570cfeb6f0d414f3bf4cd0007'),
 (1636,0x1805cbde0,0x1805cbe90,'082be27123d92e1625651fdc7f9b403d39d0707cd04d9a0d90a379be0a3b060c'),
 (5960,0x1805cbfc0,0x1805cc088,'9d7a31afd929d59fb1ad09d05d4000d10fcbffcb67603b250a7447e9c5f006af'),
 (542,0x1805cc2b0,0x1805cc2dc,None),
 ):
  entry=view.ordinal(number);require(x64_target(view,int(entry['address'],16))==body,'effective MFC ordinal owner differs');span=window(raw_mfc,view,body,high)
  if expected:require(span['sha256']==expected,'effective MFC source body differs')
  ordinals[str(number)]={'raw_export':raw_mfc.ordinal(number),'effective_export':entry,'arm64ec_body':hex(body),'bounded_source':span}
load_config=view.offset(unpack_from('<I',view.data,view.optional+112+10*8)[0]);chpe=unpack_from('<Q',view.data,load_config+0xc8)[0]-view.base;aux=unpack_from('<I',view.data,view.offset(chpe)+0x2c)[0];normal=unpack_from('<I',view.data,view.optional+112+12*8)[0];imports=view.imports();bound={}
for name,address in (('star_search',0x1803383e8),('wide_length',0x180338478),('key_equality',0x1803384b4)):
 slot=arm_iat(view,address);ordinary=slot-aux+normal;exit_target=unpack_from('<Q',view.data,view.offset(slot-view.base,8))[0];require(arm_load_slot(view,exit_target)==ordinary,'ARM64EC auxiliary exit import differs');bound[name]={'thunk':hex(address),'auxiliary_slot':hex(slot),'normal_slot':hex(ordinary),'import':imports[ordinary]}
require({k:v['import']['name'] for k,v in bound.items()}=={'star_search':'wcsstr','wide_length':'wcslen','key_equality':'wcscmp'},'map string primitive differs')
constant_values=unpack_from('<III',view.data,view.offset(0x5cbd30,12));require(constant_values==(0x811c9dc5,0xcccccccd,0x1000193),'sampled FNV constants differ')
require(ui.bytes(0x4a5d3028,0x4a5d302c).decode('utf-16-le')=='*\0','persistent exclusion text differs')
result={'schema':'kit.sw2026.line-presentation-construction-rules.v1','static_only':True,'modules':[{'name':image.path.name,'sha256':sha256(image.data).hexdigest(),'bytes':len(image.data),'base':hex(image.base),'machine':hex(image.machine)} for image,_ in pins]+[{'name':'mfc140u.dll','sha256':raw_mfc.sha256,'bytes':len(raw_mfc.data),'base':hex(raw_mfc.base),'machine':hex(raw_mfc.machine)}],'mfc_effective_view':hybrid,'bounded_ranges':ranges,'full_serializer':ui.function(0x49ce4de0),'manager_runtime':{'class':'uiLineFontMgr_c','schema':1,'size':128,'descriptor':'0x4aef4b78','primary':'0x4a773008','serializer_slot':'0x28','factory':'0x49ce4d20','constructor':'0x49d4b640'},'map_ordinals':ordinals,'ui_map_imports':ui_map_imports,'map_numeric_stores':{'initial_bucket_count':17,'count_value_site':'0x1805cc2c0','count_member_store_site':'0x1805cc2c8','count_member_offset':'0x10','allocation_block_count_default':10,'allocation_default_site':'0x1805cc2cc','allocation_count_member_offset':'0x30','first_bucket_site':'0x1805cbff4','chain_next_site':'0x1805cc014','next_bucket_remainder_site':'0x1805cc030','sampled_hash_load_site':'0x1805cbc90','multiply_site':'0x1805cbc94','xor_site':'0x1805cbca0'},'map_lookup_range':window(raw_mfc,view,0x1805cbc30,0x1805cbd3c),'map_insertion_range':window(raw_mfc,view,0x1805cbe60,0x1805cbe78),'wide_imports':bound,'hash':{'unit':'unsigned UTF16 code unit','initial':constant_values[0],'multiplier':constant_values[2],'stride':'floor(utf16_unit_count / 10)+1','stride_multiplier':constant_values[1],'stride_shift':35,'update':'((hash * multiplier) xor unit) mod 2**32','bucket_count':17,'insert':'prepend new unique key to selected bucket chain','walk':'bucket indices ascending, each chain head to next','equality':'case-sensitive wcscmp','source_inverse':'reverse compatible transmitted rows, then recompute hash, bucket and head insertion; reject if walk differs'},'rules':{'style':'named constructor owns explicit strings and empty segments; addSegment preserves each signed f64 and increments runtime period by absolute magnitude; setThickThin sets f20=1; runtime period+0x28 is not serialized','font':'each category creates a distinct uiLFConfig copy even for the same font name; explicit input selects preset width, named font and endcap; emphasis+0x1c and width print cache+0x04 are not wire fields','font_width':'preset constructor initializes f00=-1 and explicit f06; custom width mode remains outside this component','font_store_filter':'both count and write passes skip keys containing wide star, so this persistent component refuses them instead of losing categories','style_lookup':'ordered case-insensitive prefix lookup by UTF16 query length, may return -1; serialized font name is independent of an object link or local-row existence','count_widths':'font count u16, styles signed32, segments u16; counts derive from actual constructed collections'},'construction_scope':{'version':19000,'schema':1,'parts_only':True,'preset_weights':[0,1,2],'endcaps':[0,2],'patterns':'finite signed doubles with positive finite absolute period; immutable authored order','categories':'nonempty valid UTF16 without NUL or star; distinct case-sensitive keys','native_execution':False,'full_source_admission':False},'limits':['custom physical-width units and additional weight/endcap modes remain unqualified','wider renderer/global resolution of names missing from local catalog remains separate','constructor-compatible inverse map order preserves this wire representation without claiming original call chronology','no per-case row/default table, runtime source file read or native launch in construction','runtime reset/load normalization is separate from this complete typed component','full through-all original and public acceptance gates remain closed'],'tool_hashes':{str(path.relative_to(args.repo)):sha256(path.read_bytes()).hexdigest() for path in (args.repo/'re/tooling/sw2026/CollectDrawingViewSupportEvidence.py',args.repo/'re/tooling/sw2026/freecad_cylinder/NativeNamePe.py',args.repo/'re/tooling/sw2026/freecad_cylinder/PinCylinderNameResource.py')},'collector_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'llvm_sha256':sha256(args.llvm.read_bytes()).hexdigest(),'native_processes':0,'heldout_inputs_read':0,'persistent_analysis_target_opened':False,'vendor_bytes_or_listing_in_delivery':False}
args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest(),'bounded_ranges':len(ranges)}))
