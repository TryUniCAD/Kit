from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)


# only the signed box profile should bypass the provisional rectangle and selected cut readers
def IsBoxAxisModel(Archive: SldprtArchive, ModelValue: NativeModel) -> bool:
    return (
        len(ModelValue.operations) == 1
        and ModelValue.operations[0].kind == "join"
        and ModelValue.operations[0].direction_code == 1
        and sum(
            Feature.class_name == "moRefAxis_c" or Feature.kind == "Axis"
            for Feature in ModelValue.features
        )
        == 3
        and IsCacheAbsent(Archive)
    )
