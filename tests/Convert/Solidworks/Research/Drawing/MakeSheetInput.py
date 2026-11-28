from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue


# independent paper metadata must reach the writer without borrowing saved drawing fields
def MakeSheetInput(
    Label: str, ScaleNumerator: int, ScaleDenominator: int
) -> dict[str, object]:
    RepoRoot = FilePath(__file__).resolve().parents[5]
    Request = CastValue(
        dict[str, object],
        LoadJson((RepoRoot / "re/tooling/sw2026/DrawingBlankSpec01.json").read_bytes()),
    )
    Request["name"] = Label
    SheetValue = CastValue(dict[str, object], Request["sheet"])
    SheetValue.update(
        name=Label + " paper",
        custom_property_view="authored " + Label,
        scale_numerator=ScaleNumerator,
        scale_denominator=ScaleDenominator,
    )
    Request["output"] = {
        "path_name": "C:\\Users\\Public\\Documents\\KitOracle\\SdkSheet\\"
        + Label
        + ".SLDDRW",
        "saved_at": 1794700291,
    }
    return Request
