from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct

from CollectDrawingViewSupportEvidence import Image, module, require

MODULES={"sldmodu.dll":"569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e","sldasmu.dll":"05ab90ee7380335088505c47202137c63dbce18d7d516e7fd6703aee31d70390"}


def word(image,address):
    return struct.unpack("<Q",image.bytes(address,address+8))[0]


def table(image,address,name,offsets):
    locator=word(image,address-8)
    signature,displacement,_,type_rva,_,self_rva=struct.unpack("<6I",image.bytes(locator,locator+24))
    require(signature==1 and displacement==0 and image.base+self_rva==locator and image.string(type_rva+16)==name,"the exact concentric RTTI changed")
    return {"va":hex(address),"rtti_locator_va":hex(locator),"rtti_class":name,"slots":{hex(offset):hex(word(image,address+offset)) for offset in offsets}}


def collect(directory):
    images={name:Image(directory/name) for name in MODULES}
    model,assembly=images["sldmodu.dll"],images["sldasmu.dll"]
    descriptor=0x4DAC9CA0
    name,packed,allocate,base_class=struct.unpack("<4Q",model.bytes(descriptor,descriptor+32))
    require(model.string(name-model.base)=="moMateConcentric" and packed==0x80000001000004F0 and allocate==0x4B653D80 and base_class==0x4B653B70,"concentric class allocation differs")
    model_table=table(model,0x4CFA8FB0,".?AVmoMateConcentric@@",(0,0x28,0x21F0,0x2258,0x22C8,0x23B0,0x23D0))
    command_table=table(assembly,0x3FC81270,".?AVuiAssemblyMateConcentricCmd_c@@",(0xB8,0x988))
    require(model_table["slots"]["0x28"]=="0x4b669080" and model_table["slots"]["0x23d0"]=="0x4bc5d920" and command_table["slots"]["0x988"]=="0x3f815a20","concentric dispatch differs")
    jump=struct.unpack("<25I",assembly.bytes(0x3F98AAC8,0x3F98AB2C))
    require(assembly.base+jump[1]==0x3F989AF2,"the exact API enum dispatch differs")
    routines={"sldmodu.dll":{"class_getter":0x4B6600B0,"allocator":allocate,"concrete_constructor":0x4BC2D720,"serializer":0x4B669080,"shared_two_geometry_serializer":0x4B668A60,"ordinary_factory":0x4BC42030,"ordinary_initializer":0x4BC5D920,"can_lock_rotation":0x4BC3D6D0,"misaligned_query":0x4BC353C0,"position_type_getter":0x4B28B0D0,"tolerance_check_getter":0x4B28B0C0,"tolerance_value_getter":0x4B2AC4D0,"current_tolerance_getter":0x4B2ABC40,"misaligned_dependent_getter":0x4B2AC3D0,"misaligned_parent_getter":0x4B2AC3E0},"sldasmu.dll":{"api_command_factory":0x3F989A10,"command_model_creation":0x3F815A20,"ordinary_command_runner":0x3F8267F0}}
    return {"schema":"kit.sw2026.concentric-native-source.v1","document_version":19000,"native_build":"34.5.2.0604","modules":{name:module(image,MODULES[name]) for name,image in images.items()},"runtime_class":{"va":hex(descriptor),"name":"moMateConcentric","object_bytes":packed&0xffffffff,"schema":hex(packed>>32),"allocator":hex(allocate),"base_class_getter":hex(base_class)},"model_vtable":model_table,"command_vtable":command_table,"api_enum_switch":{"va":"0x3f98aac8","api_value":1,"case_va":"0x3f989af2"},"archive_primitives":{hex(address):model.imports[address] for address in (0x4CD3D870,0x4CD3D880,0x4CD3D888,0x4CD3DA10,0x4CD3DA18)},"command_model_imports":{hex(address):assembly.imports[address] for address in (0x3FBECF80,0x3FBEA690)},"routines":{name:{role:images[name].function(address) for role,address in values.items()} for name,values in routines.items()},"serializer_rules":{"base_call_va":"0x4b6690ac","base_serializer":"0x4b668a60","ordinary_store":[{"member":"f4b8","type":"i32","store_call_va":"0x4b6690cb","load_version_minimum":6197,"meaning":"concentric-specific option; rotation-lock binding pending exact API/corpus correlation"},{"member":"f4c4","type":"i32","store_call_va":"0x4b6690da","load_version_minimum":9129,"meaning":"concentric position type"}],"conditional_misalignment":{"condition":"f4c4 != -1","fields":[["f4c8","i32"],["f4d0","f64"],["f4d8","f64"],["f4e0 feature ID or -1","i32"],["f4e8 feature ID or -1","i32"]],"reference_id_format_version_minimum":9224},"ordinary_constructor_position_type":-1,"ordinary_constructor_option":0,"additional_reference_and_tolerance_tail_omitted_when_position_is_minus_one":True},"construction_state":{"concrete_constructor_va":"0x4bc2d720","common_two_geometry_constructor_call_va":"0x4bc2d732","shared_model_initializer_slot":"0x23d0","shared_alignment_setter":"0x4b2cfe10","lock_rotation_eligible_is_not_lock_rotation_enabled":True},"limitations":["No native concentric source or generated writer acceptance exists at this handoff","The concentric option at f4b8 is not yet declared to be the API lock-rotation field","Cylinder-face versus datum-axis wrapper publication requires the new source corpus","Misaligned and linked concentric mates are outside the first ordinary coaxial scope","Function extents come from exact exception-directory fragments; leaf export samples remain explicit"],"native_processes_started":0,"heldout_inputs_read":0,"writer_output_count":0,"script_sha256":sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--binaries",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),"use a fresh numeric concentric receipt")
    result=collect(args.binaries.resolve(strict=True))
    data=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    args.output.write_bytes(data)
    print(json.dumps({"sha256":sha256(data).hexdigest(),"native_processes_started":0,"writer_output_count":0}))


if __name__=="__main__":
    main()
