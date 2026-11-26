from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native field order lets the read profile recover each concrete unit owner
KUnitFields = MappingProxyType(
    {
        "moAngleUserUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
        ),
        "moDensityUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fc0", "u16"),
            NativeField("Scalar", "fc4", "u16"),
            NativeField(
                "Present",
                "has_fb8",
                "u8",
                BodyValue=(NativeField("Node", "fb8"),),
                CountValue="fb8",
                ModeValue="ObjectPresence",
            ),
            NativeField("Scalar", "fc8", "u16"),
            NativeField("Scalar", "fcc", "i32"),
        ),
        "moEnergyUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
        ),
        "moFloatNumberUserUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moForceUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
        ),
        "moFrequencyUserUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moGravityUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moLengthUserUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
            NativeField("Node", "fb8"),
        ),
        "moLinearMotorUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moNumberUserUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moPowerUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
        ),
        "moRotaryMotorUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moSpringConstantUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moStressUnits_c": (NativeField("Base", "moUserUnits_c.Serialize"),),
        "moTimeUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
        ),
        "moUnitSysUnits_c": (
            NativeField("Base", "moUserUnits_c.Serialize"),
            NativeField("Scalar", "fb0", "u16"),
        ),
        "moUnitsTable_c": (NativeField("Base", "su_CObArray"),),
        "moUserUnits_c.Serialize": (
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Scalar", "f18", "f64"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f24", "i32"),
            NativeField("Scalar", "f30", "f64"),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Scalar", "f70", "i32"),
            NativeField("Scalar", "f74", "i32"),
            NativeField("Scalar", "f88", "f64"),
            NativeField("Scalar", "f7c", "u16"),
            NativeField("Scalar", "f08", "i32"),
        ),
    }
)
