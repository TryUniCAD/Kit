from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.adapters.Fusion.Native.Cuts.CheckCutScopes import CheckCutScopes
from convert.adapters.Fusion.Native.Cuts.CheckCutRefs import CheckCutRefs
from convert.adapters.Fusion.Native.Cuts.CheckCutTarget import CheckCutTarget
from convert.adapters.Fusion.Native.Cuts.ReadCutOps import ReadCutOps
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    RequireFields,
    ResolveField,
    EmptyFields,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Policy.CheckClasses import CheckClasses
from convert.adapters.Fusion.Native.Policy.CheckAssembly import CheckAssembly
from convert.adapters.Fusion.Native.Policy.CheckContainers import CheckContainers
from convert.adapters.Fusion.Native.Policy.CheckPlacement import CheckPlacement
from convert.adapters.Fusion.Native.Policy.CheckFeature import CheckFeature
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion


# multiple contexts retain all original qualification checks with explicit union coverage
def CheckCutGraph(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext], AssetId: str
) -> FeatureTag:
    EmptyFields(Contexts[0].BodyNode, ("faceVisualMaterialByAttrTagID",))
    CheckClasses(Graph, Additional=("DRBody", "ASMRecipe"))
    if any(
        Group.Opaque
        for NodeValue in Graph.Nodes.values()
        if NodeValue.SegmentId == 0
        for Group in NodeValue.Groups
    ):
        raise ValueError("Native cut has opaque semantic members")
    CheckAssembly(Graph, Contexts[0])
    CheckContainers(Graph, Contexts[0], tuple(Context.Sketch for Context in Contexts))
    for Index, Context in enumerate(Contexts):
        CheckPlacement(Graph, Context, Scoped=True)
        EmptyFields(
            ResolveField(
                Graph, Context.SketchFeature, "rProgenitorTable", "ProgenitorTable"
            ),
            ("ProgenitorTagVec",),
        )
        CheckFeature(Graph, Context.SketchFeature)
        CheckFeature(Graph, Context.Extrude)
        CheckExtrusion(Graph, Context, Operation=4 if Index == 0 else 2)
    CheckCutScopes(Graph, Contexts, AssetId)
    CheckCutRefs(Graph, Contexts)
    BodyTag = CheckCutTarget(Graph, Contexts, ReadCutOps(Graph, Contexts))
    for NodeValue in (Contexts[0].Component, Contexts[0].BodyNode):
        if any(
            Value != -1.0
            for Value in ObjectFields(NodeValue.Fields["massProperties"]).values()
        ):
            raise ValueError("Native cut has custom mass property overrides")
    RequireFields(Contexts[0].DcBody, {"isEliminated": False})
    return BodyTag
