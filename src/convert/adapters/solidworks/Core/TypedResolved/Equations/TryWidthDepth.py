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
    if len(Equation.references) != 1 or (
        not Equation.lhs.startswith("D1@")
        and (
            Equation.lhs.count("@") != 1
            or Equation.rhs != f'"{Equation.references[0]}" / 2'
        )
    ):
        return None
    try:
        LinkValue = ReadNativeLink(
            Archive,
            Model.active_configuration_id,
            RelationConfig=Model.configurations[0].name,
        )
        Projected = ProjectTyped(Model, LinkValue)
        Relation = ReadWidthDepth(Projected, LinkValue, Archive)
    except (ValueError, TypeError, KeyError):
        return None
    Dormant = Relation.DormantValue
    if Dormant is not None and (
        Equation.source != Relation.SourceText or Equation.configuration_id != 0
    ):
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
                **(
                    {
                        "dormant_depth": {
                            "name": Dormant.DepthValue.name,
                            "value_mm": Dormant.DepthValue.value_mm,
                            "owner": Dormant.DepthValue.TypedOwner,
                        }
                    }
                    if Dormant is not None
                    else {}
                ),
            },
        },
    )
