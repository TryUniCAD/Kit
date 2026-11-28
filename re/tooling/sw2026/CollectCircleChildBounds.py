from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json,struct


def main():
    parser=argparse.ArgumentParser()
    for name in ('support','binaries','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert sha256(args.support.read_bytes()).hexdigest()=='55edce424c2359f7b126f8cfa72516ae6b7924b404e3bef2b67a5746c3398b8d'
    spec=importlib.util.spec_from_file_location('circle_bbox_pe',args.support);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    images={name:module.Image(args.binaries/name) for name in ('sldmodu.dll','sldmgu.dll','sldgcu.dll','sldgciParau.dll')}
    modules={name:{'sha256':sha256(image.data).hexdigest(),'bytes':len(image.data),'image_base':hex(image.base)} for name,image in images.items()}
    assert modules['sldmodu.dll']['sha256']=='569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e'
    assert modules['sldmgu.dll']['sha256']=='99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c'
    assert modules['sldgcu.dll']['sha256']=='77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594'
    assert modules['sldgciParau.dll']['sha256']=='96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce'
    table=0x4d1252d8;model=images['sldmodu.dll'];assert struct.unpack('<Q',model.bytes(table+0x1350,table+0x1358))[0]==0x4b57a7e0
    routines=[('part_box_wrapper','sldmodu.dll',0x4b57a7e0,0x4b57a82c),('model_box','sldmodu.dll',0x4b581040,0x4b581568),('body_box_thunk','sldgcu.dll',0x4388ecd0,0x4388ecd5),('body_box_dispatch','sldgcu.dll',0x43e816e0,0x43e8170e),('backend_body_box','sldgciParau.dll',0x32f80ef0,0x32f80f08),('backend_topology_box','sldgciParau.dll',0x33096440,0x33096501),('array_box','sldmgu.dll',0x31de8760,0x31de87e7),('point_pair_setter','sldmgu.dll',0x31de85b0,0x31de868a),('sphere_getter','sldmgu.dll',0x31de53f0,0x31de563c)]
    functions=[{'role':role,'module':name,'start_va':hex(start),'end_va_exclusive':hex(end),'code_sha256':sha256(images[name].bytes(start,end)).hexdigest()} for role,name,start,end in routines]
    edges=[]
    for name,site,target,kind in [('sldmodu.dll',0x4b57a827,0x4b581040,'jump'),('sldgcu.dll',0x4388ecd0,0x43e816e0,'jump'),('sldgciParau.dll',0x32f80ef4,0x33096440,'call'),('sldmgu.dll',0x31de87ad,0x31de85b0,'call')]:
        data=images[name].bytes(site,site+5);assert data[0]==(0xe8 if kind=='call' else 0xe9) and site+5+struct.unpack('<i',data[1:])[0]==target;edges.append({'module':name,'site_va':hex(site),'target_va':hex(target),'kind':kind})
    imports=[]
    for name,site,iat,symbol in [('sldmodu.dll',0x4b5811f4,0x4cd3a6a8,'?isSet@mgBBox_c@@QEBAHXZ'),('sldmodu.dll',0x4b58120c,0x4cd3a6e8,'??_5mgBBox_c@@QEAAAEAV0@AEBV0@@Z'),('sldmodu.dll',0x4b581321,0x4cd38778,'?getBBox@gcBody_w@@QEAAHPEAVmgBBox_c@@@Z'),('sldgcu.dll',0x43e81707,0x43f5a1a0,'?getBBox@gciBody_w@GCP@@QEAAHPEAVmgBBox_c@@@Z'),('sldgciParau.dll',0x330964d2,0x330b62b0,'?set@mgBBox_c@@QEAAXQEAN@Z')]:
        image=images[name];prefix=int(image.bytes(site,site+1)==b'\x48');size=6+prefix;data=image.bytes(site,site+size);assert data[prefix:prefix+2] in (b'\xff\x15',b'\xff\x25') and site+size+struct.unpack('<i',data[prefix+2:])[0]==iat;assert image.imports[iat]['symbol']==symbol;imports.append({'module':name,'site_va':hex(site),'iat_va':hex(iat),'import':image.imports[iat],'instruction_bytes':size})
    result={'schema':'kit.sw2026.circle-child-bounds-native.v1','modules':modules,'functions':functions,'direct_edges':edges,'imports':imports,'part_bbox_virtual_slot':'0x1350','part_bbox_vtable':hex(table),'cache_member':'0x7f8','sphere_rule':'point-pair midpoint and half-diagonal; preserve all ten cache words when copying an existing box','kernel_extrema_arithmetic_is_fully_traced':False,'native_processes':0,'hidden_inputs_read':0,'hopper_sessions_opened':0,'support_sha256':sha256(args.support.read_bytes()).hexdigest(),'tool_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
    assert not args.output.exists();args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
