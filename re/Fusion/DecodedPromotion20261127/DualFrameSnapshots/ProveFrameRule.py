from pathlib import Path
from dataclasses import replace, asdict
from collections import Counter
from math import cos, sin, tau
import hashlib,json,sys

root=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(root/'src'),str(root)]
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import BodyClosure
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CanonicalBody import CanonicalBody
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSnapLinks import CheckSnapLinks
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSnapHead import CheckSnapHead
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces,FaceCoedges
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers,ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import CheckIdentity,PointCoords
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import TransformNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import SketchAttrib
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Geometry.Extrude.Circular.DualSide.DualFrame import DualFrame
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState

def certify_transform(state,body):
    if body.TransformRef==-1:return
    node=SnapEntity(state,body.TransformRef,TransformNode)
    assert node==TransformNode(-1,-1,(1.,0.,0.),(0.,1.,0.),(0.,0.,1.),(0.,0.,0.),1.,False,False,False),'BODY transform is not exactly identity'

def faces(state,body):
    certify_transform(state,body)
    return BodyFaces(state,replace(body,TransformRef=-1))

def frame_source(graph,context,shape,reading):
    matrix=context.Plane.Fields['transform']; assert isinstance(matrix,MatrixValue) and matrix.Entries is not None
    values=matrix.Entries; assert len(values)==16 and values[12:]==(0.,0.,0.,1.)
    owned=ResolveField(graph,context.SketchFeature,'rSketchPlaneMatrix','DRMatrix')
    assert owned.Fields['matrix3d']==matrix
    CheckIdentity(context.Sketch.Fields['occurrenceTransform'])
    frame=Transform(SpaceVector(*(values[i]*10 for i in (3,7,11))),SpaceVector(*(values[i] for i in (0,4,8))),SpaceVector(*(values[i] for i in (1,5,9))),SpaceVector(*(values[i] for i in (2,6,10))))
    placed=DualFrame(frame,shape.Geometry)
    SameNumbers(PointCoords(context.Extrude.Fields['profileNormal']),(frame.z_axis.x,frame.z_axis.y,frame.z_axis.z))
    SameNumbers(values,tuple(reading['profile']['transform']))
    SameNumbers(tuple(v/10 for v in (placed.origin.x,placed.origin.y,placed.origin.z)),tuple(reading['profile']['center_world_cm']))
    return frame

def sheet(state,rootid,shape,frame):
    body=SnapEntity(state,rootid,BodyNode);certify_transform(state,body)
    closure=BodyClosure(state,rootid)
    wanted={t:1 for t in (BodyNode,LumpNode,ShellNode,FaceNode,LoopNode,CoedgeNode,EdgeNode,VertexNode,PointNode,PlaneNode,EllipseNode)};wanted[SketchAttrib]=2
    if body.TransformRef!=-1:wanted[TransformNode]=1
    assert Counter(type(state.Entities[i]) for i in closure)==wanted
    face,=faces(state,body)
    assert not face.Reversed and face.Contained==(False if face.DoubleSided else None)
    local=Transform() if not face.DoubleSided else frame
    placed=DualFrame(local,shape.Geometry)
    center=tuple(v/10 for v in (placed.origin.x,placed.origin.y,placed.origin.z)); normal=tuple((local.z_axis.x,local.z_axis.y,local.z_axis.z)); axisu=tuple((local.x_axis.x,local.x_axis.y,local.x_axis.z));axisv=tuple((local.y_axis.x,local.y_axis.y,local.y_axis.z))
    plane=SnapEntity(state,face.Surface,PlaneNode)
    SameNumbers(plane.OriginCm,center);SameNumbers(plane.Normal,normal);SameNumbers(plane.ReferenceAxis,axisu)
    assert not plane.ReversedV and all(v is None for v in (plane.ULower,plane.UUpper,plane.VLower,plane.VUpper))
    coedge,=FaceCoedges(state,face); assert coedge.Partner==-1 and not coedge.Reversed and coedge.Pcurve==-1
    edge=SnapEntity(state,coedge.EdgeRef,EdgeNode);curve=SnapEntity(state,edge.CurveRef,EllipseNode)
    radius=shape.Geometry.radius/10
    SameNumbers(curve.OriginCm,center);SameNumbers(curve.Normal,normal);SameNumbers(curve.MajorAxisCm,tuple(radius*x for x in axisu))
    assert curve.EllipseRatio==1 and curve.LowerBound is None and curve.UpperBound is None
    assert edge.StartVertex==edge.EndVertex and not edge.Reversed and edge.Convexity=='unknown'
    SameNumbers((edge.EndParam-edge.StartParam,),(tau,))
    vertex=SnapEntity(state,edge.StartVertex,VertexNode);assert vertex.EdgeIndex==0
    point=SnapEntity(state,vertex.PointRef,PointNode)
    expected=tuple(c+radius*cos(edge.StartParam)*u+radius*sin(edge.StartParam)*v for c,u,v in zip(center,axisu,axisv,strict=True));SameNumbers(point.PositionCm,expected)
    for i in closure:
        node=state.Entities[i]
        if not isinstance(node,(EdgeNode,CoedgeNode,SketchAttrib)):
            assert MakeEntityNode(node).Tokens[0]==(12,-1)
        if isinstance(node,(EdgeNode,CoedgeNode)):
            attribute=SnapEntity(state,node.Prefix.Attribute,SketchAttrib)
            assert attribute.SourceLink==SketchLink(CurveTag(shape.CurveNode),0,int(isinstance(node,EdgeNode)),1,1)
            assert (attribute.Links.OwnerRef,attribute.Links.NextAttrib,attribute.Links.PriorAttrib)==(i,-1,-1)
    return closure

