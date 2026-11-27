import json,hashlib,sys
from pathlib import Path
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import ReadRimContext
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import CheckRimPolicy
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimParams import ReadRimParams
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import ReadPolicyCases

root=Path(__file__).resolve().parents[4];folder=Path(__file__).parent
rows=[]
for case in ReadPolicyCases():
    data=case.Source.read_bytes();assert hashlib.sha256(data).hexdigest()==case.Digest
    model=ReadDocument(data);graph=BuildGraph(model);context=ReadRimContext(graph)
    CheckRimPolicy(model,graph,context);params=ReadRimParams(graph,context)
    catalog={p.name:p for p in params};assert len(catalog)==len(case.Parameters)
    for name,value,unit,expression in case.Parameters:
        projected=catalog[name]
        assert abs(projected.value.value-value*(10 if unit=='mm' else 1))<1e-9
        assert projected.expression.source==expression
    rows.append(dict(source=str(case.Source.relative_to(root)),sha256=case.Digest,passed=True,parameters=len(case.Parameters)))
negatives=[]
for file in sorted((folder/'Counterexamples').glob('*.f3d')):
    data=file.read_bytes();model=ReadDocument(data);graph=BuildGraph(model)
    row=dict(source=str(file.relative_to(root)),sha256=hashlib.sha256(data).hexdigest())
    try:
        CheckRimPolicy(model,graph,ReadRimContext(graph));row['passed']=False
    except (ValueError,KeyError) as error:row.update(passed=True,error=type(error).__name__+': '+str(error))
    negatives.append(row)
sources={}
for module in tuple(sys.modules.values()):
    name=getattr(module,'__file__',None)
    if not name:continue
    path=Path(name).resolve()
    if path.suffix=='.py' and path.is_relative_to(root):sources[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
for path in (root/'src/convert/adapters/Fusion/Native/Circular/RimPolicy').glob('*.py'):sources[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
for path in (root/'tests/Convert/Integration/Fusion/RimFillet/Policy').glob('*.py'):sources[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
receipt=dict(base_revision='6087ed24cb75ad8fb10626b556192c0351d989d7',binding='working tree source hashes pending parent publication commit',python=sys.version,native_calls=0,models=False,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native_build='historical Fusion 2706.1.17',positive_cases=rows,counterexamples=negatives,loaded_repository_sources=sources)
(folder/'ProductionReceipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(dict(positive=len(rows),parameters=sum(r['parameters'] for r in rows),counterexamples=len(negatives),refused=sum(r['passed'] for r in negatives),loaded_sources=len(sources)))
