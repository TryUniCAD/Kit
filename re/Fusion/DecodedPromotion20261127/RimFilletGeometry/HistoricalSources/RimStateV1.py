from dataclasses import fields,replace
from collections import Counter
from math import isclose,isfinite,pi
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces,FaceCoedges
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import BodyClosure
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import SketchAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode


def equal(actual,expected):
    if isinstance(expected,(tuple,list)):
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected,strict=True):equal(a,b)
    elif type(expected) is float:assert isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-10),(actual,expected)
    else:assert actual==expected,(actual,expected)


def shape_state(state,r,h,f):
    final=f>0;count=Counter(type(e).__name__ for e in state.Entities)
    expected=dict(AsmRoot=1,BodyNode=1,LumpNode=1,ShellNode=1,FaceNode=4 if final else 3,LoopNode=6 if final else 4,CoedgeNode=6 if final else 4,EdgeNode=3 if final else 2,VertexNode=3 if final else 2,PointNode=3 if final else 2,PlaneNode=2,ConeNode=1,EllipseNode=3 if final else 2,TagAttrib=6,SketchAttrib=2,TimeAttrib=1)
    expected['TorusNode' if final else 'TrackAttrib']=1
    assert count==expected,(count,expected)
    root,=(i for i,e in enumerate(state.Entities) if isinstance(e,BodyNode));body=state.Entities[root]
    assert set(BodyClosure(state,root))==set(range(1,len(state.Entities))) and root==1
    faces=BodyFaces(state,body);assert len(faces)==expected['FaceNode'] and set(faces)=={e for e in state.Entities if isinstance(e,FaceNode)}
    edge_roles={};surface_roles={};a=r-f;z=h-f
    for index,e in enumerate(state.Entities):
        name=type(e).__name__
        if name in ('PlaneNode','ConeNode','TorusNode','EllipseNode','PointNode'):
            assert e.Prefix.Attribute==e.Prefix.EntityTag==-1
        if name=='ConeNode':
            want=dict(OriginCm=(0.,0.,0.),AxisVector=(0.,0.,1.),MajorAxisCm=(r,0.,0.),EllipseRatio=1.,EllipseLower=None,EllipseUpper=None,SineAngle=0.,CosineAngle=1.,UScaleCm=r,Reversed=False,ULower=None,UUpper=None,VLower=None,VUpper=None);surface_roles[index]='side'
        elif name=='TorusNode':
            want=dict(CenterCm=(0.,0.,z),AxisVector=(0.,0.,1.),MajorRadiusCm=a,MinorRadiusCm=f,ReferenceAxis=(1.,0.,0.),ReversedV=False,ULower=None,UUpper=None,VLower=None,VUpper=None);surface_roles[index]='blend'
        elif name=='PlaneNode':
            role='bottom' if abs(e.OriginCm[2])<1e-10 else 'top';level=0. if role=='bottom' else h
            want=dict(OriginCm=(0.,0.,level),Normal=(0.,0.,1.),ReferenceAxis=(1.,0.,0.),ReversedV=False,ULower=None,UUpper=None,VLower=None,VUpper=None);surface_roles[index]=role
        elif name=='EllipseNode':
            level=e.OriginCm[2];role='bottom' if abs(level)<1e-10 else 'top' if abs(level-h)<1e-10 else 'side'
            rr=a if final and role=='top' else r;zz=0. if role=='bottom' else h if role=='top' else z
            want=dict(OriginCm=(0.,0.,zz),Normal=(0.,0.,-1. if final and role=='top' else 1.),MajorAxisCm=(rr,0.,0.),EllipseRatio=1.,LowerBound=None,UpperBound=None)
            edge_roles[index]=role
        else:continue
        assert {d.name for d in fields(e)}=={'Prefix',*want}
        for key,value in want.items():equal(getattr(e,key),value)
    seen_edges=set();seen_loops=set();seen_coedges=set();face_roles={}
    for face in faces:
        index=state.Entities.index(face);role=surface_roles[face.Surface];face_roles[role]=index
        assert face.DoubleSided is False and face.Contained is None and face.Reversed==(role=='bottom')
        assert state.Entities[face.OwnerShell].FirstWire==-1
        uses=FaceCoedges(state,face);roles=set()
        for use in uses:
            ci=state.Entities.index(use);loop=state.Entities[use.OwnerLoop];edge=state.Entities[use.EdgeRef];partner=state.Entities[use.Partner]
            assert ci not in seen_coedges and use.NextCoedge==use.PriorCoedge==ci and use.Pcurve==-1
            assert loop.OwnerFace==index and loop.FirstCoedge==ci and use.OwnerLoop not in seen_loops
            assert partner.Partner==ci and partner.EdgeRef==use.EdgeRef and partner.Reversed!=use.Reversed
            seen_loops.add(use.OwnerLoop);seen_coedges.add(ci);seen_edges.add(use.EdgeRef)
            roles.add(edge_roles[edge.CurveRef])
            assert use.Reversed==((role=='side' and edge_roles[edge.CurveRef]!='bottom') or role in ('top','bottom'))
        assert roles==({'bottom','side'} if final else {'bottom','top'}) if role=='side' else roles==({'side','top'} if role=='blend' else {role})
    assert set(face_roles)==({'side','blend','top','bottom'} if final else {'side','top','bottom'})
    assert seen_coedges=={i for i,e in enumerate(state.Entities) if isinstance(e,CoedgeNode)} and seen_loops=={i for i,e in enumerate(state.Entities) if isinstance(e,LoopNode)}
    assert seen_edges=={i for i,e in enumerate(state.Entities) if isinstance(e,EdgeNode)}
    for index in seen_edges:
        e=state.Entities[index];role=edge_roles[e.CurveRef];curve=state.Entities[e.CurveRef]
        assert e.StartVertex==e.EndVertex and e.Reversed is False and e.Convexity==('unknown' if role=='bottom' else 'tangent') if final else e.Convexity=='unknown'
        equal((e.StartParam,e.EndParam),(-pi,pi));assert state.Entities[e.OwnerCoedge].EdgeRef==index
        vertex=state.Entities[e.StartVertex];assert vertex.OwnerEdge==index and vertex.EdgeIndex in (0,2)
        point=state.Entities[vertex.PointRef];equal(point.PositionCm,(-curve.MajorAxisCm[0],0.,curve.OriginCm[2]))
    assert {state.Entities[i].CurveRef for i in seen_edges}==set(edge_roles)
    assert {state.Entities[i].StartVertex for i in seen_edges}=={i for i,e in enumerate(state.Entities) if isinstance(e,VertexNode)}
    assert {e.PointRef for e in state.Entities if isinstance(e,VertexNode)}=={i for i,e in enumerate(state.Entities) if isinstance(e,PointNode)}
    return dict(root=root,faces=face_roles,edges={role:next(i for i in seen_edges if edge_roles[state.Entities[i].CurveRef]==role) for role in edge_roles.values()})


def drop_tracker(state,selected,reference):
    tracks=[(i,e) for i,e in enumerate(state.Entities) if isinstance(e,TrackAttrib)];assert len(tracks)==1
    index,track=tracks[0];owner=state.Entities[selected];assert track.TrackedId==reference and track.Links.OwnerRef==selected and track.Links.PriorAttrib==-1 and owner.Prefix.Attribute==index
    following=state.Entities[track.Links.NextAttrib];assert isinstance(following,TagAttrib) and following.Links.PriorAttrib==index and following.Links.OwnerRef==selected
    entities=list(state.Entities);entities[selected]=replace(owner,Prefix=replace(owner.Prefix,Attribute=track.Links.NextAttrib));entities[track.Links.NextAttrib]=replace(following,Links=replace(following.Links,PriorAttrib=-1))
    mapping=tuple(i-(i>index) if i!=index else -1 for i in range(len(entities)))
    return replace(state,Entities=tuple(RemapEntity(e,mapping) for i,e in enumerate(entities) if i!=index)),dict(index=index,record=track)
