from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# provisional ownership cannot stand in for saved body results or chooser state
def CheckColdBodyState(
    NodesValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
) -> None:
    CutValue = NodesValue[2]
    for NodeValue in NodesValue:
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
        ):
            raise ValueError(
                "pre-rebuild solid has a result, consumed atom or chooser owner"
            )
    FieldsValue = CutValue.FieldsValue
    if FieldsValue.get("n494") != 0 or NativeRows(FieldsValue.get("f498")):
        raise ValueError("pre-rebuild cut has a result identity")


# extrude ends must also exclude a saved geometry owner
def CheckColdState(
    OwnersValue: tuple[ExtrudeOwner, ExtrudeOwner, ExtrudeOwner],
) -> None:
    First, Second, Cut = OwnersValue
    CheckColdBodyState((First.NodeValue, Second.NodeValue, Cut.NodeValue))
    if any(Value.EndValue.FieldsValue.get("f158") != 0 for Value in OwnersValue):
        raise ValueError(
            "pre-rebuild solid has a result, consumed atom or chooser owner"
        )
