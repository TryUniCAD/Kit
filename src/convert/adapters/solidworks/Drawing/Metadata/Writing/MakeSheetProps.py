from convert.adapters.solidworks.Drawing.Metadata.Writing.DrawSheetIndex import (
    DrawSheetIndex,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.MakeInfoProps import (
    MakeInfoProps,
)


# the six drawing layout properties must share actual sheet values and deterministic fresh property ids without copied native rows
def MakeSheetProps(SheetValue: DrawSheetIndex) -> bytes:
    if type(SheetValue) is not DrawSheetIndex:
        raise TypeError(
            "drawing property construction requires its actual typed sheet index"
        )
    PaperValues = (
        0,
        SheetValue.WidthValue,
        SheetValue.HeightValue,
        SheetValue.Numerator,
        SheetValue.Denominator,
        0,
    )
    ExpandedValue = "@".join(
        (SheetValue.NameValue, *(format(Value, ".6f") for Value in PaperValues), "", "")
    )
    return MakeInfoProps(
        (
            ("SW-Current Sheet", "1"),
            ("SW-Total Sheets", "1"),
            ("SW-Sheet Name", SheetValue.NameValue),
            ("SW-All Sheet Names", SheetValue.NameValue + "@"),
            ("SW-Config-Model-View-Sheet-List", "0:"),
            ("SW-All Sheet Format Data", ExpandedValue),
        )
    )
