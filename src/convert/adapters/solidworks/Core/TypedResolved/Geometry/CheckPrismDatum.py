from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Display.DatumDisplay import (
    DatumDisplay,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a principal frame cannot substitute for an attached clipped or differently defined datum with coincident cached coordinates
def CheckPrismDatum(
    DatumValue: ArchiveNode, DisplayValue: DatumDisplay | None = None
) -> None:
    Fields = RequireNative(
        DatumValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    ).FieldsValue
    if any(
        Fields.get(FieldName) is not None for FieldName in ("f48", "f68", "f70", "f78")
    ):
        raise ValueError("cache free prism datum has additional geometric owners")
    if any(Fields.get(FieldName) != 0 for FieldName in ("f50", "old_e5", "f60", "f64")):
        raise ValueError("cache free prism datum has unsupported border or mode state")
    if Fields.get("f54") != -4 or Fields.get("f58") != -4 or Fields.get("f5c") != 1:
        raise ValueError("cache free prism datum has alternate constructor state")
    Borders = tuple(
        RequireScalar(Fields.get(NameValue)) for NameValue in ("b0", "b1", "b2", "b3")
    )
    Center = ReadVector(Fields.get("display_root"))
    if DisplayValue is not None:
        if not (
            DisplayValue.IsClose(Borders, DisplayValue.BordersValue)
            and DisplayValue.IsClose(Center, DisplayValue.CenterValue)
        ):
            raise ValueError("cache free axis datum display disagrees with its stock")
        return
    if any(Borders):
        raise ValueError("cache free prism datum has unsupported border or mode state")
    if any(Center):
        raise ValueError("cache free prism datum has a displaced display origin")
