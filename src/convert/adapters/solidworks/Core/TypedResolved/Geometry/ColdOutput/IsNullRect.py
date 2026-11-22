from convert.adapters.solidworks.Container.ColdStreamRoles import (
    HasColdStreams,
    KColdChildStreams,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.Features.FeatureExtrude import ExtrudeEnd


# only the measured ordinary cold rectangle can interpret the three null list owners as absent geometry
def IsNullRect(
    Archive: SldprtArchive, Model: NativeModel, LinkValue: NativeLink
) -> bool:
    if (
        not HasColdStreams(Archive, KColdChildStreams)
        or Model.equations
        or len(Model.sketches) != 1
        or len(Model.operations) != 1
    ):
        return False
    LoopValue = Model.sketches[0].TypedLines
    if LoopValue is None or LoopValue.DimsValue is None:
        return False
    Fields = LinkValue.ConfigValue.RootValue.FieldsValue
    Operation = Model.operations[0]
    return (
        len(LoopValue.DimsValue.DriverValues) == 2
        and LoopValue.DimsValue.OriginValue is None
        and Operation.kind == "join"
        and Operation.extrusion_end == ExtrudeEnd.KBlind
        and Operation.direction_code == 0
        and all(
            NameValue in Fields and Fields[NameValue] is None
            for NameValue in ("f9d8", "fa48", "fa50")
        )
    )
