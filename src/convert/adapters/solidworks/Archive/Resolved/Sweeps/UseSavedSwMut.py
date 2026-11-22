from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSweepCtxMut import (
    UseSweepCtxMut,
)


# saved history children and retained face choices require their actual current archive classes
def UseSavedSwMut(ContextValue: BodyContext) -> None:
    UseSweepCtxMut(ContextValue, SavedResult=True)
    HistoryName = "moHistoryFeatItemData_c"
    SideName = "moSweepSideSurfIdRep_c"
    DisplayName = "moDisplayItem_c.Serialize"
    ContextValue.LayoutsValue = dict(ContextValue.LayoutsValue) | {
        HistoryName: (
            NativeField("Base", "moNode_c"),
            NativeField("Node", "f48", "moCompFeature_c"),
        ),
        SideName: (
            NativeField("Base", "er.FUN_4bba8790"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f3c", "i32"),
        ),
        "moPartConfiguration_c.SerializeMBSMDataObjects": (
            NativeField(
                "Array",
                "fcd8",
                "u32",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Node", "o"),
                ),
                CountValue="n",
            ),
        ),
        DisplayName: tuple(
            (
                ReplaceValue(FieldValue, BodyValue=(NativeField("Scalar", "v", "i32"),))
                if FieldValue.NameValue == "f2b0"
                else FieldValue
            )
            for FieldValue in ContextValue.LayoutsValue[DisplayName]
        ),
    }
    ContextValue.SchemasValue = dict(ContextValue.SchemasValue) | {
        HistoryName: (1,),
        "moCompFeature_c": (1,),
        SideName: (1,),
    }
    ContextValue.VirtualValue = dict(ContextValue.VirtualValue) | {
        (HistoryName, 1000): None,
        (HistoryName, 1016): True,
        (HistoryName, 1208): "moNode_c.SerializeLWData",
        (HistoryName, 1216): None,
        ("moCompFeature_c", 1208): None,
        ("moCompFeature_c", 1216): None,
    }
