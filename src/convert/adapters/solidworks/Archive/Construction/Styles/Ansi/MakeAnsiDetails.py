from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.ReadFields import (
    ReadFields,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetAnnotationsMut import (
    SetAnnoStyleMut,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetDimensionsMut import (
    SetDimStyleMut,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetHeightMut import (
    SetHeightMut,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetLabelsMut import (
    SetLabelsMut,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.SetTablesMut import (
    SetTablesMut,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeDetails import (
    MakeDetails,
)


# ansi construction needs fresh standard one ownership before applying the native standard zero defaults
def MakeAnsiDetails(StyleValue: StyleInput) -> dict[str, object]:
    if type(CastValue(object, StyleValue)) is not StyleInput:
        raise TypeError("ANSI construction requires an explicit style input")
    if (
        type(CastValue(object, StyleValue.StandardValue)) is not int
        or StyleValue.StandardValue != 0
    ):
        raise ValueError("ANSI construction requires actual standard zero")
    FieldsValue = MakeDetails(
        StandardValue=1,
        FontName=StyleValue.FontName,
        LineStyleName=StyleValue.LineStyleName,
        LanguageId=StyleValue.LanguageId,
        PrintWidths=StyleValue.PrintWidths,
        ExclusionNames=StyleValue.ExclusionNames,
        TaskLabels=StyleValue.TaskLabels,
        CutlistExpressions=StyleValue.CutlistExpressions,
    )
    FieldsValue.update({"f10": 0, "f08": 0.00635, "f28": 0.00254, "f24": 2, "f34": 0})
    FieldsValue["f20"] = CastValue(int, FieldsValue["f20"]) & ~0x100000
    SetHeightMut(FieldsValue, "f90")
    SetDimStyleMut(ReadFields(FieldsValue, "f13b0"))
    SetAnnoStyleMut(ReadFields(FieldsValue, "f1f18"))
    SetLabelsMut(ReadFields(FieldsValue, "f2750"))
    SetTablesMut(ReadFields(FieldsValue, "f2410"))
    return FieldsValue
