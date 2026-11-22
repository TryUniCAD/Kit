from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the measured sweep ghost rows attach one feature to each typed transport identity
KSweepGhost = (
    NativeField("Scalar", "f08", "i32"),
    NativeField("Scalar", "f0c", "i32"),
    NativeField("Scalar", "f10", "i32"),
    NativeField("Scalar", "fc0", "i32"),
    NativeField(
        "Array",
        "fa0",
        "i32",
        BodyValue=(NativeField("Scalar", "v", "i32"),),
        CountValue="nb0",
        ModeValue="Positive",
    ),
    NativeField(
        "Present",
        "has_f50",
        "i32",
        BodyValue=(NativeField("Fail", "alternate SOLIDWORKS sweep ghost reference"),),
    ),
    NativeField(
        "Array",
        "ff0",
        "i32",
        CountValue="nf0",
        ModeValue="Positive",
        BodyValue=(NativeField("Fail", "populated SOLIDWORKS sweep ghost points"),),
    ),
)


# explicit sweep configuration leaves other populated ghost contexts unsupported
def UseSweepCfgMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000 or ContextValue.UsageValue.SchemaCalls:
        raise BodyUnsupported("unqualified SOLIDWORKS sweep configuration context")
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        "moGhostBodyObject_c.FUN_4bf05390": KSweepGhost,
    }
    ContextValue.FlagsValue["sweep_ghosts"] = 1
