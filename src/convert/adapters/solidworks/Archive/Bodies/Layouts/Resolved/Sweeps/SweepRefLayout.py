from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Sweeps.SweepRefTail import (
    KRefWrapperTailFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the shared selection tail ends with ordinary curve fields and one conditionally embedded section
KSweepCurve = (
    NativeField("Node", "f58", "moCompProfile_c"),
    *KRefWrapperTailFields,
    NativeField("Scalar", "fb0", "f64"),
    NativeField("Scalar", "fb8", "f64"),
    NativeField("Scalar", "has_fc8", "u8"),
    NativeField(
        "Branch",
        "has_fc8",
        BodyValue=(NativeField("Embed", "fc8", "sweep.embeddedSection19000"),),
        ModeValue="Nonzero",
    ),
    NativeField("Scalar", "fd0", "u32"),
    NativeField("Scalar", "fd4", "i32"),
    NativeField("Node", "fe0", "moContourChooser_c"),
    NativeField("Node", "fd8", "moCompSketchEntHandle_c"),
    NativeField("Node", "fe8", "moContourChooser_c"),
)


# a front path contact has one live curve owner and initially null guide and loft contacts
KSweepContact = (
    NativeField("Embed", "f50", "suObList"),
    NativeField("Scalar", "f90", "f64"),
    NativeField("Scalar", "f98", "i32"),
    NativeField("Node", "fa0", "moDisplayAngularDim_c"),
    NativeField("Scalar", "fa8", "f64"),
    NativeField("Scalar", "fb0", "i32"),
    NativeField("Scalar", "fb8", "i32"),
    NativeField("Scalar", "fc8", "i32"),
    NativeField("Scalar", "fcc", "i32"),
    NativeField("Node", "fe0", "moLoftSynchRef_c"),
    NativeField("Scalar", "f40", "u32"),
    NativeField("Scalar", "f44", "u32"),
    NativeField("Scalar", "f48", "u32"),
    NativeField("Scalar", "fc0", "f64"),
    NativeField("Node", "fe8", "moGeneralCurveRef_w"),
)
