from collections.abc import Mapping

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# neutral history must prove this selected mode creates the sole first solid
def CheckScopeRoot(
    StepValue: FeatureStep,
    History: tuple[FeatureStep, ...],
    Bodies: tuple[DesignBody, ...],
) -> None:
    if (
        StepValue.kind != FeatureKind.KExtrusion
        or StepValue.operation != BooleanOp.KCreate
        or StepValue.suppressed
        or StepValue.configuration_states
        or StepValue.sketch_id is None
        or StepValue.selection_ids
        or len(Bodies) != 1
        or Bodies[0].final_feature_id != StepValue.id
    ):
        raise ValueError("first creator scope requires one active root solid extrusion")
    for PriorStep in History:
        if PriorStep.order < StepValue.order and (
            PriorStep.operation is not None
            or PriorStep.kind not in (FeatureKind.KReference, FeatureKind.KNative)
        ):
            raise ValueError("first creator scope has an earlier solid operation")
        if PriorStep.id in StepValue.input_feature_ids and (
            PriorStep.kind != FeatureKind.KReference
            or PriorStep.sketch_id != StepValue.sketch_id
        ):
            raise ValueError("first creator scope inputs must own its profile sketch")
    if len(StepValue.input_feature_ids) > 1:
        raise ValueError("first creator scope requires one profile dependency")


# the stored positive extent must still be the value of its sole live owner
def CheckScopeDepth(
    StepValue: FeatureStep,
    Definition: ScopedExtrude,
    Parameters: Mapping[str, Parameter],
) -> None:
    if len(StepValue.parameter_ids) != 1:
        raise ValueError("first creator scope requires one live depth driver")
    Driver = Parameters.get(StepValue.parameter_ids[0])
    if (
        Driver is None
        or Driver.owner_id != StepValue.id
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or Driver.value != Definition.Extrusion.length
    ):
        raise ValueError("first creator scope requires its actual live depth owner")


# a first creator can specify only the forward normal of its profile plane
def CheckScopePlane(
    StepValue: FeatureStep,
    Definition: ScopedExtrude,
    Sketches: Mapping[str, Sketch],
    Frames: Mapping[str, SupportPlane],
) -> None:
    Profile = Sketches.get(StepValue.sketch_id or "")
    Support = None if Profile is None else Frames.get(Profile.support_plane_id or "")
    Direction = Definition.Extrusion.direction
    if Support is None or (
        Direction is not None and Direction != Support.transform.z_axis
    ):
        raise ValueError(
            "first creator scope requires its profile plane's forward direction"
        )


# the new scope mode needs timeline validation only when it is explicitly present
def FirstScopeErrs(
    History: tuple[FeatureStep, ...],
    Bodies: tuple[DesignBody, ...],
    Parameters: Mapping[str, Parameter],
    Sketches: Mapping[str, Sketch],
    Frames: Mapping[str, SupportPlane],
) -> tuple[str, ...]:
    Errors: list[str] = []
    for StepValue in History:
        Definition = StepValue.definition
        if (
            isinstance(Definition, ScopedExtrude)
            and Definition.ScopeMode == "first_creator"
        ):
            try:
                CheckScopeRoot(StepValue, History, Bodies)
                CheckScopeDepth(StepValue, Definition, Parameters)
                CheckScopePlane(StepValue, Definition, Sketches, Frames)
            except ValueError as ErrorInfo:
                Errors.append(f"extrusion {StepValue.id} is invalid: {ErrorInfo}")
    return tuple(Errors)
