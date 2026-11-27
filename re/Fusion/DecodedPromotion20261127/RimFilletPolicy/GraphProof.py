from Policy import *
from RoleChecks import CheckFeatureStatus
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems,MappingItems
from math import pi
from dataclasses import fields,is_dataclass
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef

def Pairs(value):
    entries=MappingItems(value)
    result={p.First:p.Second for p in entries}
    assert len(result)==len(entries)
    return result

def Managers(graph,context,rim):
    nodes=ResolveField(graph,context.Fragment,'rNodes','DcNodes')
    children=LinkedNodes(graph,nodes,'children')
    assert len({n.Identity for n in children})==len(children)
    for field,cls in (('rComputeManager','DcComputeManager'),('rDependencyManager','DcDependencyManager'),('rAssociationManager','DcAssociationManager'),('rFeatureIdManager','DcFeatureIdManager')):
        manager=ResolveField(graph,context.Fragment,field,cls)
        assert graph.Resolve(manager.Fields['rOwnerFragment'])==context.Fragment
    compute=graph.OneClass('DcComputeManager')
    RequireFields(compute,{'sortIsCurrent':True})
    SameNodes(LinkedNodes(graph,compute,'sortedNodesAll'),children)
    assert len(set(n.Identity for n in LinkedNodes(graph,compute,'sortedNodesAll')))==len(children)
    dependency=graph.OneClass('DcDependencyManager')
    RequireFields(dependency,{'mapsAreCurrent':True})
    before=Pairs(dependency.Fields['predecessorMap'])
    after=Pairs(dependency.Fields['successorMap'])
    forward={(graph.Resolve(a).Identity,graph.Resolve(b).Identity,IntegerValue(flag)) for b,values in before.items() for a,flag in Pairs(values).items()}
    backward={(graph.Resolve(a).Identity,graph.Resolve(b).Identity,IntegerValue(flag)) for a,values in after.items() for b,flag in Pairs(values).items()}
    assert forward==backward
    component=graph.OneClass('DcComponent')
    matrix=ResolveField(graph,context.SketchFeature,'rSketchPlaneMatrix','DRMatrix')
    (datum,)=LinkedNodes(graph,matrix,'dataRefs')
    (profile,)=LinkedNodes(graph,context.Extrude,'profileDataRefs')
    (region,)=LinkedNodes(graph,profile,'dataRefs')
    tool=ResolveField(graph,context.Extrude,'rExtrudeToolBody','DcExtrudeToolBody')
    (selected,)=LinkedNodes(graph,rim,'targetDataRefs')
    (brep,)=LinkedNodes(graph,selected,'dataRefs')
    (rim_data,)=LinkedNodes(graph,rim,'filletEdgeData')
    radius=ResolveField(graph,rim_data,'radiusValue','DcDoubleParameter')
    weight=ResolveField(graph,rim_data,'tangencyWeight','DcDoubleParameter')
    expected=((component,context.SketchFeature,4096),(matrix,context.SketchFeature,1),(datum,matrix,1),(component,context.Extrude,4096),(tool,context.Extrude,1),(region,profile,1),(context.SketchFeature,region,4),(profile,tool,1),(context.Along,tool,1),(context.Taper,tool,1),(component,rim,4096),(context.Extrude,rim,1024),(selected,rim,1),(weight,rim,1),(radius,rim,1),(brep,selected,1),(context.Extrude,brep,1))
    assert forward=={(a.Identity,b.Identity,flag) for a,b,flag in expected}
    childids={n.Identity for n in children}
    assert all(a in childids and b in childids and flag in (1,4,1024,4096) for a,b,flag in forward)
    assert (context.Extrude.Identity,rim.Identity,1024) in forward
    association=graph.OneClass('DcAssociationManager')
    EmptyFields(association,('associationHolderMap','featureAssociationMap'))
    feature_ids=graph.OneClass('DcFeatureIdManager')
    EmptyFields(feature_ids,('obsoleteFeatureIds',))
    identities=Pairs(feature_ids.Fields['featureIdMap'])
    inverse=Pairs(feature_ids.Fields['enetityIdMap'])
    features=(context.SketchFeature,context.Extrude,rim)
    assert set(IntegerValue(v) for v in identities.values())=={n.ObjectId for n in features}
    assert {(IntegerValue(k),IntegerValue(v)) for k,v in identities.items()}=={(IntegerValue(v),IntegerValue(k)) for k,values in inverse.items() for v in SeriesItems(values)}
    assert len(identities)==4 and len(inverse)==3
    assert len(SeriesItems(inverse[context.Extrude.ObjectId]))==2
    assert len(SeriesItems(inverse[context.SketchFeature.ObjectId]))==len(SeriesItems(inverse[rim.ObjectId]))==1
    dyns=tuple(ResolveField(graph,n,'rDynamicUpdateData','DynamicUpdateData') for n in children)
    SameNodes(dyns,graph.ByClass('DynamicUpdateData'))
    assert len({n.Identity for n in dyns})==len(dyns)
    for owner,dyn in zip(children,dyns,strict=True):
        RequireFields(owner,{'isActive':True,'isEdited':False,'isEliminated':False,'rGroupRepresentative':None})
        assert graph.Resolve(owner.Fields['rParent'])==nodes
        if 'status' in owner.Fields:CheckFeatureStatus(graph,owner)
        assert graph.Resolve(dyn.Fields['rOwnerNode'])==owner
        health=owner.ClassName not in ('DcDoubleParameter','DcComponent')
        RequireFields(dyn,{'isBodyOK':health,'isPredecessorOK':health,'xRefPredecessorsHash':0})
        EmptyFields(dyn,('bodies',))
        assert IntegerValue(dyn.Fields['timeStamp'])>=0
        for ref,stamp in Pairs(dyn.Fields['predecessors']).items():
            pred=graph.Resolve(ref)
            pred_dyn=ResolveField(graph,pred,'rDynamicUpdateData','DynamicUpdateData')
            assert IntegerValue(stamp)==IntegerValue(pred_dyn.Fields['timeStamp'])
        if not health:
            EmptyFields(dyn,('predecessors',))
    assert IntegerValue(context.Extrude.Fields['endModelHS'])==IntegerValue(rim.Fields['startModelHS'])
    assert IntegerValue(rim.Fields['endModelHS'])>IntegerValue(rim.Fields['startModelHS'])
    SameNodes(tuple(ResolveField(graph,n,'status','DcStatus') for n in children if 'status' in n.Fields),graph.ByClass('DcStatus'))

