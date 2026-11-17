from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KHeaderLayout,
    KHeaderScalars,
)


# shared external file fields must not acquire a second independently maintained wire layout
def MakeBodyFields(LayoutValue: KHeaderLayout) -> tuple[NativeField, ...]:
    FieldsValue: list[NativeField] = []
    for FieldName, TypeName in LayoutValue:
        ScalarName = KHeaderScalars.get(TypeName)
        if ScalarName is not None:
            FieldsValue.append(NativeField("Scalar", FieldName, ScalarName))
        elif TypeName == "text":
            FieldsValue.append(NativeField("Text", FieldName))
        else:
            FieldsValue.append(NativeField("Node", FieldName))
    return tuple(FieldsValue)
