import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--binaries',type=Path,required=True);parser.add_argument('--llvm',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();sys.path.insert(0,str(args.repo/'re/tooling/sw2026'))
from CollectDrawingViewSupportEvidence import Image
require=lambda value,message:None if value else (_ for _ in ()).throw(ValueError(message))
require(not args.output.exists(),'choose an unused evidence path')
images={name:Image(args.binaries/name) for name in ('slduiu.dll','sldmgu.dll')}
for name,wanted in (('slduiu.dll','025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7'),('sldmgu.dll','99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c')):
 image=images[name];require(sha256(image.data).hexdigest()==wanted and image.machine==0x8664,'pinned licensed image differs')
rows=[]
for name,module,start,end,alias,tokens in (
 ('document_orientation_getter','slduiu.dll',0x49787270,0x49787278,'?getDefaultViewXform@uiModelDoc_c@@',('0xae8(%rcx)','retq')),
 ('document_orientation_setter','slduiu.dll',0x48ee7f80,0x48ee7f8e,'?iSetDefaultViewXform@uiModelDoc_c@@',('0xae8(%rcx)','0x4a4718d8')),
 ('document_pan_zoom_getter','slduiu.dll',0x497871a0,0x497871a8,None,('0xaf0(%rcx)','retq')),
 ('transform_save','sldmgu.dll',0x31e03ce0,0x31e03d9a,'?save@mgXform_c@@',('0x31f205a0','0x31e039b0','0x58(%rbx)','0x70(%rbx)','0x78(%rbx)')),
 ('matrix_save','sldmgu.dll',0x31e039b0,0x31e03a12,'?save@mgMatrix_c@@',()),
 ):
 image=images[module]
 if alias is not None:require(any(x.startswith(alias) for x in image.exports.get(start,())),'exact native export alias differs')
 disassembly=subprocess.run([str(args.llvm),'-d','--no-show-raw-insn','--start-address='+hex(start),'--stop-address='+hex(end),str(image.path)],text=True,capture_output=True,check=True).stdout
 require(all(token in disassembly for token in tokens),'bounded instruction access changed')
 rows.append({'role':name,'module':module,'start':hex(start),'end_exclusive':hex(end),'code_sha256':sha256(image.bytes(start,end)).hexdigest(),'semantic_export_prefix':alias,'instruction_predicates_verified':list(tokens)})
ui=images['slduiu.dll'];assignment=ui.imports[0x4a4718d8];require(assignment=={'module':'sldmgu.dll','symbol':'??4mgXform_c@@QEAAAEBV0@AEBV0@@Z'},'native default-view setter no longer forwards assignment')
result={'schema':'kit.sw2026.throughall-view-native-rules.v1','modules':[{'name':name,'sha256':sha256(image.data).hexdigest(),'image_base':hex(image.base),'machine':hex(image.machine)} for name,image in images.items()],'bounded_ranges':rows,'full_native_functions':{'ui_model_serialize':ui.function(0x497011e0),'editable_initial_view_update':ui.function(0x493b4790),'splitter_view_restore':ui.function(0x497d68b0),'active_pan_zoom_setter':ui.function(0x498299c0)},'orientation_assignment_import':{'cell':'0x4a4718d8',**assignment},'rules':{'orientation':'separate document owner +0xae8; explicit orthonormal right-handed matrix in stored order, zero translation and unit scale in this profile','pan_zoom':'separate document owner +0xaf0; no matrix, explicit finite translation triple and positive scale, zero flags','wire':'ordinary legacy archive branch; presence byte, optional nine binary64 matrix entries, three binary64 translation entries, binary64 scale, flags, then optional perspective body; no perspective in admitted profile','read_boundary':'canonical representation only; no source matrix-presence normalization, source affine translation, reflection, shear or unknown transform fields','native_save_caveat':'save invokes iValidateRepairXForm before selecting legacy/msgpack storage and masks bit0 from stored flags; this component admits only validated rigid transforms with flags0, not the generic repair universe','window_state':'per-user splitters and window words are independently owned and remain unrepresented, not discarded or defaulted by source admission'},'existing_evidence':['re/solidworks/records/DefaultViewTransform2026.md','re/solidworks/measurements/2026/ViewProbeCorrelationA062.json','re/solidworks/measurements/2026/ViewHeldoutInspection01.json','re/solidworks/measurements/2026/ViewLoaderCallers01.json'],'tools':{'collector_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'image_reader_sha256':sha256((args.repo/'re/tooling/sw2026/CollectDrawingViewSupportEvidence.py').read_bytes()).hexdigest(),'llvm_sha256':sha256(args.llvm.read_bytes()).hexdigest(),'llvm_version':subprocess.run([str(args.llvm),'--version'],text=True,capture_output=True,check=True).stdout.splitlines()[0]},'static_only':True,'native_launches':0,'heldout_payload_reads':0,'persistent_analysis_target_opened':False,'vendor_bytes_or_listing_in_delivery':False}
args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'path':str(args.output),'sha256':sha256(args.output.read_bytes()).hexdigest()}))
