from uuid import UUID as UuidValue

from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawFolders import (
    DrawFolders,
)
from convert.adapters.solidworks.Drawing.Construction.Model.MakeSheetBuild import (
    MakeSheetBuild,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckSheetBuild import (
    CheckSheetBuild,
)


# invalid neutral drawing settings must fail before construction can publish partially owned native objects
def CheckDrawBuild(BuildValue: DrawBuild) -> None:
    if (
        type(BuildValue) is not DrawBuild
        or type(BuildValue.FolderValue) is not DrawFolders
    ):
        raise TypeError(
            "drawing root construction requires explicit typed inputs and folder names"
        )
    if (
        type(BuildValue.StyleValue) is not StyleInput
        or type(BuildValue.UnitValue) is not UnitInput
    ):
        raise TypeError(
            "drawing root construction requires explicit style and unit inputs"
        )
    if (
        type(BuildValue.TargetValue) is not FeatureTarget
        or type(BuildValue.AutoLink) is not bool
    ):
        raise TypeError(
            "drawing root construction requires explicit target and dimension link preference"
        )
    if (
        type(BuildValue.BlockValue) is not UuidValue
        or BuildValue.BlockValue.version != 4
    ):
        raise ValueError(
            "drawing root block identity requires an independently allocated uuid4"
        )
    CheckDrawText(BuildValue.NameValue, True)
    FolderValue = BuildValue.FolderValue
    for NameValue in (
        FolderValue.CabinetName,
        FolderValue.BinderName,
        FolderValue.CommentsName,
        FolderValue.BlocksName,
        FolderValue.InkName,
        FolderValue.ReviewName,
    ):
        CheckDrawText(NameValue, False)
    _ = FeatureTime(BuildValue.CreatedAt)
    CheckSheetBuild(MakeSheetBuild(BuildValue, 4))
    if BuildValue.SheetValue.LengthUnit != BuildValue.UnitValue.LengthUnit:
        raise ValueError("drawing root sheet zones and document units must agree")
