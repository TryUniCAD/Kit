from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Motion.MotionKeyFields import KMotionKeyFields
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# each motion stream starts an independent concrete object map with its own manager
KMotionMgr = RuntimeClass("moAnimationManager_c", 1)


# the controller backreference must resolve to the existing study allocation
KMotionKey = RuntimeClass("moAnimKeyData_c", 1)


# the ordinary study graph tracks model body and controller framing without admitting solver or task objects
KMotionLayouts = {
    KMotionMgr.NameValue: (
        NativeField("Scalar", "f30", "i32"),
        NativeField(
            "Array",
            "studies",
            "u32",
            BodyValue=(NativeField("Node", "o", KMotionKey.NameValue),),
            CountValue="studyCount",
        ),
        NativeField("Scalar", "f50", "u32"),
    ),
    KMotionKey.NameValue: KMotionKeyFields,
    "MotionSolvers": (
        NativeField("Scalar", "selected", "i32"),
        NativeField("Scalar", "count", "i32"),
    ),
    "moAnimController_c": (
        NativeField("Node", "f08", KMotionKey.NameValue),
        NativeField("Scalar", "taskCount", "i32"),
        NativeField("Scalar", "f38", "i32"),
    ),
}


# motion bodies can consume only the two actual tagged classes in the measured default profile
KMotionSchemas = {
    ClassValue.NameValue: (ClassValue.SchemaValue,)
    for ClassValue in (KMotionMgr, KMotionKey)
}
