from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes,ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue,MappingItems
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures


def read_source(graph,model,prior):
    component=graph.OneClass('FusionComponent');fragment,ordered=OrderedFeatures(graph,component)
    assert tuple(n.ClassName for n in ordered)==('DcSketch','DcExtrudeFeature','DcFilletEdgeFeature')
    sketch,extrude,feature=ordered;data,=LinkedNodes(graph,feature,'filletEdgeData')
    assert data.ClassName=='DcFilletEdgeData' and feature.Fields['rParamRadius'] is None
    for key,want in dict(bAsymmetric=False,bChord=False,bConstantRadius=True,bFlip=False,bG2Blend=False,bIsComputeChain=True,bRuleFillet=False).items():assert data.Fields[key] is want
    for key in ('chordLen','curveChainStartPoint','edgeOffset1Value','edgeOffset2Value','rFaceRef','rFeatureRef','rFullRoundRef','rRuleRef'):assert data.Fields[key] is None
    for key in ('edgeSequence','midPointParams','pointParams','pointRadii'):assert not data.Fields[key].Items
    radius=ResolveField(graph,data,'radiusValue','DcDoubleParameter');user=ResolveField(graph,radius,'parameter','Parameter')
    assert graph.Resolve(user.Fields['dcParameter'])==radius and graph.Resolve(radius.Fields['rrOwnerFeature'])==feature and user.Fields['name']=='Radius' and user.Fields['unit']=='mm'
    amount=NumberValue(radius.Fields['value']);assert amount==NumberValue(user.Fields['value']) and amount>0
    weight=ResolveField(graph,data,'tangencyWeight','DcDoubleParameter');weightuser=ResolveField(graph,weight,'parameter','Parameter')
    assert graph.Resolve(weight.Fields['rrOwnerFeature'])==feature and graph.Resolve(weightuser.Fields['dcParameter'])==weight and weight.Fields['value']==weightuser.Fields['value']==1.0 and weightuser.Fields['name']=='TangencyWeight'
    target,=LinkedNodes(graph,feature,'targetDataRefs');assert graph.Resolve(data.Fields['connectedEdgeRef'])==target
    operand,=LinkedNodes(graph,target,'dataRefs');assert target.ClassName=='ModelDataRef' and operand.ClassName=='BrepRef'
    body,=LinkedNodes(graph,operand,'refBodies');assert body.ClassName=='DcBody' and graph.Resolve(body.Fields['rOwnFeature'])==extrude
    actual=ResolveField(graph,body,'rBody','Body');assert body.Fields['bodyUuid']==actual.Fields['persistentId']
    recipe=ResolveField(graph,operand,'rRecipe','ASMRecipe').Fields['m_Recipe'];assert isinstance(recipe,OptionalValue) and isinstance(recipe.Value,RecipeValue) and isinstance(recipe.Value.Payload,EdgeRecipe)
    tag,=recipe.Value.Tags[recipe.Value.Payload.PrimaryTagIndex];tag=FeatureTag(''.join(map(chr,tag.PrimaryId)),tag.OperationIds,tag.SecondaryId,tag.ApproachId)
    selected,=(e.Links.OwnerRef for e in prior.Entities if isinstance(e,TagAttrib) and e.Groups==(tag,));edge=prior.Entities[selected];assert isinstance(edge,EdgeNode)
    circle=prior.Entities[edge.CurveRef];assert isinstance(circle,EllipseNode)
    height=NumberValue(ResolveField(graph,extrude,'rAlongDistance','DcDoubleParameter').Fields['value']);assert abs(circle.OriginCm[2]-height)<1e-10
    assert extrude.Fields['endModelHS']==feature.Fields['startModelHS'] and feature.Fields['endModelHS']==model.Bodies[0].History.Stream.CurrentStateId
    manager=ResolveField(graph,fragment,'rFeatureIdManager','DcFeatureIdManager');ops={p.First:p.Second for p in MappingItems(manager.Fields['featureIdMap'])}
    parents={graph.Resolve(n.Fields['rParent']).ObjectId for n in (feature,target,operand)};assert len(parents)==1
    parent=graph.ResolveId(next(iter(parents)));assert parent.ClassName=='DcNodes' and graph.Resolve(parent.Fields['rParent'])==fragment and all(n in LinkedNodes(graph,parent,'children') for n in (feature,target,operand))
    for n in (feature,target,operand,radius,weight):
        assert n.Fields['isActive'] is True and n.Fields['isEdited'] is False and n.Fields['isEliminated'] is False
        update=ResolveField(graph,n,'rDynamicUpdateData','DynamicUpdateData');assert graph.Resolve(update.Fields['rOwnerNode'])==n
        if n in (feature,target,operand):assert update.Fields['isBodyOK'] is True and update.Fields['isPredecessorOK'] is True
    from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
    from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
    sketchbody=ResolveField(graph,sketch,'rSketch','MSketch');plane=ResolveField(graph,sketchbody,'UCS','CoordinateSystem')
    context=ExtrudeContext(component,fragment,sketch,sketchbody,plane,extrude,ResolveField(graph,extrude,'rAlongDistance','DcDoubleParameter'),ResolveField(graph,extrude,'rTaperAngle','DcDoubleParameter'),actual,body)
    shape=ReadCircle(graph,context);assert abs(shape.Geometry.radius/10-circle.MajorAxisCm[0])<1e-10 and shape.Geometry.center.x==shape.Geometry.center.y==0
    return dict(context=context,shape=shape,radius=circle.MajorAxisCm[0],height=height,fillet=amount,selected_edge=selected,operand=operand.ObjectId,tag=tag,body=actual,feature=feature,extrude=extrude,ops=ops,recipe=recipe.Value)