def validate(data,reading):
    model=ReadDocument(data);assert len(model.Bodies)==1 and len(model.Snapshots)==1
    graph=BuildGraph(model);context=SelectExtrusion(graph);shape=ReadCircle(graph,context)
    frame=frame_source(graph,context,shape,reading)
    CheckScopes(graph,context,model.Asset.AssetId);CheckRegion(graph,context,(shape.CurveNode,),model.Asset.AssetId)
    live=ReadDualState(model.Bodies[0].History,context.Extrude.Fields['endModelHS']);state=model.Snapshots[0].Snapshot
    CheckSnapHead(state,live)
    roots=[(i,e,faces(state,e)) for i,e in enumerate(state.Entities) if isinstance(e,BodyNode)]
    assert len(roots)==3
    assert all(e.Prefix.Attribute==-1 and e.Prefix.EntityTag==-1 for i,e,f in roots)
    roles=tuple((i,'solid' if len(f)>1 else 'profile' if f[0].DoubleSided else 'sketch') for i,e,f in roots)
    assert {r for i,r in roles}=={'solid','profile','sketch'}
    CheckSnapLinks(model,graph,context,tuple(r for i,r in roles))
    solid=next(i for i,r in roles if r=='solid');liveroot,=(i for i,e in enumerate(live.Entities) if isinstance(e,BodyNode));certify_transform(live,live.Entities[liveroot])
    assert CanonicalBody(state,solid)==CanonicalBody(live,liveroot)
    closures=[BodyClosure(state,solid)]+[sheet(state,i,shape,frame) for i,r in roles if r!='solid']
    assert sum(map(len,closures))==len(state.Entities)-1 and set().union(*map(set,closures))==set(range(1,len(state.Entities)))
    return {'solid_correspondence':True,'source_frame':asdict(frame),'body_roles':roles,'closure_sizes':list(map(len,closures)),'snapshot_records':len(state.Entities),'sheet_correspondence':True,'all_records_accounted':True}

def pins():
    base=Path(__file__).parent
    files=[base/'FrameRules.md',Path(__file__),*sorted((root/'src/convert/adapters/Fusion/Native/Circular/DualSnapshots').glob('*.py'))]
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

if __name__=='__main__':
    split=sys.argv[1];output=Path(sys.argv[2]);base=Path(__file__).parent
    if split=='freeze':
        output.write_text(json.dumps({'frozen_pins':pins(),'discovery_case':'frame','holdout_case':'holdout_a','holdout_opened':False},indent=2)+'\n');print('frozen');sys.exit()
    if split=='holdout':
        seal=json.loads(Path(sys.argv[3]).read_text());assert seal['frozen_pins']==pins(),'rule or relied-on code changed after freeze'
    caseid='frame' if split=='discovery' else 'holdout_a'
    capture_path=root/'re/Fusion/TwoSidedDraft20261127/Capture.json';capture=json.loads(capture_path.read_text());case=next(c for c in capture['cases'] if c['id']==caseid)
    observations={o['stage']:o['value'] for o in case['observations']};rows=[]
    for archive in case['archives']:
        path=root/'re/Fusion/TwoSidedDraft20261127/Native'/archive['file'];data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==archive['sha256']
        suffix=path.stem.removeprefix(caseid);stage='restore_draft_second' if suffix=='_restored' else suffix.lstrip('_') or 'baseline'
        row={'source':str(path.relative_to(root)),'sha256':archive['sha256'],'stage':stage}
        try:row.update(status='passed',**validate(data,observations[stage]))
        except Exception as error:row.update(status='failed',exception=type(error).__name__,message=str(error).replace(str(root),'<checkout>'))
        rows.append(row)
    report={'split':split,'rule_pins':pins(),'capture_sha256':hashlib.sha256(capture_path.read_bytes()).hexdigest(),'native_calls':0,'models':False,'sources':rows,'summary':{'sources':len(rows),'passed':sum(r['status']=='passed' for r in rows)}}
    output.write_text(json.dumps(report,indent=2)+'\n');print(report['summary'])
