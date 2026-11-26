from convert.adapters.solidworks.Archive.Construction.Styles.MakeDimStyle import (
    MakeDimStyle,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeDimDefs(*, FontName: str, LineStyleName: str) -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        "f8": 0.001016,
        "f10": 0.003302,
        "f18": 0.00635,
        "f20": 0.001,
        "f28": 0.001,
        "f30": 0.005,
        "f38": 0.01,
        "f40": 0.003175,
        "f48": 0.001524,
        "f50": 0.00635,
        "f58": -25.0,
        "f60": 0,
        "f64": 0,
        "f68": 1,
        "f6c": 1,
        "f70": 20,
        "f74": 0,
        "f78": 0.0,
        "f80": 0.0,
        "f88": 0,
        "f8c": 0,
        "f90": 0.01,
        "f98": 0.006,
        "fa0": 0.26179938779915,
        "fa8": 1,
        "fb0": 1.0,
        "fb8": 0,
        "fbc": 1,
        "fc0": 1,
        "fc4": 1,
        "fcc": 1,
        "fd0": 1,
        "fd4": 1,
        "fd8": 8369,
    }
    for FieldName, KindValue in (
        ("fe0", "linear"),
        ("f1f0", "angle"),
        ("f2f8", "arc_length"),
        ("f3f8", "radial"),
        ("f500", "hole"),
        ("f608", "ordinate"),
        ("f718", "angular_ordinate"),
        ("f830", "chamfer"),
        ("f960", "diameter"),
        ("fa68", "base"),
    ):
        FieldsValue[FieldName] = MakeDimStyle(
            KindValue=KindValue, FontName=FontName, LineStyleName=LineStyleName
        )
    return FieldsValue
