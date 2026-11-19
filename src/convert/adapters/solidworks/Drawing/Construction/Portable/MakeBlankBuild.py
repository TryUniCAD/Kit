from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import (
    DrawDocOptions,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.ReadSheetRatio import (
    ReadSheetRatio,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.IsAnsiLandscapeSize import (
    IsAnsiLandscapeSize,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetInput import SheetInput
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet


# blank construction must consume genuine portable sheet semantics and reject content the selected constructor cannot represent
def MakeBlankBuild(DrawingValue: DrawingData, Options: DrawDocOptions) -> DrawBuild:
    if type(DrawingValue) is not DrawingData or type(Options) is not DrawDocOptions:
        raise TypeError(
            "neutral blank drawing requires typed drawing semantics and native options"
        )
    if len(DrawingValue.Sheets) != 1 or DrawingValue.ModelRefs:
        raise ValueError(
            "neutral blank drawing requires one sheet and no model references"
        )
    SheetValue = DrawingValue.Sheets[0]
    if (
        type(SheetValue) is not DrawingSheet
        or SheetValue.Views
        or type(SheetValue.EntityId) is not str
        or not SheetValue.EntityId
        or type(DrawingValue.ActiveSheetId) is not str
        or DrawingValue.ActiveSheetId != SheetValue.EntityId
        or not IsAnsiLandscapeSize(SheetValue.SheetWidth, SheetValue.SheetHeight)
    ):
        raise ValueError(
            "neutral blank drawing has an unsupported active sheet paper or view content"
        )
    Numerator, Denominator = ReadSheetRatio(SheetValue.ScaleRatio)
    return DrawBuild(
        Options.NameValue,
        SheetInput(
            SheetValue.EntityName,
            "ansi-a-landscape",
            Numerator,
            Denominator,
            Options.UnitValue.LengthUnit,
            Options.PropertyView,
        ),
        Options.SheetNames,
        Options.FolderValue,
        Options.StyleValue,
        Options.UnitValue,
        Options.TargetValue,
        Options.CreatedAt,
        Options.BlockValue,
        Options.AutoLink,
    )
