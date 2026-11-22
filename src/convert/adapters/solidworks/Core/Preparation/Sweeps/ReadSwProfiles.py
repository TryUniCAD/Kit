from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.SweepFeature import SweepFeature
from interchange.geometry.Models.Sketch import Sketch


# the measured supports are named datum frames and must be the actual geometric owners of the two sketches
def CheckSwFrames(
    DocumentValue: CadDocument,
    SectionValue: Sketch,
    PathValue: Sketch,
    LabelsValue: SweepLabels,
) -> None:
    FixedValues = {Value.name: Value for Value in DocumentValue.support_planes}
    AxisValues = {LabelsValue.PlaneName: "z", "Right Plane": "x", "Top Plane": "y"}
    if (
        len(FixedValues) != len(DocumentValue.support_planes)
        or not {LabelsValue.PlaneName, "Right Plane"}
        <= FixedValues.keys()
        <= AxisValues.keys()
        or any(
            PlaneValue.support_selection_id is not None
            or PlaneValue.offset_parameter_id is not None
            or PlaneValue.attributes
            or ReadPrincAxis(PlaneValue.transform) != AxisValues[NameValue]
            for NameValue, PlaneValue in FixedValues.items()
        )
        or SectionValue.support_plane_id != FixedValues["Right Plane"].id
        or PathValue.support_plane_id != FixedValues[LabelsValue.PlaneName].id
    ):
        raise ValueError(
            "sweep sketches must use their exact Right section and Front path supports"
        )


# use the actual typed section and path references before consulting their dimensions or shape
def ReadSwProfiles(
    DocumentValue: CadDocument, LabelsValue: SweepLabels
) -> tuple[Sketch, Sketch]:
    StepValue = DocumentValue.feature_timeline[0]
    Definition = StepValue.definition
    if (
        type(Definition) is not SweepFeature
        or StepValue.kind != FeatureKind.KSweep
        or StepValue.operation != BooleanOp.KCreate
        or StepValue.name != LabelsValue.FeatureName
        or StepValue.sketch_id is None
        or StepValue.input_feature_ids
        or StepValue.parameter_ids
        or StepValue.selection_ids
        or StepValue.configuration_states
        or StepValue.suppressed
        or StepValue.attributes
    ):
        raise ValueError(
            "sweep requires its active typed first creator with distinct section and path"
        )
    SketchValues = {Value.id: Value for Value in DocumentValue.sketches}
    SectionValue = SketchValues[StepValue.sketch_id]
    PathValue = SketchValues[Definition.PathSketchId]
    if (SectionValue.name, PathValue.name) != (
        LabelsValue.SectionName,
        LabelsValue.SketchName,
    ):
        raise ValueError("sweep requires its canonical native sketch names")
    CheckSwFrames(DocumentValue, SectionValue, PathValue, LabelsValue)
    return SectionValue, PathValue
