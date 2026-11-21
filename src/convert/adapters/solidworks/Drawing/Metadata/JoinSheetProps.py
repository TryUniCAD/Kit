from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Drawing.Metadata.SavedSheet import SavedSheet
from interchange.document.Models.Drawing.ValidMeasure import IsFiniteMeasure


# paper dimensions are published with the active sheet name and scale ratio
def JoinSheetProps(Props: dict[str, str], Sheet: SavedSheet) -> tuple[float, float]:
    if (
        Props["SW-Current Sheet"] != "1"
        or Props["SW-Total Sheets"] != "1"
        or Props["SW-Sheet Name"] != Sheet.NameValue
        or Props["SW-All Sheet Names"] != Sheet.NameValue + "@"
    ):
        raise SldprtFormat("drawing active sheet and keyword sheet disagree")
    Fields = Props["SW-All Sheet Format Data"].split("@")
    if len(Fields) != 9 or Fields[0] != Sheet.NameValue or Fields[-2:] != ["", ""]:
        raise SldprtFormat("drawing paper fields do not describe the expected sheet")
    Width = float(Fields[2])
    Height = float(Fields[3])
    Scale = (float(Fields[4]), float(Fields[5]))
    if Scale != Sheet.ScaleRatio or not all(
        IsFiniteMeasure(Value) and Value > 0 for Value in (Width, Height, *Scale)
    ):
        raise SldprtFormat("drawing paper dimensions or scale are invalid")
    return Width, Height
