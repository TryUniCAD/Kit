from Policy import *
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems, MappingItems
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ProjectParam
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from interchange.Records.RecordParameter import Parameter, ParameterValue, Expression
from interchange.Enums.EnumValues import ValueKind
from math import isfinite, pi
from re import fullmatch

def Parameters(graph,context,rim,data):
    table=ResolveField(graph,context.Component,'rParameterTable','ParameterTable')
    nodes=LinkedNodes(graph,table,'children')
    SameNodes(nodes,graph.ByClass('Parameter'))
    catalog={TextValue(n.Fields['userName']):n for n in nodes}
    assert len(catalog)==len(nodes) and '' not in catalog
    radius=ResolveField(graph,data,'radiusValue','DcDoubleParameter')
    weight=ResolveField(graph,data,'tangencyWeight','DcDoubleParameter')
    bindings=(context.Along,context.Taper,weight,radius)
    SameNodes(bindings,graph.ByClass('DcDoubleParameter'))
    identifiers=tuple(IntegerValue(n.Fields['rparamId']) for n in bindings)
    assert len(set(identifiers))==4 and min(identifiers)>0 and max(identifiers)<=IntegerValue(context.Fragment.Fields['nextParamId'])
    projected=[]
    parameters=[]
    for binding,owner,role,unit in zip(bindings,(context.Extrude,context.Extrude,rim,rim),('AlongDistance','TaperAngle','TangencyWeight','Radius'),('mm','deg','','mm'),strict=True):
        RequireFields(binding,{'isActive':True,'isEdited':False,'isEliminated':False,'rGroupRepresentative':None})
        assert graph.Resolve(binding.Fields['rrOwnerFeature'])==owner
        assert graph.Resolve(binding.Fields['rParentFeature'])==owner
        assert graph.Resolve(binding.Fields['rParent'])==ResolveField(graph,context.Fragment,'rNodes','DcNodes')
        param=ResolveField(graph,binding,'parameter','Parameter')
        assert graph.Resolve(param.Fields['dcParameter'])==binding
        assert graph.Resolve(param.Fields['rParent'])==table
        RequireFields(param,{'name':role,'unit':unit,'isUserDefined':False,'isDirty':False,'isDriven':False,'isOrphan':False,'isExternal':False,'expressionType':0,'booleanValue':False,'textValue':'','rClientObject':None,'group':None})
        SameNumbers((NumberValue(param.Fields['value']),),(NumberValue(binding.Fields['value']),))
        if unit:
            projected.append(ProjectParam(param,catalog,owner))
        else:
            literal=TextValue(param.Fields['expression'])
            assert fullmatch(r'\s*[+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\s*',literal)
            assert float(literal)==NumberValue(param.Fields['value'])==1
            projected.append(Parameter(param.Identity,param.Fields['userName'],ParameterValue(1,ValueKind.KNumber,''),expression=Expression(literal,language='fusion'),owner_id=owner.Identity,attributes={'comment':param.Fields['comment'],'native_name':role}))
        parameters.append(param)
    users=tuple(n for n in nodes if n not in parameters)
    for param in users:
        assert graph.Resolve(param.Fields['rParent'])==table
        RequireFields(param,{'dcParameter':None,'isUserDefined':True,'rClientObject':None,'group':None})
        projected.append(ProjectParam(param,catalog,None))
    SameNodes((*parameters,*users),nodes)
    assert NumberValue(context.Along.Fields['value'])>0 and NumberValue(context.Taper.Fields['value'])==0
    assert 0<NumberValue(radius.Fields['value'])<ReadCircle(graph,context).Geometry.radius/10
    return tuple(projected)

