import hashlib
import json
from pathlib import Path
import struct
import sys

root=Path(sys.argv[1]).resolve()
campaign=Path(sys.argv[2]).resolve()
output=Path(sys.argv[3])
sys.path[:0]=[str(root/'re/Fusion/Study'),str(root/'src')]
from fusion_archive import read_members
from fusion_metadata import design_records
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
members=[]
providers=[]
for path in sorted((campaign/'Native').glob('*.f3d')):
    content=read_members(path)
    bulk=next(k for k in content if k.endswith('/BulkStream.dat'))
    data=content[bulk]
    records,index=design_records(data,content[bulk.replace('BulkStream','MetaStream')])
    for record in records:
        if record.class_guid!='69EE2FA7-BCC7-449E-9CA9-976CEFDFED44':
            continue
        raw=data[record.body:record.end]
        providers.append(dict(file=path.name,object_id=record.object_id,record_offset=record.body,length=len(raw),prefix_hex=raw[:23].hex(),prefix_zero=raw[:23]==b'\0'*23,method=struct.unpack_from('<I',raw,47)[0],owner_trailer=raw[-11:].hex(),sha256=hashlib.sha256(raw).hexdigest()))
    for name,raw in content.items():
        if not name.endswith(('.smb','.smbh')):
            continue
        row=dict(file=path.name,member=name,sha256=hashlib.sha256(raw).hexdigest(),prefix=raw[:15].decode('ascii'))
        try:
            table=ReadAsmTable(raw)
            row.update(roots=table.RootCount,records=len(table.Records))
        except Exception as error:
            row['error']=str(error)
        members.append(row)
output.write_text(json.dumps(dict(members=members,point_providers=providers),indent=2))
print(json.dumps(dict(members=len(members),member_errors=sum('error' in r for r in members),point_providers=len(providers),nonzero_prefixes=sum(not r['prefix_zero'] for r in providers))))
