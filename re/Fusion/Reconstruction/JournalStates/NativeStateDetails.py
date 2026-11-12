import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess

base=Path(__file__).resolve().parent
binaries={name:Path('/tmp/kit-fusion-native-analysis')/filename for name,filename in (('kernel','libASMkern232.arm64.dylib'),('tagging','NaTagDefs10.arm64.dylib'))}

def disassemble(binary,start,stop):
    return subprocess.check_output(['/Library/Developer/CommandLineTools/usr/bin/llvm-objdump','--disassemble','--demangle',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(binary)],text=True)

def read_string(binary,address):
    payload=binary.read_bytes();position=32
    for index in range(struct.unpack_from('<I',payload,16)[0]):
        command,size=struct.unpack_from('<II',payload,position)
        if command==0x19:
            start,span,offset,length=struct.unpack_from('<4Q',payload,position+24)
            if start<=address<start+length:
                place=offset+address-start
                return payload[place:payload.index(b'\0',place)].decode('ascii')
        position+=size
    raise ValueError('Unmapped string')

code={
    'DELTA_STATE::tree_debug_node':disassemble(binaries['kernel'],0x16a028,0x16a0e8),
    'BULLETIN_BOARD::tree_debug_node':disassemble(binaries['kernel'],0x16a0e8,0x16a1f0),
    'TaggingInterface::tracked_tag_id':disassemble(binaries['tagging'],0x12914,0x12a68),
    'TaggingInterface::FPM_tracked_attrib_def':disassemble(binaries['tagging'],0x12a68,0x12c08),
    'TaggingInterface::tracked_attrib_def_savres':disassemble(binaries['tagging'],0x13130,0x1320c),
}
encoded=lzma.compress(json.dumps(code,indent=2).encode())
(base/'NativeStateDetails.json.xz').write_bytes(encoded)
stubs=subprocess.check_output(['/Library/Developer/CommandLineTools/usr/bin/llvm-objdump','--macho','--indirect-symbols',str(binaries['tagging'])],text=True)
report={
    'schema':'FusionDeltaAndTrackedAttributeSemantics/1',
    'scope':'Static symbols, instructions, import table and string literals; no native execution',
    'binaries':{name:{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for name,path in binaries.items()},
    'disassembly':{'path':'NativeStateDetails.json.xz','sha256':hashlib.sha256(encoded).hexdigest()},
    'deltaFields':[
        {'name':'rollsBack','offset':'0x14','instruction':'0x16a08c ldrb w8, [x20,#0x14]','meaning':'native debug calls the same flag backward in DELTA_STATE::debug'},
        {'name':'hidden','offset':'0x15','instruction':'0x16a090 ldrb w9, [x20,#0x15]','proofStringAddress':'0xab5d43'},
        {'name':'partnerNode','offset':'0x30','instruction':'0x16a0a8 ldr x8, [x20,#0x30]','proofStringAddress':'0xab5d64'},
        {'name':'mergedWithNode','offset':'0x50','instruction':'0x16a0b4 ldr x9, [x20,#0x50]','proofStringAddress':'0xab5d64'},
    ],
    'nativeDebugStrings':{hex(address):read_string(binaries['kernel'],address) for address in (0xab5d0f,0xab5d43,0xab5d64,0xab5de9)},
    'boardEnumBound':'BULLETIN_BOARD::tree_debug_node compares signed status at +0x50 with 3 at 0x16a154..0x16a15c before its four-name lookup',
    'trackedAttribute':{
        'family':'FPM_tracked_attrib_def','qualifiedSchema':1,'payloadFields':[{'name':'trackedTagId','nativeType':'TaggingInterface::tracked_tag_id containing signed int','tagObjectOffset':'0x8','attributeObjectOffset':'0x18','saveInstructions':['0x12b84 loads w1 from attribute+0x18','0x12b8c calls save_context::write_int(int)'],'restoreInstructions':['0x12bb0 calls restore_context::read_int()','0x12bb4 stores w0 to attribute+0x18']}],
        'constructor':'0x12ac8 copies tracked_tag_id+0x8 into attribute+0x18; no-payload constructor initializes -1',
        'comparison':'tracked_tag_id::operator< at 0x1293c uses signed lt comparison',
        'qualifiedControlJoin':'Both Draft and offset-cylinder archived attributes use 271; their Design entity 271 is BrepRefMetaType owned by feature267, with rRecipe274. This is a verified source-specific identity match, not proof of a universal allocation rule.',
        'debugPrefix':read_string(binaries['tagging'],0x1454d),
        'importStubs':[line for line in stubs.splitlines() if any(address in line for address in ('00000000000134ac','00000000000134f4','00000000000134e8','00000000000133ec'))],
    },
    'qualification':'Observed journals are linear, backward=true, hidden=false, mergedWith=null, optionalName absent and stateList48 empty; nonempty stateList48 semantics and branched/merged execution remain unqualified',
}
(base/'NativeStateDetails.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ('nativeDebugStrings','boardEnumBound')},indent=2))
