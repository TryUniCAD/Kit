from convert.adapters.solidworks.Drawing.Construction.Indexes.DrawViewIndex import (
    DrawViewIndex,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.DrawSheetIndex import (
    DrawSheetIndex,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.MakeInfoProps import (
    MakeInfoProps,
)


# linked layout properties preserve the actual selected model path configuration and view instead of the blank sheet sentinel
def MakeViewProps(SheetValue: DrawSheetIndex, ViewValue: DrawViewIndex) -> bytes:
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
    ModelValue = "@".join(
        (
            "1:",
            "",
            ViewValue.ConfigName,
            str(ViewValue.ConfigId),
            str(ViewValue.PathValue),
            ViewValue.NameValue,
            SheetValue.NameValue,
        )
    )
    return MakeInfoProps(
        (
            ("SW-Current Sheet", "1"),
            ("SW-Total Sheets", "1"),
            ("SW-Sheet Name", SheetValue.NameValue),
            ("SW-All Sheet Names", SheetValue.NameValue + "@"),
            ("SW-Config-Model-View-Sheet-List", ModelValue),
            ("SW-All Sheet Format Data", ExpandedValue),
        )
    )
