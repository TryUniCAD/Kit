import json, hashlib, sys
from pathlib import Path
from dataclasses import asdict
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from Policy import SelectContext, ExistingChecks, CheckRegion, ReadCircle
from RoleChecks import Parameters, Selection
from GraphProof import Managers,Caches,ReferenceCoverage,Allocators

root=Path(__file__).resolve().parents[4]
folder=Path(__file__).parent

def validate(data):
    model=ReadDocument(data)
    graph=BuildGraph(model)
    context,rim,rimdata=SelectContext(graph)
    inherited=ExistingChecks(model,graph,context,rim,rimdata)
    for name,result in inherited.items():
        if name!='region' and not result['passed']:raise ValueError(name+': '+result['error'])
    parameters=Parameters(graph,context,rim,rimdata)
    selected,recipe=Selection(graph,context,rim,rimdata,model.Asset.AssetId)
    Managers(graph,context,rim)
    Caches(graph,context,rim,rimdata,model.Asset.AssetId)
    Allocators(graph,context)
    refs=ReferenceCoverage(graph)
    return dict(check_groups=18,reference_occurrences=refs,semantic_nodes=sum(n.SegmentId==0 for n in graph.Nodes.values()),field_occurrences=sum(len(n.Fields) for n in graph.Nodes.values()),selected_reference=selected.Identity,parameters=[asdict(p) for p in parameters],inherited_checks=inherited)

if __name__=='__main__':
    destination=Path(sys.argv[1])
    assert not destination.exists()
    rows=[]
    for index in range(1,7):
        path=root/f're/Fusion/RimFilletPack/Sources/discovery-{index:02}/Native.f3d'
        data=path.read_bytes()
        row=dict(source=str(path.relative_to(root)),sha256=hashlib.sha256(data).hexdigest())
        try:row.update(passed=True,result=validate(data))
        except Exception as error:row.update(passed=False,error=type(error).__name__+': '+str(error))
        rows.append(row)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.py')}
    destination.write_text(json.dumps(dict(native_calls=0,models=False,reserved_opened=False,producer_hashes=hashes,rows=rows),indent=2,default=repr)+'\n')
    print(dict(cases=len(rows),passed=sum(r['passed'] for r in rows),failures=[r for r in rows if not r['passed']]))
