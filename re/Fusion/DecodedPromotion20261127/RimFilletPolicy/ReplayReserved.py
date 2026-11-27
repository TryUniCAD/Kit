import hashlib,json
from pathlib import Path
from RunPolicy import validate

root=Path(__file__).resolve().parents[4]
folder=Path(__file__).parent
seal=json.loads((folder/'RuleSeal.json').read_text())
for name,digest in seal['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest
records=json.loads((root/'re/Fusion/RimFilletPack/Qualification/Cases.json').read_text())
rows=[]
for record in records:
    identity=record['id']
    if identity.startswith('source-discovery'):continue
    path=root/('re/Fusion/RimFilletPack/Sources/'+identity.removeprefix('source-')+'/Native.f3d' if identity.startswith('source-') else 're/Fusion/RimFilletPack/Qualification/Archives/'+identity+'/Native.f3d')
    data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert digest==record['source_sha256']
    row=dict(source=str(path.relative_to(root)),sha256=digest,case=identity,native_build=record['measurements']['version'])
    try:
        result=validate(data)
        measured=record['measurements']['initial']['parameters']
        projected={p['name']:p for p in result['parameters']}
        assert len(measured)==len(projected)
        for parameter in measured:
            p=projected[parameter['name']]
            multiplier=10 if parameter['unit']=='mm' else 1
            assert abs(p['value']['value']-parameter['value']*multiplier)<1e-9
            assert p['expression']['source']==parameter['expression']
        row.update(passed=True,result=result,actual_api_parameter_comparisons=len(measured))
    except Exception as error:row.update(passed=False,error=type(error).__name__+': '+str(error))
    rows.append(row)
output=folder/'ReservedReceipt.json'
assert not output.exists()
output.write_text(json.dumps(dict(rule_seal_sha256=hashlib.sha256((folder/'RuleSeal.json').read_bytes()).hexdigest(),native_calls=0,models=False,typed_source_split_only=True,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows),indent=2,default=repr)+'\n')
print(dict(cases=len(rows),passed=sum(r['passed'] for r in rows),failures=[(r['case'],r['error']) for r in rows if not r['passed']]))
