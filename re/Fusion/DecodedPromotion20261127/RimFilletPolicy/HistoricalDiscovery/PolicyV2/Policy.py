from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField, SameNodes, RequireFields, EmptyFields, SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, ObjectFields, TextValue, PointCoords, CheckIdentity
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures
from convert.adapters.Fusion.Native.Policy.CheckClasses import CheckClasses
from convert.adapters.Fusion.Native.Policy.CheckAssembly import CheckAssembly
from convert.adapters.Fusion.Native.Policy.CheckContainers import CheckContainers
from convert.adapters.Fusion.Native.Policy.CheckPlacement import CheckPlacement
from convert.adapters.Fusion.Native.Policy.CheckFeature import CheckFeature
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion

def SelectContext(graph):
    component=graph.OneClass('FusionComponent')
    fragment,features=OrderedFeatures(graph,component)
    assert tuple(n.ClassName for n in features)==('DcSketch','DcExtrudeFeature','DcFilletEdgeFeature')
    SameNodes(features,tuple(n for n in graph.Nodes.values() if n.SegmentId==0 and graph.HasBase(n,'DcFeature')))
    sketch_feature,extrude,rim=features
    sketch=ResolveField(graph,sketch_feature,'rSketch','MSketch')
    plane=ResolveField(graph,sketch,'UCS','CoordinateSystem')
    along=ResolveField(graph,extrude,'rAlongDistance','DcDoubleParameter')
    taper=ResolveField(graph,extrude,'rTaperAngle','DcDoubleParameter')
    (dcbody,)=LinkedNodes(graph,extrude,'dcBodies')
    assert dcbody.ClassName=='DcBody'
    body=ResolveField(graph,dcbody,'rBody','Body')
    context=ExtrudeContext(component,fragment,sketch_feature,sketch,plane,extrude,along,taper,body,dcbody)
    (data,)=LinkedNodes(graph,rim,'filletEdgeData')
    assert data.ClassName=='DcFilletEdgeData'
    return context,rim,data

def ExistingChecks(model,graph,context,rim,data):
    extra=('DcFilletEdgeFeature','DcFilletEdgeData','BrepRef','ASMRecipe','BrepProgenitor','ETCachedCircleArc')
    steps={}
    for name,call in (
        ('classes',lambda:CheckClasses(graph,Additional=extra)),
        ('assembly',lambda:CheckAssembly(graph,context)),
        ('containers',lambda:CheckContainers(graph,context)),
        ('placement',lambda:CheckPlacement(graph,context)),
        ('sketch_feature',lambda:CheckFeature(graph,context.SketchFeature)),
        ('extrude_feature',lambda:CheckFeature(graph,context.Extrude)),
        ('rim_feature',lambda:CheckFeature(graph,rim)),
        ('extrusion',lambda:CheckExtrusion(graph,context)),
        ('scope',lambda:CheckScopes(graph,context,model.Asset.AssetId)),
        ('scene',lambda:CheckSceneRefs(graph,model.Graphics)),
        ('material',lambda:ReadMaterial(graph,context,model)),
        ('circle',lambda:ReadCircle(graph,context)),
        ('region',lambda:CheckRegion(graph,context,(ReadCircle(graph,context).CurveNode,),model.Asset.AssetId)),
    ):
        try:
            call()
            steps[name]=dict(passed=True)
        except Exception as error:
            steps[name]=dict(passed=False,error=type(error).__name__+': '+str(error))
    return steps
