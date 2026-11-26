from collections.abc import MutableMapping
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# origin insertion derives point usage and collection counters from the one retained logical constraint without manufacturing solved solver state
def WireOriginMut(
    SketchValue: ArchiveNode, PointValue: ArchiveNode, Constraint: ArchiveNode
) -> None:
    PointValue.FieldsValue.update({"pflags": 0x1E | 1, "fe4": 1, "f0c": 1})
    Relations = [{"d": Constraint.FieldsValue}]
    PointValue.FieldsValue["f20"] = len(Relations)
    PointRows = [{"kind": 0, "point": PointValue.FieldsValue}]
    SketchValue.FieldsValue.update(
        {"points": PointRows, "npoints": len(PointRows), "f188": 0}
    )
    Dimensions = CastValue(MutableMapping[str, object], SketchValue.FieldsValue["dims"])
    Dimensions.update({"log_g1": Relations, "nlog1": len(Relations)})
    Counters = CastValue(MutableMapping[str, object], SketchValue.FieldsValue["f140"])
    Counters["f08"] = len(PointRows) + 1
