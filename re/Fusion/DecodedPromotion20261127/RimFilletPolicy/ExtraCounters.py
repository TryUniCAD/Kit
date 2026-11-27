from pathlib import Path
from dataclasses import replace
import json,hashlib
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import ReadRimContext
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import CheckRimPolicy
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField

root=Path(__file__).resolve().parents[4];folder=Path(__file__).parent
source=(root/'re/Fusion/RimFilletPack/Sources/discovery-01/Native.f3d').read_bytes()
rows=[]
for mode in ('cache_distribution','orphan_data','foreign_segment'):
    model=ReadDocument(source);graph=BuildGraph(model);ctx=ReadRimContext(graph)
    row=dict(mode=mode)
    try:
        if mode=='cache_distribution':
            profile=graph.Resolve(ctx.Extrusion.Extrude.Fields['profileDataRefs'].Items[0]);selected=graph.Resolve(ctx.EdgeData.Fields['connectedEdgeRef'])
            model=ChangeField(model,selected.ObjectId,'caches',ValueSeries(selected.Fields['caches'].Items+profile.Fields['caches'].Items))
            model=ChangeField(model,profile.ObjectId,'caches',ValueSeries(()))
        else:
            segment=model.Segments[0];records=tuple(r for r in segment.Records if r.ObjectId==ctx.EdgeData.ObjectId)
            if mode=='orphan_data':
                new_id=max(r.ObjectId for r in segment.Records)+1
                segment=replace(segment,Records=segment.Records+tuple(replace(r,ObjectId=new_id) for r in records))
                model=replace(model,Segments=(segment,*model.Segments[1:]))
            else:
                other=model.Segments[1];new_id=max(r.ObjectId for r in other.Records)+1
                other=replace(other,Records=other.Records+tuple(replace(r,ObjectId=new_id) for r in records))
                model=replace(model,Segments=(segment,other,*model.Segments[2:]))
        encoded=EmitParsed(model);(folder/'Counterexamples'/(mode+'.f3d')).write_bytes(encoded)
        row.update(sha256=hashlib.sha256(encoded).hexdigest(),encoded=True)
        decoded=ReadDocument(encoded);g=BuildGraph(decoded)
        CheckRimPolicy(decoded,g,ReadRimContext(g));row['status']='unexpected_admission'
    except Exception as error:row.update(status='refused',error=type(error).__name__+': '+str(error))
    rows.append(row)
(folder/'ExtraCounterReceipt.json').write_text(json.dumps(dict(native_calls=0,models=False,post_exposure=True,source_sha256=hashlib.sha256(source).hexdigest(),program_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows),indent=2)+'\n')
print(json.dumps(rows,indent=2))
