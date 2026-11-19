from interchange.Enums.EnumUnits import UnitSystem
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Validation.CheckDrawing import CheckDrawing

from convert.adapters.solidworks.Drawing.Construction.Portable.ReadSheetRatio import (
    ReadSheetRatio,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.IsAnsiLandscapeSize import (
    IsAnsiLandscapeSize,
)


# the ordinary blank profile can represent a single authored layout without dropping other document domains
def NeedBlankDrawing(DocumentValue: CadDocument) -> DrawingData:
    DrawingValue = DocumentValue.DrawingValue
    if type(DrawingValue) is not DrawingData:
        raise ValueError("native blank drawing requires a typed drawing")
    if (
        DocumentValue.units != UnitSystem.KMeter
        or any(
            (
                DocumentValue.assembly,
                DocumentValue.brep,
                DocumentValue.configurations,
                DocumentValue.parameters,
                DocumentValue.support_planes,
                DocumentValue.sketches,
                DocumentValue.selections,
                DocumentValue.feature_timeline,
                DocumentValue.bodies,
                DocumentValue.meshes,
                DocumentValue.brep_payloads,
                DocumentValue.materials,
                DocumentValue.diagnostics,
                DocumentValue.capabilities,
                DocumentValue.source.attributes,
            )
        )
        or set(DocumentValue.metadata) - {"name"}
    ):
        raise ValueError("native blank drawing requires complete plain metre layout intent")
    Errors = CheckDrawing(DrawingValue)
    if Errors:
        raise ValueError("invalid native drawing layout: " + ", ".join(Errors))
    if len(DrawingValue.Sheets) != 1 or DrawingValue.ModelRefs:
        raise ValueError("native blank drawing requires one unlinked sheet")
    SheetValue = DrawingValue.Sheets[0]
    if SheetValue.Views or SheetValue.Notes or not IsAnsiLandscapeSize(SheetValue.SheetWidth, SheetValue.SheetHeight):
        raise ValueError("native blank drawing requires an empty landscape ANSI A sheet")
    _ = ReadSheetRatio(SheetValue.ScaleRatio)
    return DrawingValue
