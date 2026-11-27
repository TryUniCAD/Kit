from math import isfinite
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanLink import CheckSpanLink
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes,ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import SketchAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode


def attributes(state,roles,source,snapshot,graph,final):
    assert all(e.Attribute==-1 for e in state.Entities if isinstance(e,TagAttrib))
    attrs={i:e for i,e in enumerate(state.Entities) if isinstance(e,(TagAttrib,SketchAttrib,TimeAttrib,TrackAttrib))};seen=set()
    for index,e in enumerate(state.Entities):
        if index in attrs:continue
        head=MakeEntityNode(e).Tokens[0][1];previous=-1
        while head!=-1:
            assert head in attrs and head not in seen
            a=attrs[head];assert a.Links.OwnerRef==index and a.Links.PriorAttrib==previous
            seen.add(head);previous,head=head,a.Links.NextAttrib
    assert seen==set(attrs)
    bodies=[e for e in attrs.values() if isinstance(e,TagAttrib) and e.Links.OwnerRef==roles['root']];assert len(bodies)==1
    tag=bodies[0].Groups;assert len(tag)==1
    operation,=(op for op,oid in source['ops'].items() if oid==source['extrude'].ObjectId and op==int(tag[0].PrimaryId))
    assert tag[0].OperationIds==() and tag[0].ApproachId==0
    table=ResolveField(graph,source['extrude'],'rProgenitorTable','ProgenitorTable')
    bodypairs=[p for p in table.Fields['ProgenitorTagVec'].Items if graph.Resolve(p.First).ClassName=='BodyProgenitor'];assert len(bodypairs)==1 and tag[0].SecondaryId==bodypairs[0].Second
    expected={roles['root']:tag,roles['faces']['side']:(snapshot.TagSet.SideFace,),roles['faces']['top']:(snapshot.TagSet.TopFace,),roles['faces']['bottom']:(snapshot.TagSet.BottomFace,),roles['edges']['bottom']:(snapshot.TagSet.BottomEdge,)}
    if final:
        filletop,=(op for op,oid in source['ops'].items() if oid==source['feature'].ObjectId)
        fillettable=ResolveField(graph,source['feature'],'rProgenitorTable','ProgenitorTable');pair,=fillettable.Fields['ProgenitorTagVec'].Items;progenitor=graph.Resolve(pair.First);assert progenitor.ClassName=='BrepProgenitor'
        assert ResolveField(graph,progenitor,'m_brepRecipe','ASMRecipe').Fields['m_Recipe'].Value==source['recipe']
        expected[roles['faces']['blend']]=(FeatureTag(str(pair.Second),(filletop,),0,0),)
    else:expected[roles['edges']['top']]=(snapshot.TagSet.TopEdge,)
    actual={a.Links.OwnerRef:a.Groups for a in attrs.values() if isinstance(a,TagAttrib)};assert actual==expected
    sketches=[a for a in attrs.values() if isinstance(a,SketchAttrib)]
    bottomuses={i for i,e in enumerate(state.Entities) if isinstance(e,CoedgeNode) and e.EdgeRef==roles['edges']['bottom']}
    assert {a.Links.OwnerRef for a in sketches}==bottomuses and len(sketches)==2
    for a in sketches:CheckSpanLink(state,a,source['shape'])
    times=[a for a in attrs.values() if isinstance(a,TimeAttrib)];assert len(times)==1 and times[0].Links.OwnerRef==roles['root'] and isfinite(times[0].UnixMicros) and times[0].UnixMicros>=0
    return dict(tag_owners=len(actual),attributes=len(attrs),operation=operation)
