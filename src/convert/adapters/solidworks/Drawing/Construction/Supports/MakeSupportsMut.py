from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeSheetBuild import (
    MakeSheetBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.ViewProjection import (
    ViewProjection,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeSheetDetail import (
    MakeSheetDetail,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames
from convert.adapters.solidworks.Drawing.Construction.Supports.MakeViewPair import (
    MakeViewPair,
)
from convert.adapters.solidworks.Drawing.Construction.Supports.RegisterDrawMut import (
    RegisterDrawMut,
)
from convert.adapters.solidworks.Drawing.Construction.Supports.ViewNames import (
    ViewNames,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# the view detail precedes view allocation and each plane handle precedes its own plane id in the native support registration sequence
def MakeSupportsMut(
    ViewValue: ArchiveNode,
    GraphValue: DrawRootGraph,
    BuildValue: DrawBuild,
    Projection: ViewProjection,
    NamesValue: ViewNames,
) -> None:
    if type(NamesValue) is not ViewNames or ViewValue.FieldsValue["f08"] != -1:
        raise ValueError(
            "drawing view support construction requires a fresh unregistered view and typed names"
        )
    for NameValue in (
        NamesValue.DetailName,
        NamesValue.SheetPlane,
        NamesValue.SheetProfile,
        NamesValue.ModelPlane,
        NamesValue.ModelProfile,
    ):
        CheckDrawText(NameValue, False)
    Allocator = GraphValue.Allocator
    SeedValue = ReplaceValue(
        MakeSheetBuild(BuildValue, Allocator.NextValue - 3),
        NamesValue=SheetNames(
            NamesValue.SheetPlane, NamesValue.SheetProfile, NamesValue.DetailName
        ),
    )
    DetailValue = MakeSheetDetail(ViewValue, SeedValue)
    RegisterDrawMut(DetailValue, Allocator)
    DetailValue.FieldsValue["f0c"] = 0
    _ = Allocator.AllocateMut(ViewValue)
    SheetPair = MakeViewPair(
        ViewValue,
        GraphValue.ModelValue,
        SeedValue,
        dict(NeedConceptMap(Projection.FieldsValue["f778"])),
        Projection.SheetFrame,
        Allocator,
        None,
    )
    ModelSeed = ReplaceValue(
        SeedValue,
        NamesValue=SheetNames(
            NamesValue.ModelPlane, NamesValue.ModelProfile, NamesValue.DetailName
        ),
    )
    ModelPair = MakeViewPair(
        ViewValue,
        GraphValue.ModelValue,
        ModelSeed,
        dict(NeedConceptMap(Projection.FieldsValue["f648"])),
        Projection.ModelFrame,
        Allocator,
        Projection.AxisValues,
    )
    Children = (DetailValue, *SheetPair, *ModelPair)
    ViewValue.FieldsValue.update(
        {
            "f60": {
                "list": {
                    "n": len(Children),
                    "items": tuple({"o": NodeValue} for NodeValue in Children),
                },
                "tail": 0,
            },
            "f630": DetailValue,
            "has_f7c8": 1,
            "f7c8": SheetPair[1],
            "has_fde0": 1,
            "fde0": ModelPair[1],
        }
    )
