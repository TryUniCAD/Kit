from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadTypedPrism import ReadTypedPrism


# cold prism refinements must bind their verified dimensions through existing feature and operation identities
def WithTypedNative(
    Model: NativeModel, Archive: SldprtArchive, *, Strict: bool = True
) -> NativeModel:
    if (
        ContainerMo(Archive.streams) != 19000
        or KPartitionStream in Archive.streams
        or len(Model.sketches) != 1
        or len(Model.operations) != 1
    ):
        return Model
    try:
        TypedValue = ReadTypedPrism(Model, Archive)
    except SldprtFormat as ErrorInfo:
        if Strict:
            raise
        return ReplaceValue(Model, diagnostics=(*Model.diagnostics, str(ErrorInfo)))
    if TypedValue is None:
        return Model
    Bound, Owner = TypedValue
    (Operation,) = Model.operations
    return ReplaceValue(
        Model,
        sketches=(Bound,),
        features=tuple(
            (
                BindDepth(Feature, Owner)
                if Feature.object_id == Operation.object_id
                else (
                    ReplaceValue(Feature, dimensions=Bound.dimensions)
                    if Bound.dimensions and Feature.object_id == Bound.object_id
                    else Feature
                )
            )
            for Feature in Model.features
        ),
        operations=(BindExtrude(Operation, Owner),),
    )
