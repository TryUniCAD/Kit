import dataclasses
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanOwners import CheckSpanOwners
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState


root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]);mode=sys.argv[3]
if output.exists():raise ValueError('output must be unused')
rows=[]
for sample in ReadDualCases():
    if sample.Frame.z_axis.z!=1 or sample.FirstTaper==sample.SecondTaper==0:continue
    holdout=sample.Identity.startswith('holdout')
    if (mode=='discovery' and holdout) or (mode=='holdout' and not holdout):continue
    raw=sample.Source.read_bytes();assert hashlib.sha256(raw).hexdigest()==sample.Digest
    model=ReadDocument(raw);graph=BuildGraph(model);context=SelectExtrusion(graph);shape=ReadCircle(graph,context)
    state=ReadDualState(model.Bodies[0].History,context.Extrude.Fields['endModelHS'])
    body,bodytag=ReadSpanBody(state)
    operations=CheckSpanOwners(graph,context,model,model.Bodies[0].History,body,bodytag)
    table=ResolveField(graph,context.Extrude,'rProgenitorTable','ProgenitorTable')
    pairs=[p for p in SeriesItems(table.Fields['ProgenitorTagVec']) if isinstance(p,ValuePair) and graph.Resolve(p.First).ClassName=='SketchCurveProgenitor']
    attrs=[]
    for index,entity in enumerate(state.Entities):
        if not hasattr(entity,'Links'):continue
        owner=state.Entities[entity.Links.OwnerRef]
        role=type(owner).__name__
        if role=='FaceNode':
            surface=state.Entities[owner.Surface]
            role='side_first' if type(surface).__name__=='ConeNode' and surface.AxisVector[2]>0 else 'side_second' if type(surface).__name__=='ConeNode' else 'cap_lower' if surface.OriginCm[2]<0 else 'cap_upper'
        elif role=='EdgeNode':
            curve=state.Entities[owner.CurveRef]
            role='joint' if curve.OriginCm[2]==0 else 'rim_lower' if curve.OriginCm[2]<0 else 'rim_upper'
        attrs.append(dict(index=index,kind=type(entity).__name__,owner_role=role,record=dataclasses.asdict(entity)))
    rows.append(dict(source=str(sample.Source.relative_to(root)),sha256=sample.Digest,curve_tag=CurveTag(shape.CurveNode),side_label=pairs[0].Second,operations=operations,classes=dict(Counter(type(e).__name__ for e in state.Entities)),attributes=attrs))
output.write_text(json.dumps(dict(models=False,mode=mode,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows),indent=2,sort_keys=True))
patterns=Counter(json.dumps([(a['kind'],a['owner_role'],a['record'].get('Groups'),a['record'].get('SourceLink')) for a in r['attributes']],sort_keys=True) for r in rows)
print(json.dumps(dict(files=len(rows),patterns=len(patterns),class_patterns=len({json.dumps(r['classes'],sort_keys=True) for r in rows}))))
