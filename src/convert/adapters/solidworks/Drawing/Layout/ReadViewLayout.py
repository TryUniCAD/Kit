from math import hypot as HypotValue, isclose as IsClose

from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Drawing.Metadata.SavedSheet import SavedSheet
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.geometry.Models.VectorPlane import PlaneVector


# the native header provides the outline and a provisional position until definition is joined
def ReadViewLayout(
    Header: NativeHeader, Sheet: SavedSheet, ModelId: str
) -> DrawingView:
    Bounds = Header.Bounds
    if Bounds is None:
        raise SldprtFormat("drawing view has no native bounds")
    (
        CenterX,
        CenterY,
        CenterZ,
        UpperX,
        UpperY,
        UpperZ,
        LowerX,
        LowerY,
        LowerZ,
        Radius,
    ) = Bounds
    if (
        LowerX >= UpperX
        or LowerY >= UpperY
        or (CenterZ, UpperZ, LowerZ) != (0.0, 0.0, 0.0)
        or not IsClose(CenterX, (LowerX + UpperX) / 2, abs_tol=1e-12)
        or not IsClose(CenterY, (LowerY + UpperY) / 2, abs_tol=1e-12)
        or not IsClose(
            Radius, HypotValue(UpperX - LowerX, UpperY - LowerY) / 2, abs_tol=1e-12
        )
    ):
        raise SldprtFormat("drawing header bounds do not describe a single sheet view")
    return DrawingView(
        EntityId=f"slddrw:sheet:{Sheet.IdValue}:view:1",
        EntityName=Sheet.ViewName,
        ModelRefId=ModelId,
        ConfigurationName=Sheet.ConfigName,
        PositionValue=PlaneVector(CenterX, CenterY),
        OutlineValues=(LowerX, LowerY, UpperX, UpperY),
    )
