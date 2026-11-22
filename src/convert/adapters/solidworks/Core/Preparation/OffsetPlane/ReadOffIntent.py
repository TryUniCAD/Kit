from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetFrame import (
    OffsetFrame,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffBaseFrame import (
    OffBaseFrame,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import RefPlaneFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter


# a true selected offset requires one signed placement and the same positive editable magnitude
def ReadOffIntent(
    StepValue: FeatureStep,
    BaseValue: SupportPlane,
    CarrierValue: SupportPlane,
    Driver: Parameter,
) -> OffsetInput:
    Definition = StepValue.definition
    if (
        type(Definition) is not RefPlaneFeature
        or StepValue.kind != FeatureKind.KReference
        or StepValue.suppressed
        or StepValue.input_feature_ids
        or StepValue.selection_ids
        or StepValue.configuration_states
        or StepValue.attributes
        or StepValue.operation is not None
        or StepValue.sketch_id is not None
        or StepValue.parameter_ids != (Driver.id,)
        or Definition.support_plane_id != CarrierValue.id
        or Definition.reference_plane_id != BaseValue.id
        or CarrierValue.name != StepValue.name
        or CarrierValue.offset_parameter_id != Driver.id
        or CarrierValue.support_selection_id is not None
        or CarrierValue.attributes
    ):
        raise ValueError(
            "offset definition requires its actual local base carrier and driver"
        )
    Offset = Definition.offset
    Amount = RequireScalar(Offset.value)
    if (
        Driver.name != "D1"
        or Driver.owner_id != StepValue.id
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or Driver.attributes
        or Driver.value.kind != ValueKind.KLength
        or Offset.kind != ValueKind.KLength
        or Offset.unit not in ("mm", "m")
        or Driver.value.unit != Offset.unit
        or RequireScalar(Driver.value.value) != abs(Amount)
    ):
        raise ValueError("offset definition and its positive driving D1 disagree")
    AmountMm = Amount if Offset.unit == "mm" else Amount / 0.001
    Frame = OffsetFrame(OffBaseFrame(ReadPrincAxis(BaseValue.transform)), AmountMm)
    if CarrierValue.transform != Transform(
        SpaceVector(*Frame.OriginValue),
        SpaceVector(*Frame.AxisU),
        SpaceVector(*Frame.AxisV),
        SpaceVector(*Frame.NormalValue),
    ):
        raise ValueError("offset placement contradicts its base and signed distance")
    return OffsetInput(StepValue.name, ReadLength(Driver.value), Amount < 0, 19000)
