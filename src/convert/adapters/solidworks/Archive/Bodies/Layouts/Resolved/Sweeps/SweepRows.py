from collections.abc import Mapping
from dataclasses import replace as ReplaceField

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# only the explicit sweep context opens the arc and reference rows used by its generated graph
def SweepRows(
    LayoutValues: Mapping[str, tuple[NativeField, ...]],
) -> dict[str, tuple[NativeField, ...]]:
    ArcRow = (
        NativeField("Scalar", "flags", "u16"),
        NativeField(
            "Branch",
            "flags",
            BodyValue=(NativeField("Fail", "alternate SOLIDWORKS sketch arc body"),),
            ModeValue="NotEquals",
        ),
        NativeField("Embed", "arc", "sk.sgArc.FUN_4c585150"),
    )
    DimRows = {
        "val_g1": (NativeField("Node", "d", "sgCircleDim"),),
        "log_g2": (NativeField("Embed", "d", "sk.sgLogG2Dim.FUN_4c58b970"),),
    }
    return {
        "sgSketch": tuple(
            (
                ReplaceField(FieldValue, BodyValue=ArcRow)
                if FieldValue.NameValue == "arcs"
                else FieldValue
            )
            for FieldValue in LayoutValues["sgSketch"]
        ),
        "rf.suObArray": tuple(
            ReplaceField(FieldValue, BodyValue=(NativeField("Node", "o"),))
            for FieldValue in LayoutValues["rf.suObArray"]
        ),
        "sk.sgSketch.FUN_4c5a0f00": tuple(
            ReplaceField(
                FieldValue,
                BodyValue=DimRows.get(FieldValue.NameValue, FieldValue.BodyValue),
            )
            for FieldValue in LayoutValues["sk.sgSketch.FUN_4c5a0f00"]
        ),
    }