def Caches(graph,context,rim,data,asset_id):
    connected=graph.Resolve(data.Fields['connectedEdgeRef'])
    (brep,)=LinkedNodes(graph,connected,'dataRefs')
    (circle,)=LinkedNodes(graph,brep,'caches')
    assert circle.ClassName=='ETCachedCircleArc'
    SameNodes((circle,),graph.ByClass('ETCachedCircleArc'))
    matrix=ResolveField(graph,context.SketchFeature,'rSketchPlaneMatrix','DRMatrix')
    (profile,)=LinkedNodes(graph,context.Extrude,'profileDataRefs')
    SameNodes((*LinkedNodes(graph,matrix,'caches'),*LinkedNodes(graph,profile,'caches'),*LinkedNodes(graph,connected,'caches')),graph.ByClass('ETCachedMatrix3d'))
    (datum,)=LinkedNodes(graph,matrix,'dataRefs')
    SameNodes(LinkedNodes(graph,datum,'caches'),graph.ByClass('ETCachedPlane'))
    (region,)=LinkedNodes(graph,profile,'dataRefs')
    tool=ResolveField(graph,context.Extrude,'rExtrudeToolBody','DcExtrudeToolBody')
    SameNodes((*LinkedNodes(graph,region,'caches'),*LinkedNodes(graph,tool,'toolbodyCaches')),graph.ByClass('ETCachedTopology'))
    RequireFields(circle,{'progenitor':None,'rCachedEdge':None,'startPtProgenitor':None,'endPtProgenitor':None})
    CheckIdentity(circle.Fields['sketchTransf'])
    geometry=ObjectFields(circle.Fields['rCachedGeometry'])
    assert set(geometry)=={'center','normal','refVec','radius','startAngle','endAngle'}
    SameNumbers(PointCoords(geometry['center']),(0,0,NumberValue(context.Along.Fields['value'])))
    SameNumbers(PointCoords(geometry['normal']),(0,0,1))
    SameNumbers(PointCoords(geometry['refVec']),(1,0,0))
    SameNumbers((NumberValue(geometry['radius']),NumberValue(geometry['startAngle']),NumberValue(geometry['endAngle'])),(ReadCircle(graph,context).Geometry.radius/10,0,2*pi))
    for node in graph.ByClass('ETCachedMatrix3d'):
        CheckIdentity(node.Fields['rCachedGeometry'])
        CheckIdentity(node.Fields['sketchTransf'])
        RequireFields(node,{'progenitor':None})
    for node in graph.ByClass('ETCachedTopology'):
        RequireFields(node,{'progenitor':None})
        assert ObjectFields(node.Fields['scope'])==dict(assetId=asset_id,scopeEntityIdentifier=TextValue(context.Component.Fields['persistentId']),scopeIdType=2,segmentId=0)
        assert IntegerValue(node.Fields['cachedEntityId'])>0
    for node in (context.Component,context.BodyNode):
        assert all(v==-1 for v in ObjectFields(node.Fields['massProperties']).values())
    EmptyFields(context.BodyNode,('faceVisualMaterialByAttrTagID',))
    RequireFields(context.DcBody,{'isEliminated':False})
    assert graph.Resolve(context.DcBody.Fields['rOwnFeature'])==context.Extrude
    assert graph.Resolve(context.DcBody.Fields['rParent'])==context.Fragment
    assert context.BodyNode.Fields['persistentId']==context.DcBody.Fields['bodyUuid']==graph.OneClass('BodyProgenitor').Fields['bodyUuid']

