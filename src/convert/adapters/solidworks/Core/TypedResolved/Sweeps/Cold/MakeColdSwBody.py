from convert.Geometry.SweptTube.BuildQuarter import BuildQuarter
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwBody import (
    MakeSwMeasure,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep


# a cold sweep derives its boundary from the verified profiles and the feature owns the body
def MakeColdSwBody(
    StateValue: SwReadGraph, FeatureValue: FeatureStep, IncludeBrep: bool
) -> tuple[DesignBody, BrepModel | None]:
    BodyValue = MakeSwMeasure(StateValue, FeatureValue)
    if not IncludeBrep:
        return BodyValue, None
    return BodyValue, BuildQuarter(
        BodyValue.id,
        StateValue.SectionValue.CurveValue.Radius * 1000.0,
        StateValue.PathValue.CurveValue.Radius * 1000.0,
    )
