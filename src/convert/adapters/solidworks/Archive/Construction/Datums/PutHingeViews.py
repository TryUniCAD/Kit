from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import (
    MakeDefaultData,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# a finite document support grows by the measured fraction from the current stock extents
def PutHingeViews(
    SystemValue: PartSystem,
    BoundsValue: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> tuple[float, float]:
    Lower, Upper = BoundsValue
    if Lower[2] != 0.0 or SystemValue.RootValue.ClassValue.NameValue != "moPart_c":
        raise ValueError("finite datum sizing requires a joined Front-plane part")
    Limits = tuple(
        (RequireScalar(StartValue), RequireScalar(FinishValue))
        for StartValue, FinishValue in zip(Lower, Upper, strict=True)
    )
    Width, Height, DepthValue = (
        RequireScalar(FinishValue - StartValue) for StartValue, FinishValue in Limits
    )
    if min(Width, Height, DepthValue) <= 1e-7 or set(
        SystemValue.SystemValues.PlaneValues
    ) != {"x", "y", "z"}:
        raise ValueError(
            "finite hinge sizing requires positive stock and actual canonical supports"
        )
    CenterX, CenterY, CenterZ = (
        RequireScalar((StartValue + FinishValue) * 0.5)
        for StartValue, FinishValue in Limits
    )
    MarginX, MarginY, MarginZ = (
        Value * 0.5 + Value * 0.05 for Value in (Width, Height, DepthValue)
    )
    PlansValue = tuple(
        PlanHingeView(SystemValue, AxisValue, Center, Borders)
        for AxisValue, Center, Borders in (
            ("y", (CenterX, 0.0, CenterZ), (MarginX, -MarginX, MarginZ, -MarginZ)),
            ("x", (0.0, CenterY, CenterZ), (MarginZ, -MarginZ, MarginY, -MarginY)),
        )
    )
    for PlaneValue, DataValue, Display, Corner in PlansValue:
        DataValue.FieldsValue.update(Display)
        PlaneValue.FieldsValue["f6c0"] = Corner
    return CenterZ - (-MarginZ), CenterZ - MarginZ


# unrelated principal displays are never replaced by the new feature geometry
def PlanHingeView(
    SystemValue: PartSystem,
    AxisValue: str,
    Center: tuple[float, float, float],
    Borders: tuple[float, float, float, float],
) -> tuple[ArchiveNode, ArchiveNode, dict[str, object], dict[str, float]]:
    PlaneValue = RequireNode(
        SystemValue.SystemValues.PlaneValues[AxisValue], "moRefPlane_c"
    )
    DataValue = RequireNode(PlaneValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c")
    FrameValue = PrincipalFrame(AxisValue)
    if (
        sum(Value is PlaneValue for Value in SystemValue.FeatureValues) != 1
        or PlaneValue.FieldsValue.get("owner") is not SystemValue.RootValue
        or DataValue.FieldsValue != MakeDefaultData(AxisValue, FrameValue).FieldsValue
        or PlaneValue.FieldsValue.get("f6c0") != {"x": 0.0, "y": 0.0, "z": 0.0}
    ):
        raise ValueError(
            "finite hinge requires unchanged actual principal display owners"
        )
    Corner = tuple(
        Origin + (Borders[1] * AxisU + Borders[2] * AxisV)
        for Origin, AxisU, AxisV in zip(
            Center, FrameValue.AxisU, FrameValue.AxisV, strict=True
        )
    )
    Display: dict[str, object] = {
        "display_root": dict(zip("xyz", Center, strict=True)),
        **{f"b{Index}": Value for Index, Value in enumerate(Borders)},
    }
    return PlaneValue, DataValue, Display, dict(zip("xyz", Corner, strict=True))
