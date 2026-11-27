from dataclasses import replace as ReplaceValue

from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import ProjectFeatures
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# radius and weight keep distinct editable roles on the actual modifying feature
def ProjectRimSteps(
    Graph: NativeGraph, Context: RimContext, Parameters: tuple[Parameter, ...]
) -> tuple[FeatureStep, ...]:
    Sketch, Extrude = ProjectFeatures(Graph, Context.Extrusion)
    BodyId = Context.Extrusion.BodyNode.Identity
    Fillet = FeatureStep(
        Context.Feature.Identity,
        TextValue(Context.Feature.Fields["featureUserName"])
        or TextValue(Context.Feature.Fields["featureBaseName"]),
        FeatureKind.KFillet,
        2,
        (Extrude.id,),
        parameter_ids=tuple(
            Value.id
            for Value in Parameters
            if Value.owner_id == Context.Feature.Identity
        ),
        definition=RadiusFillet(
            Context.SelectedRef.Identity,
            Context.RadiusParam.Identity,
            Context.WeightParam.Identity,
            Context.Feature.Fields["isTangentPropagation"] is True,
            Context.Feature.Fields["isRollingBallCorners"] is True,
        ),
        selection_ids=(Context.SelectedRef.Identity,),
        OutputBodyIds=(BodyId,),
    )
    return Sketch, ReplaceValue(Extrude, OutputBodyIds=(BodyId,)), Fillet
