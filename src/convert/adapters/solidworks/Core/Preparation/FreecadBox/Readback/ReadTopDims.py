from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# the portable sketch dimension preserves its live metre value and the actual sketch owner
def ReadTopLength(
    Driver: Parameter, NameValue: str, ProfileId: str, SketchId: str
) -> Parameter:
    NativeValue = Driver.attributes.get("native_value")
    OwnerValue = NativeRecord(Driver.attributes.get("typed_archive_owner"))
    if (
        Driver.name != NameValue
        or Driver.owner_id != ProfileId
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or Driver.value.kind != ValueKind.KLength
        or Driver.value.unit != "mm"
        or Driver.attributes.get("native_unit") != "m"
        or OwnerValue.get("class") != "moLengthParameter_c"
        or OwnerValue.get("value_field") != "f58"
        or type(NativeValue) is not float
        or not IsFinite(NativeValue)
        or NativeValue <= 0.0
        or Driver.value.value != NativeValue * 1000.0
    ):
        raise ValueError("SOLIDWORKS Top corner lacks its owned sketch length")
    return ReplaceValue(
        Driver,
        owner_id=SketchId,
        value=ReplaceValue(Driver.value, unit="m", value=NativeValue),
        attributes=FreezeMapping(),
        provenance=None,
    )


# the signed rectangle projection preserves precisely the two sketch drivers and the independent boss depth
def ReadTopDims(
    Parameters: tuple[Parameter, ...],
    BossValue: FeatureStep,
    ProfileValue: FeatureStep,
    SketchId: str,
) -> tuple[FeatureStep, tuple[Parameter, ...]]:
    DriverMap = {Value.id: Value for Value in Parameters}
    IdsValue = (*ProfileValue.parameter_ids, *BossValue.parameter_ids)
    if (
        len(Parameters) != 3
        or len(ProfileValue.parameter_ids) != 2
        or len(BossValue.parameter_ids) != 1
        or set(IdsValue) != DriverMap.keys()
    ):
        raise ValueError("SOLIDWORKS Top corner requires three distinct owned drivers")
    LengthId, WidthId, DepthId = IdsValue
    DepthValue = DriverMap[DepthId]
    if (
        DepthValue.name != "Height"
        or DepthValue.owner_id != BossValue.id
        or DepthValue.role != ParameterRole.KDriving
        or DepthValue.expression is not None
    ):
        raise ValueError("SOLIDWORKS Top corner lacks its independent height")
    FeatureValue, HeightValue = ReadColdBoss(BossValue, DepthValue)
    return FeatureValue, (
        ReadTopLength(DriverMap[LengthId], "Length", ProfileValue.id, SketchId),
        ReadTopLength(DriverMap[WidthId], "Width", ProfileValue.id, SketchId),
        HeightValue,
    )
