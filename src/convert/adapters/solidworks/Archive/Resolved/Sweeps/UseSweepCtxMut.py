from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepEntRules import (
    KSweepEntRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepLayout import (
    KSweepDataHead,
    KSweepDataTail,
    KSweepFeature,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepRefLayout import (
    KSweepContact,
    KSweepCurve,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepRows import (
    SweepRows,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepViewRules import (
    KSweepViewRules,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# explicitly selected cold sweep emission installs only measured ordinary part schemas in its fresh context
def UseSweepCtxMut(ContextValue: BodyContext) -> None:
    if (
        ContextValue.VersionValue != 19000
        or ContextValue.FlagsValue
        != {
            "model_compressed_stream": 1,
            "model_is_part": 1,
            "cmgr_f658": 0,
        }
        or ContextValue.UsageValue.SchemaCalls
    ):
        raise BodyUnsupported("unsupported cold SOLIDWORKS standard sweep context")
    LayoutValues = {
        "moSweep_c": KSweepFeature,
        "moGeneralCurveRef_w": KSweepCurve,
        "moWireContact_c": KSweepContact,
        "moCompProfile_c": (NativeField("Base", "moCompFeature_c"),),
        "moNotesAreaFtrFolder_c": (NativeField("Base", "moFtrFolder_c"),),
    }
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **LayoutValues,
        **KSweepEntRules,
        **KSweepViewRules,
        **SweepRows(ContextValue.LayoutsValue),
        "sweep.data19000": (*KSweepDataHead, *KSweepDataTail),
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        **dict.fromkeys(LayoutValues, (1,)),
        **dict.fromkeys(
            (
                "sgArcHandle",
                "sgCircleDim",
                "sgEntHandle",
                "moDisplayRadialDim_c",
                "moSkDimHandleRadial_c",
            ),
            (1,),
        ),
    }
    ContextValue.VirtualValue = {
        **ContextValue.VirtualValue,
        **{
            ("moSweep_c", SlotValue): ContextValue.VirtualValue[
                "moExtrusion_c", SlotValue
            ]
            for SlotValue in (1000, 1016, 1208, 1216)
        },
        **{
            ("moNotesAreaFtrFolder_c", SlotValue): ContextValue.VirtualValue[
                "moDocsFolder_c", SlotValue
            ]
            for SlotValue in (1000, 1016, 1208, 1216)
        },
        ("moNotesAreaFtrFolder_c", 2624): True,
        ("moDisplayRadialDim_c", 2216): 0,
        ("moDisplayRadialDim_c", 2264): 1,
        ("moDisplayRadialDim_c", 2680): 1,
    }
