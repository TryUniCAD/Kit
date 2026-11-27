from interchange.document.Validation.BoundDefErrors import GetBoundErrors
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.document.Validation.GetDistanceErrs import GetDistanceErrs
from typing import Mapping as TypeMap

from interchange.document.Validation.AngleRevValidate import GetAngleRevErrs
from interchange.document.Validation.PlaneAxisValidate import GetAxisErrors
from interchange.document.Validation.PlaneRevValidate import GetPlaneRevErrs
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.document.Validation.Fillets.GetFilletErrs import GetFilletErrs
from interchange.Features.Axes.AxisExtentConfig import AxisConfigView
from interchange.Features.Axes.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# the primary length can be omitted only when the saved termination is through all
def GetExtrudeErrs(
    StepValue: FeatureStep, Definition: ExtrudeFeature
) -> tuple[str, ...]:
    if Definition.length is None and Definition.end_condition != ExtrudeEnd.THROUGH_ALL:
        return (f"extrusion {StepValue.id} requires a primary length",)
    return ()


# a scoped definition carries design body references in addition to the actual extrusion
def GetScopeErrors(
    StepValue: FeatureStep, Definition: ScopedExtrude, BodyIds: set[str]
) -> tuple[str, ...]:
    ScopeIds = set(Definition.SelectedBodyIds) | set(Definition.AffectedBodyIds)
    Missing = sorted(ScopeIds - BodyIds)
    if Missing:
        return (f"scoped extrusion {StepValue.id} references missing bodies {Missing}",)
    return GetExtrudeErrs(StepValue, Definition.Extrusion)


# supported editable definitions require checks beyond generic dependency validation
def GetDefErrors(
    StepValue: FeatureStep,
    IdentitySets: TypeMap[str, set[str]],
    Selections: TypeMap[str, Selection],
    Params: TypeMap[str, Parameter],
    Frames: TypeMap[str, SupportPlane],
    Sketches: TypeMap[str, Sketch],
    AxisView: AxisConfigView | None = None,
) -> tuple[str, ...]:
    Definition = StepValue.definition
    if isinstance(Definition, ScopedExtrude):
        return GetScopeErrors(StepValue, Definition, IdentitySets["bodies"])
    if isinstance(Definition, (PlaneAxis, BoundPlaneAxis)):
        return GetAxisErrors(StepValue, Selections, Frames, Params, AxisView)
    if isinstance(Definition, PlaneRevolve):
        return GetPlaneRevErrs(
            StepValue, Definition, Selections, IdentitySets["support_planes"]
        )
    if isinstance(Definition, AngularRevolve):
        return GetAngleRevErrs(StepValue, Definition, Selections, Params)
    if isinstance(Definition, RadiusFillet):
        return GetFilletErrs(StepValue, Definition, Params, Selections)
    if isinstance(Definition, (DistanceExtrude, DistanceCut)):
        return GetDistanceErrs(
            StepValue,
            Definition,
            IdentitySets["sketches"],
            IdentitySets["bodies"],
            Params,
        )
    if isinstance(Definition, ExtrudeFeature):
        return GetExtrudeErrs(StepValue, Definition)
    return GetBoundErrors(StepValue, Params, Selections, Frames, Sketches)
