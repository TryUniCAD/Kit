from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadWidthDepth import (
    ReadWidthDepth,
)
from convert.adapters.solidworks.Core.TypedResolved.ProjectTyped import ProjectTyped
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# a legacy equation may select a bounded decode attempt while only the linked graph authorizes projection
def TryWidthDepth(Model: NativeModel, Archive: SldprtArchive) -> NativeModel | None:
    if (
        len(Model.configurations) != 1
        or len(Model.sketches) != 1
        or len(Model.operations) != 1
        or Model.operations[0].kind != "join"
        or len(Model.equations) != 1
    ):
        return None
    (Equation,) = Model.equations
    if not Equation.lhs.startswith("D1@") or len(Equation.references) != 1:
        return None
    try:
        LinkValue = ReadNativeLink(
            Archive,
            Model.active_configuration_id,
            RelationConfig=Model.configurations[0].name,
        )
        Projected = ProjectTyped(Model, LinkValue)
        Relation = ReadWidthDepth(Projected, LinkValue)
    except (ValueError, TypeError, KeyError):
        return None
    return ReplaceValue(
        Projected,
        WidthDepth=Relation,
        TypedGraph={
            **Projected.TypedGraph,
            "local_width_depth_equation": {
                "relation": Relation.RelationOwner,
                "target": Relation.DepthOwner,
                "dependency": Relation.WidthOwner,
            },
        },
    )
