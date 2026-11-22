from dataclasses import replace as ReplaceValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.BindEqOwners import (
    BindEqOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadWidthDepth import (
    ReadWidthDepth,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# a recognized local equation must survive the physical typed graph before strict semantic inspection
def ReadEqPart(
    Model: NativeModel, Archive: SldprtArchive, Settings: ReadOptions
) -> NativeModel:
    if (
        Settings.extract_raw_brep
        or len(Model.configurations) != 1
        or len(Model.sketches) != 1
        or len(Model.operations) != 1
        or Model.operations[0].kind != "join"
        or len(Model.equations) != 1
        or ContainerMo(Archive.streams) != 19000
        or not IsCacheAbsent(Archive)
    ):
        return Model
    (Equation,) = Model.equations
    if Equation.lhs != f"D1@{Model.operations[0].name}" or Equation.references != (
        f"D1@{Model.sketches[0].name}",
    ):
        return Model
    try:
        LinkValue = ReadNativeLink(
            Archive,
            Model.active_configuration_id,
            RelationConfig=Model.configurations[0].name,
        )
        Projected, BossValue = BindEqOwners(Model, LinkValue)
        Relation = ReadWidthDepth(Projected, LinkValue, BossValue)
        if Equation.source != Relation.SourceText:
            raise ValueError(
                "local equation lookup disagrees with its physical enabled row"
            )
    except (ValueError, TypeError, KeyError) as Error:
        Message = f"local SOLIDWORKS width-depth history is unresolved: {Error}"
        if Settings.strict:
            raise SldprtFormatError(Message) from Error
        return ReplaceValue(Model, diagnostics=(*Model.diagnostics, Message))
    return ReplaceValue(Projected, WidthDepth=Relation)
