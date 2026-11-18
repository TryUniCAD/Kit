from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTargetRef import (
    CheckTargetRef,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)


# direct native reference rows and expanded activity count belong to different scopes and must remain independently derived for every generated definition
def CheckTargetRows(TargetValue: TargetDocument) -> None:
    if TargetValue.RootValue.ClassValue.NameValue == "moPart_c":
        if (
            TargetValue.ReferenceValues
            or TargetValue.ChildTargets
            or TargetValue.ActivityValue
        ):
            raise ValueError("a generated part target cannot own assembly occurrences")
        return
    ListValue = RequireRecord(
        RequireRecord(TargetValue.RootValue.FieldsValue["f68"])["list"]
    )
    RowsValue = ReadRows(ListValue["items"])
    if (
        len(RowsValue) != len(TargetValue.ReferenceValues)
        or len(RowsValue) != len(TargetValue.ChildTargets)
        or len(RowsValue) != FieldInt(TargetValue.RootValue.FieldsValue, "f1560")
        or any(
            RowValue["o"] is not Reference
            for RowValue, Reference in zip(
                RowsValue, TargetValue.ReferenceValues, strict=True
            )
        )
    ):
        raise ValueError(
            "generated assembly target lost its complete direct reference list"
        )
    ActivityValue = sum(
        1 + ChildValue.ActivityValue for ChildValue in TargetValue.ChildTargets
    )
    if any(
        NumberValue != ActivityValue
        for NumberValue in (
            TargetValue.ActivityValue,
            FieldInt(TargetValue.CurrentConfig.FieldsValue, "f4b0"),
            FieldInt(TargetValue.HeaderValue.FieldsValue, "fc4"),
            FieldInt(TargetValue.TopHeader.FieldsValue, "fc4"),
        )
    ):
        raise ValueError("generated assembly activity must expand each placement path")
    for Reference, ChildValue in zip(
        TargetValue.ReferenceValues, TargetValue.ChildTargets, strict=True
    ):
        CheckTargetRef(TargetValue, Reference, ChildValue)
