from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepEntRules import (
    KSweepEntRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepRows import (
    SweepRows,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepViewRules import (
    KSweepViewRules,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSweepCtxMut import (
    UseSweepCtxMut,
)


# a saved sweep reads its signed display attachments and explicit side surface in its own context
def UseSavedSwMut(ContextValue: BodyContext) -> None:
    UseSweepCtxMut(ContextValue, SavedResult=True)
    SideName = "moSweepSideSurfIdRep_c"
    DisplayName = "moDisplayItem_c.Serialize"
    ContextValue.LayoutsValue = dict(ContextValue.LayoutsValue) | {
        **KSweepEntRules,
        **KSweepViewRules,
        **SweepRows(ContextValue.LayoutsValue),
        SideName: (
            NativeField("Base", "er.FUN_4bba8790"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f3c", "i32"),
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
    ContextValue.SchemasValue = dict(ContextValue.SchemasValue) | dict.fromkeys(
        (
            SideName,
            "sgArcHandle",
            "sgCircleDim",
            "sgEntHandle",
            "moDisplayRadialDim_c",
            "moSkDimHandleRadial_c",
        ),
        (1,),
    )
    ContextValue.VirtualValue = dict(ContextValue.VirtualValue) | {
        ("moDisplayRadialDim_c", 2216): 0,
        ("moDisplayRadialDim_c", 2264): 1,
        ("moDisplayRadialDim_c", 2680): 1,
    }
