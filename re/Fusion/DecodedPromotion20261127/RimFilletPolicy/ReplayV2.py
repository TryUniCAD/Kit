import hashlib,json
from pathlib import Path
from RunPolicy import validate
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from MakeCounters import corrupt

root=Path(__file__).resolve().parents[4];folder=Path(__file__).parent
seal=json.loads((folder/'RuleSealV2.json').read_text())
for name,digest in seal['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest
records=json.loads((root/'re/Fusion/RimFilletPack/Qualification/Cases.json').read_text())
rows=[]
for record in records:
    identity=record['id']
    path=root/('re/Fusion/RimFilletPack/Sources/'+identity.removeprefix('source-')+'/Native.f3d' if identity.startswith('source-') else 're/Fusion/RimFilletPack/Qualification/Archives/'+identity+'/Native.f3d')
    data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==record['source_sha256']
    row=dict(source=str(path.relative_to(root)),sha256=digest,case=identity,native_build=record['measurements']['version'])
    try:
        result=validate(data);measured=record['measurements']['initial']['parameters'];projected={p['name']:p for p in result['parameters']}
        assert len(measured)==len(projected)
        for p in measured:
            decoded=projected[p['name']];multiplier=10 if p['unit']=='mm' else 1
            assert abs(decoded['value']['value']-p['value']*multiplier)<1e-9
            assert decoded['expression']['source']==p['expression']
        row.update(passed=True,result=result,actual_api_parameter_comparisons=len(measured))
    except Exception as error:row.update(passed=False,error=type(error).__name__+': '+str(error))
    rows.append(row)
directory=folder/'Counterexamples';directory.mkdir(exist_ok=False)
source=(root/'re/Fusion/RimFilletPack/Sources/discovery-01/Native.f3d').read_bytes()
negatives=[]
for mode in ('role','unit','expression','owner','reciprocal','allocator','selected_owner','selected_alias','selected_body','radius_alias','variable_mode','scope_mode','history_join','dynamic_owner','cached_radius','recipe_face'):
    row=dict(mode=mode)
    try:
        bad=corrupt(ReadDocument(source),mode);encoded=EmitParsed(bad);(directory/(mode+'.f3d')).write_bytes(encoded)
        row.update(sha256=hashlib.sha256(encoded).hexdigest(),bytes=len(encoded),encoded=True)
        validate(encoded);row['status']='unexpected_admission'
    except Exception as error:row.update(status='refused',error=type(error).__name__+': '+str(error))
    negatives.append(row)
receipt=dict(native_calls=0,models=False,post_exposure=True,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rule_seal_sha256=hashlib.sha256((folder/'RuleSealV2.json').read_bytes()).hexdigest(),counterexample_source_sha256=hashlib.sha256(source).hexdigest(),rows=rows,counterexamples=negatives)
(folder/'ReceiptV2.json').write_text(json.dumps(receipt,indent=2,default=repr)+'\n')
print(dict(cases=len(rows),passed=sum(r['passed'] for r in rows),failures=[(r['case'],r['error']) for r in rows if not r['passed']],negatives=len(negatives),encoded=sum(r.get('encoded',False) for r in negatives),refused=sum(r['status']=='refused' for r in negatives)))
