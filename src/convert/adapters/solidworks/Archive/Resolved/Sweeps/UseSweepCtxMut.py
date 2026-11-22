from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepLayout import (
    KSweepDataHead,
    KSweepDataTail,
    KSweepFeature,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepRefLayout import (
    KSweepContact,
    KSweepCurve,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# explicitly selected cold sweep emission installs only measured ordinary part schemas in its fresh context
def UseSweepCtxMut(ContextValue: BodyContext, *, SavedResult: bool = False) -> None:
    if (
        ContextValue.VersionValue != 19000
        or ContextValue.FlagsValue
        != {
            "model_compressed_stream": 1,
            "model_is_part": 1,
            "cmgr_f658": int(SavedResult),
        }
        or ContextValue.UsageValue.SchemaCalls
    ):
        raise BodyUnsupported("unsupported cold SOLIDWORKS standard sweep context")
    LayoutValues = {
        "moSweep_c": KSweepFeature,
        "moGeneralCurveRef_w": KSweepCurve,
        "moWireContact_c": KSweepContact,
        "moCompProfile_c": (NativeField("Base", "moCompFeature_c"),),
    }
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **LayoutValues,
        "sweep.data19000": (*KSweepDataHead, *KSweepDataTail),
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        **dict.fromkeys(LayoutValues, (1,)),
    }
    ContextValue.VirtualValue = {
        **ContextValue.VirtualValue,
        **{
            ("moSweep_c", SlotValue): ContextValue.VirtualValue["moICE_c", SlotValue]
            for SlotValue in (1000, 1016, 1208, 1216)
        },
    }