def ReferenceCoverage(graph):
    count=0
    def walk(value,segment):
        nonlocal count
        if isinstance(value,(LocalRef,SegmentRef)):
            graph.Resolve(value,segment)
            count+=1
        elif is_dataclass(value):
            for field in fields(value):
                walk(getattr(value,field.name),segment)
        elif isinstance(value,tuple):
            for item in value:walk(item,segment)
    for node in graph.Nodes.values():
        assert all(group.Opaque is None for group in node.Groups)
        walk(node.Groups,node.SegmentId)
    return count

def Allocators(graph,context):
    for node in graph.ByClass('PassiveIdGenerator'):
        scan=tuple(IntegerValue(x) for x in SeriesItems(node.Fields['scanOrderIndex']))
        addresses=tuple(IntegerValue(x) for x in SeriesItems(node.Fields['addressOfTopEntities']))
        assert len(set(scan))==len(scan) and scan and min(scan)>0
        assert IntegerValue(node.Fields['nextId'])>max(scan)
        assert not addresses or len(addresses)==len(scan) and min(addresses)>0
        assert node.Fields['rBody'] is None
        if node.Fields['rBodies'] is not None:
            assert graph.Resolve(node.Fields['rBodies'])==graph.Resolve(context.Component.Fields['rBodies'])
    serializer=graph.OneClass('BRepSerializer')
    generator=ResolveField(graph,serializer,'topEntityPIDGenerator','PassiveIdGenerator')
    assert generator.Fields['rBodies'] is None
    RequireFields(serializer,{'rBody':None})
    EmptyFields(serializer,('mapBodyId',))
    for feature in (context.SketchFeature,context.Extrude,graph.OneClass('DcFilletEdgeFeature')):
        table=ResolveField(graph,feature,'rProgenitorTable','ProgenitorTable')
        entries=SeriesItems(table.Fields['ProgenitorTagVec'])
        tags=tuple(IntegerValue(p.Second) for p in entries)
        assert len(set(tags))==len(tags) and (not tags or min(tags)>0)
        assert IntegerValue(table.Fields['tagId'])>max(tags,default=0)
        assert len({graph.Resolve(p.First).Identity for p in entries})==len(entries)
        RequireFields(table,{'rParent':None})