def Selection(graph,context,rim,data,asset_id):
    RequireFields(rim,{'filletType':0,'isRollingBallCorners':True,'isSheetMetalFillet':False,'isTangentPropagation':True,'rParamRadius':None,'scopeOption':0,'topologyOption':0})
    RequireFields(data,{**{k:False for k in ('bAsymmetric','bChord','bFlip','bG2Blend','bRuleFillet')},'bConstantRadius':True,'bIsComputeChain':True,'scopeOption':0,'topologyOption':0,'selSetIndex':0,**{k:None for k in ('chordLen','curveChainStartPoint','edgeOffset1Value','edgeOffset2Value','rFaceRef','rFeatureRef','rFullRoundRef','rRuleRef')}})
    EmptyFields(data,('edgeSequence','midPointParams','pointParams','pointRadii'))
    connected=ResolveField(graph,data,'connectedEdgeRef','ModelDataRef')
    assert LinkedNodes(graph,rim,'targetDataRefs')==(connected,)
    (brep,)=LinkedNodes(graph,connected,'dataRefs')
    assert brep.ClassName=='BrepRef'
    SameNodes(LinkedNodes(graph,rim,'childNodes'),(connected,brep,graph.Resolve(data.Fields['radiusValue']),graph.Resolve(data.Fields['tangencyWeight'])))
    for node,tracking in ((connected,8),(brep,8)):
        RequireFields(node,{'trackingType':tracking,'updateFlag':0,'xRefAssetHash':0,'isActive':True,'isEdited':False,'isEliminated':False,'rGroupRepresentative':None})
        assert graph.Resolve(node.Fields['rParentFeature'])==rim
        assert graph.Resolve(node.Fields['rParent'])==ResolveField(graph,context.Fragment,'rNodes','DcNodes')
        assert NumberValue(node.Fields['computeTime'])>=0
        CheckFeatureStatus(graph,node)
    RequireFields(connected,{'rOwnerOccurrence':None,'rTargetOccurrence':None})
    EmptyFields(connected,('refBodies',))
    RequireFields(brep,{'bAlwaysRecompute':False,'bDirReversedAgainstRefEntity':False})
    assert LinkedNodes(graph,brep,'refBodies')==(context.DcBody,)
    recipe=ResolveField(graph,brep,'rRecipe','ASMRecipe')
    value=recipe.Fields['m_Recipe']
    assert isinstance(value,OptionalValue) and isinstance(value.Value,RecipeValue)
    value=value.Value
    assert value.Version==3 and not value.LwdTags and len(value.Tags)==3 and all(len(t)==1 for t in value.Tags)
    assert isinstance(value.Payload,EdgeRecipe)
    payload=value.Payload
    assert payload.PrimaryTagIndex==0 and payload.LwdTagIndex==-1 and payload.ReferenceFaceIndex==-1
    assert tuple(f.PrimaryTagIndex for f in payload.AdjacentFaces)==(1,2) and all(f.LwdTagIndex==-1 for f in payload.AdjacentFaces)
    assert len(payload.AdjacentVertices)==1
    vertex=payload.AdjacentVertices[0]
    assert vertex.PrimaryTagIndex==-1 and vertex.AdjacentFaces==payload.AdjacentFaces
    assert len(vertex.AdjacentEdges)==1
    edge=vertex.AdjacentEdges[0]
    assert edge==EdgeRecipe(0,-1,(),(),-1)
    assert len(vertex.UvOrders)==1 and vertex.UvOrders[0].KeyValue==0
    uv=vertex.UvOrders[0].Value
    assert (uv.FaceVertexCount,uv.UOrder,uv.ULowerOrder,uv.UUpperOrder,uv.VOrder,uv.VLowerOrder,uv.VUpperOrder)==(2,2,2,2,1,0,1)
    assert all(t.SecondaryId==0 and t.ApproachId==0 and len(t.OperationIds)==1 for tags in value.Tags for t in tags)
    assert len({t.OperationIds for tags in value.Tags for t in tags})==1
    progen=graph.OneClass('BrepProgenitor')
    RequireFields(progen,{'rParent':None})
    duplicate=ResolveField(graph,progen,'m_brepRecipe','ASMRecipe')
    assert duplicate.Fields['m_Recipe']==recipe.Fields['m_Recipe']
    SameNodes((recipe,duplicate),graph.ByClass('ASMRecipe'))
    profiles=LinkedNodes(graph,context.Extrude,'profileDataRefs')
    SameNodes((*profiles,connected),graph.ByClass('ModelDataRef'))
    CheckRegion(graph,context,(ReadCircle(graph,context).CurveNode,),asset_id,Scoped=True)
    return brep,value

def CheckFeatureStatus(graph,node):
    status=ResolveField(graph,node,'status','DcStatus')
    RequireFields(status,{'statusType':0})
    EmptyFields(status,('statusCodes',))
