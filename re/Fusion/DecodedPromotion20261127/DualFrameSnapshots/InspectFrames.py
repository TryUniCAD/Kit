import json,hashlib,sys
from pathlib import Path
from dataclasses import asdict
from collections import Counter
root=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(root/'src'),str(root)]
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CanonicalBody import CanonicalBody
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import BodyClosure
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import TransformNode
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState

def faces(st,body):
 lump=SnapEntity(st,body.FirstLump,LumpNode);shell=SnapEntity(st,lump.FirstShell,ShellNode)
 result=[];i=shell.FirstFace
 while i!=-1:
  f=SnapEntity(st,i,FaceNode);result.append(f);i=f.NextFace
 return result
capture=json.loads((root/'re/Fusion/TwoSidedDraft20261127/Capture.json').read_text())
case=next(c for c in capture['cases'] if c['id']=='frame')
rows=[]
for archive in case['archives']:
 path=root/'re/Fusion/TwoSidedDraft20261127/Native'/archive['file'];data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==archive['sha256']
 model=ReadDocument(data);graph=BuildGraph(model);ctx=SelectExtrusion(graph);shape=ReadCircle(graph,ctx)
 live=ReadDualState(model.Bodies[0].History,ctx.Extrude.Fields['endModelHS']);snap=model.Snapshots[0].Snapshot
 bodies=[(i,e) for i,e in enumerate(snap.Entities) if isinstance(e,BodyNode)]
 solid=next(i for i,e in bodies if len(faces(snap,e))>1);liveroot=next(i for i,e in enumerate(live.Entities) if isinstance(e,BodyNode))
 closures=[BodyClosure(snap,i) for i,e in bodies]
 row={'source':str(path.relative_to(root)),'sha256':archive['sha256'],'selected_plane':repr(ctx.Plane.Fields),'occurrence_transform':repr(ctx.Sketch.Fields['occurrenceTransform']),'profile_normal':repr(ctx.Extrude.Fields['profileNormal']),'circle_geometry':repr(shape.Geometry),'live_transform_records':[(i,asdict(e)) for i,e in enumerate(live.Entities) if isinstance(e,TransformNode)],'snapshot_transform_records':[(i,asdict(e)) for i,e in enumerate(snap.Entities) if isinstance(e,TransformNode)],'snapshot_classes':dict(Counter(type(e).__name__ for e in snap.Entities)),'snapshot_bodies':[(i,asdict(e),len(faces(snap,e))) for i,e in bodies],'live_bodies':[(i,asdict(e)) for i,e in enumerate(live.Entities) if isinstance(e,BodyNode)],'solid_graph_correspondence':CanonicalBody(snap,solid)==CanonicalBody(live,liveroot),'closure_sizes':[len(x) for x in closures],'closure_intersections':[sorted(set(closures[i])&set(closures[j])) for i in range(3) for j in range(i+1,3)],'api_observations':case['observations']}
 rows.append(row)
report={'discovery_only':True,'holdout_a_opened':False,'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sources':rows}
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(rows[0],indent=2)[:13000]);print('sources',len(rows),'solidmatches',sum(x['solid_graph_correspondence'] for x in rows))
