from dataclasses import replace
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from Policy import SelectContext

def corrupt(model,mode):
    graph=BuildGraph(model);context,rim,data=SelectContext(graph)
    radius=graph.Resolve(data.Fields['radiusValue']);param=graph.Resolve(radius.Fields['parameter'])
    selected=graph.Resolve(data.Fields['connectedEdgeRef']);(brep,)=tuple(graph.Resolve(x) for x in selected.Fields['dataRefs'].Items)
    if mode=='role':return ChangeField(model,param.ObjectId,'name','AlongDistance')
    if mode=='unit':return ChangeField(model,param.ObjectId,'unit','deg')
    if mode=='expression':return ChangeField(model,param.ObjectId,'expression','1 + 1')
    if mode=='owner':return ChangeField(model,radius.ObjectId,'rrOwnerFeature',LocalRef(context.Extrude.ObjectId))
    if mode=='reciprocal':return ChangeField(model,param.ObjectId,'dcParameter',LocalRef(context.Along.ObjectId))
    if mode=='allocator':return ChangeField(model,radius.ObjectId,'rparamId',context.Along.Fields['rparamId'])
    if mode=='selected_owner':return ChangeField(model,brep.ObjectId,'rParentFeature',LocalRef(context.Extrude.ObjectId))
    if mode=='selected_alias':return ChangeField(model,data.ObjectId,'connectedEdgeRef',context.Extrude.Fields['profileDataRefs'].Items[0])
    if mode=='selected_body':return ChangeField(model,brep.ObjectId,'refBodies',ValueSeries(()))
    if mode=='radius_alias':return ChangeField(model,data.ObjectId,'radiusValue',data.Fields['tangencyWeight'])
    if mode=='variable_mode':return ChangeField(model,data.ObjectId,'bConstantRadius',False)
    if mode=='scope_mode':return ChangeField(model,rim.ObjectId,'scopeOption',1)
    if mode=='history_join':return ChangeField(model,rim.ObjectId,'startModelHS',context.Extrude.Fields['startModelHS'])
    if mode=='dynamic_owner':
        dynamic=graph.Resolve(radius.Fields['rDynamicUpdateData'])
        return ChangeField(model,dynamic.ObjectId,'rOwnerNode',LocalRef(context.Along.ObjectId))
    if mode=='cached_radius':
        (cache,)=tuple(graph.Resolve(x) for x in brep.Fields['caches'].Items)
        geom=cache.Fields['rCachedGeometry']
        return ChangeField(model,cache.ObjectId,'rCachedGeometry',replace(geom,Fields=tuple(replace(f,Value=f.Value*2) if f.FieldName=='radius' else f for f in geom.Fields)))
    if mode=='recipe_face':
        recipe=graph.Resolve(brep.Fields['rRecipe']);saved=recipe.Fields['m_Recipe'].Value
        payload=replace(saved.Payload,AdjacentFaces=tuple(replace(f,PrimaryTagIndex=0) for f in saved.Payload.AdjacentFaces))
        return ChangeField(model,recipe.ObjectId,'m_Recipe',OptionalValue(replace(saved,Payload=payload)))
    raise ValueError(mode)
