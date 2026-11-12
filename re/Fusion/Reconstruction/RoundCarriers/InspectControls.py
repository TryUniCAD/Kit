import hashlib
import json
import lzma
import runpy
import subprocess
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
READ=runpy.run_path(str(ROOT/'re/Fusion/Reconstruction/BrepTokens.py'))['read_stream']
FIELDS=runpy.run_path(str(ROOT/'re/Fusion/Reconstruction/JournalStates/Materialize.py'))['Fields']
THIN=Path('/tmp/kit-fusion-native-analysis/ASMkern232.arm64.dylib')

def decode(record):
    fields=FIELDS(record)
    result=dict(attribute=fields.take(12),entityTag=fields.take(4),reservedRef=fields.take(12),centerCm=fields.take(19))
    if record['name']=='sphere-surface':
        result.update(signedRadiusCm=fields.take(6),referenceDirection=fields.take(20),poleDirection=fields.take(20),reverseV=fields.boolean())
    elif record['name']=='torus-surface':
        result.update(axis=fields.take(20),majorRadiusCm=fields.take(6),signedMinorRadiusCm=fields.take(6),referenceDirection=fields.take(20),reverseV=fields.boolean())
    else:raise ValueError('Unsupported round carrier')
    result.update(lowerU=fields.bound(),upperU=fields.bound(),lowerV=fields.bound(),upperV=fields.bound())
    fields.done()
    return dict(kind=record['name'],fields=result)

def main():
    inventory=json.loads(lzma.decompress((ROOT/'re/Fusion/Reconstruction/BrepCoverage/Inventory.json.xz').read_bytes()))
    selected=[item for item in inventory['members'] if {'sphere-surface','torus-surface'} & set(inventory['uniqueBlobs'][item['sha256']]['recordTypes'])]
    for path in sorted((ROOT/'re/Fusion/LocalOracle/RoundCarriers').glob('*.f3d')):
        with ZipFile(path) as archive:
            selected.extend(dict(path=str(path.relative_to(ROOT)),member=name) for name in archive.namelist() if name.endswith(('.smb','.smbh')))
    rows=[]
    for source in selected:
        with ZipFile(ROOT/source['path']) as archive:data=archive.read(source['member'])
        stream=READ(data);records=[];transforms=[]
        for index,record in enumerate(stream['records']):
            if record['boundary_marker']:break
            if record['name'] in ('sphere-surface','torus-surface'):records.append(dict(index=index,**decode(record)))
            if record['name']=='transform':
                fields=FIELDS(record);value=dict(attribute=fields.take(12),entityTag=fields.take(4),columnX=fields.take(20),columnY=fields.take(20),columnZ=fields.take(20),translationCm=fields.take(20),scale=fields.take(6),rotation=fields.boolean(),reflection=fields.boolean(),shear=fields.boolean());fields.done();transforms.append(dict(index=index,fields=value))
        rows.append(dict(path=source['path'],member=source['member'],sha256=hashlib.sha256(data).hexdigest(),header=stream['header'],records=records,transforms=transforms))
    raw=lzma.compress(json.dumps(rows,separators=(',',':'),allow_nan=False).encode());(OUT/'Controls.json.xz').write_bytes(raw)
    slices=[]
    for name,start,stop in [('sphere::save_data',0x445300,0x445374),('sphere::restore_data',0x445374,0x445450),('sphere::eval',0x442d94,0x442fd0),('torus::save_data',0x47d3f4,0x47d470),('torus::restore_data',0x47d470,0x47d53c)]:
        disassembly=subprocess.check_output(['xcrun','llvm-objdump','--disassemble','--demangle',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(THIN)],text=True)
        slices.append(dict(symbol=name,start=hex(start),stop=hex(stop),disassembly=disassembly))
    blob=lzma.compress(json.dumps(slices,separators=(',',':')).encode());(OUT/'Disassembly.json.xz').write_bytes(blob)
    report=dict(scope='Read-only named field decoding and native owned controls; no production codec or independent native write acceptance',members=len(rows),carrierRecords=sum(len(row['records']) for row in rows),sourceArchives=len({row['path'] for row in rows}),controlsSha256=hashlib.sha256(raw).hexdigest(),nativeThinBinary=str(THIN),nativeThinSha256=hashlib.sha256(THIN.read_bytes()).hexdigest(),disassemblySha256=hashlib.sha256(blob).hexdigest(),slices=[{k:v for k,v in row.items() if k!='disassembly'} for row in slices],sphereObjectFields={'0x40':'centerCm','0x58':'signedRadiusCm','0x60':'referenceDirection','0x78':'poleDirection','0x90':'reverseV'},torusObjectFields={'0x40':'referenceDirection','0x58':'centerCm','0x70':'axis','0x88':'majorRadiusCm','0x90':'signedMinorRadiusCm','0x98':'reverseV'},versionGate='Orientation directions and V-sense require save version >=10300',sphereEquation='center + abs(radius)*(sin(u)*pole + cos(u)*(cos(v)*reference + sign*sin(v)*(pole cross reference))); sign=-1 if reverseV else+1',unresolved=['Torus general signed-minor-radius parameterization and degenerate regimes','Independent topology generation and complete production document routing'])
    (OUT/'Evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['members','carrierRecords','sourceArchives','controlsSha256']}))

if __name__=='__main__':main()
