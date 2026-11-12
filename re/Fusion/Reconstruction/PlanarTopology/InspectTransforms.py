import collections
import hashlib
import json
import lzma
from pathlib import Path
import runpy
import struct
import subprocess
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
READ=runpy.run_path(str(ROOT/'re/Fusion/Reconstruction/BrepTokens.py'))['read_stream']
DECODE=runpy.run_path(str(OUT/'InspectControls.py'))['decode']
DATA=json.loads(lzma.decompress((ROOT/'re/Fusion/Reconstruction/BrepCoverage/Inventory.json.xz').read_bytes()))
BIN=Path('/tmp/kit-fusion-native-analysis/libASMkern232.arm64.dylib')
BASE=BIN.with_name('libASMbase232.arm64.dylib')
OBJ='/Library/Developer/CommandLineTools/usr/bin/llvm-objdump'


def text_at(binary,address):
    data=binary.read_bytes();offset=32
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size=struct.unpack_from('<II',data,offset)
        if command==0x19:
            start,span,place,length=struct.unpack_from('<4Q',data,offset+24)
            if start<=address<start+length:
                where=place+address-start
                return data[where:data.index(b'\0',where)].decode('ascii')
        offset+=size
    raise ValueError('Unmapped native literal')


def main():
    seen=set();records=[];signatures=collections.Counter()
    for member in DATA['members']:
        digest=member['sha256']
        if digest in seen or 'transform' not in DATA['uniqueBlobs'][digest]['recordTypes']:continue
        seen.add(digest)
        with ZipFile(ROOT/member['path']) as archive: parsed=READ(archive.read(member['member']))
        for index,record in enumerate(parsed['records']):
            if record['name']!='transform':continue
            semantic=DECODE(record)['fields'];signature=tuple(field['tag'] for field in record['fields']);signatures[str(signature)]+=1
            records.append(dict(source=member,recordOrdinal=index,fields=semantic))
    packed=lzma.compress(json.dumps(records,separators=(',',':')).encode());(OUT/'Transforms.json.xz').write_bytes(packed)
    code={name:subprocess.check_output([OBJ,'--disassemble','--demangle',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(binary)],text=True) for name,binary,start,stop in (('TRANSFORM::save_common',BIN,0x193b9c,0x193c58),('write_matrix/write_transf',BIN,0x53fd4c,0x53fe88),('read_transf',BIN,0x5403e8,0x5404bc),('position_times_transform',BASE,0xa4e34,0xa4ebc),('position_times_matrix',BASE,0x9ee58,0x9eeac))}
    binary=lzma.compress(json.dumps(code).encode());(OUT/'TransformDisassembly.json.xz').write_bytes(binary)
    report=dict(schema='FusionTransformSemantics/1',scope='Static native serializer/restorer/operator proof plus read-only complete transform field decoding; no CAD runtime or production execution',records=len(records),distinctSourceBlobs=len(seen),fieldTagSignatures=dict(signatures),detailsSha256=hashlib.sha256(packed).hexdigest(),disassemblySha256=hashlib.sha256(binary).hexdigest(),binaries={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (BIN,BASE)},nativeLabels={hex(address):text_at(BIN,address) for address in (0xac410c,0xac4116,0xac411d,0xac4128,0xac4130,0xac4139)},flagCombinations=dict(collections.Counter(str((row['fields']['rotation'],row['fields']['reflection'],row['fields']['shear'])) for row in records)),scales=dict(collections.Counter(str(row['fields']['scale']) for row in records)),fields=['attributeRef','entityTag','columnX','columnY','columnZ','translationCm','scale','rotation','reflection','shear'],mapping='world = scale * (x*columnX + y*columnY + z*columnZ) + translationCm',proof='TRANSFORM::save_common writes ENTITY base then write_transf. write_matrix serializes three contiguous vectors; native position*matrix multiplies input x/y/z by those vectors; position*transf multiplies result by offset0 scalar then adds offset0x50 translation. Explicit flag labels are rotation, reflection, shear; preserve independently.',nonidentityExamples=[row for row in records if row['fields']['translationCm'] != [0.0,0.0,0.0] or row['fields']['rotation'] or row['fields']['reflection'] or row['fields']['shear']][:5])
    (OUT/'TransformEvidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('records','distinctSourceBlobs','fieldTagSignatures','nativeLabels','flagCombinations','scales')},indent=2))

if __name__=='__main__':main()
