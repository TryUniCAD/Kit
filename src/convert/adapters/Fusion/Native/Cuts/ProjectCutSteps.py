from dataclasses import replace as CopyData
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import ProjectFeatures
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep


# the modifying step consumes the original body and its own profile through live distance controls
def ProjectCutSteps(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext]
) -> tuple[FeatureStep, ...]:
    Stock = ProjectFeatures(Graph, Contexts[0])
    ToolCut = ProjectFeatures(Graph, Contexts[1])
    Definition = ToolCut[-1].definition
    if not isinstance(Definition, DistanceExtrude):
        raise ValueError("Native cut has no live distance definition")
    CutStep = CopyData(
        ToolCut[-1],
        order=3,
        operation=BooleanOp.KCutOperation,
        input_feature_ids=(Stock[-1].id, ToolCut[0].id),
        definition=DistanceCut(Definition, (Contexts[0].BodyNode.Identity,)),
    )
    return (*Stock, CopyData(ToolCut[0], order=2), CutStep)
