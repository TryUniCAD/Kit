from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# provisional ownership cannot stand in for saved body results or chooser state
def CheckColdState(
    OwnersValue: tuple[ExtrudeOwner, ExtrudeOwner, ExtrudeOwner],
) -> None:
    CutValue = OwnersValue[2].NodeValue
    for OwnerValue in OwnersValue:
        NodeValue = OwnerValue.NodeValue
        FieldsValue = NodeValue.FieldsValue
        Absent: tuple[str, ...] = ("f4a8", "f4b0", "f4c0", "f530")
        if NodeValue is CutValue:
            Absent += ("f528",)
        if (
            any(
                FieldsValue.get("has_" + FieldName) != 0
                or FieldsValue.get(FieldName) is not None
                for FieldName in Absent
            )
            or FieldsValue.get("f538") is not None
            or OwnerValue.EndValue.FieldsValue.get("f158") != 0
        ):
            raise ValueError(
                "pre-rebuild solid has a result, consumed atom or chooser owner"
            )
    FieldsValue = CutValue.FieldsValue
    if FieldsValue.get("n494") != 0 or NativeRows(FieldsValue.get("f498")):
        raise ValueError("pre-rebuild cut has a result identity")
