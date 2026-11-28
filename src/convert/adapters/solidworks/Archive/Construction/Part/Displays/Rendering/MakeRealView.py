from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.ClassicLook import (
    ClassicLook,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.LookScalar import (
    LookScalar,
)


# the classic render body uses the independently mapped native defaults and explicit stock color parameters
def MakeRealView(
    InputValue: ClassicLook, IdValue: int, LocatorValue: str, PackedColor: int
) -> dict[str, object]:
    if (
        type(InputValue) is not ClassicLook
        or InputValue.ShaderName != "defaultplastic"
        or type(CastValue(object, InputValue.MappingMode)) is not int
        or InputValue.MappingMode != 3
        or type(CastValue(object, InputValue.ColorForm)) is not int
        or InputValue.ColorForm != 1
        or type(CastValue(object, InputValue.DoubleSided)) is not bool
        or type(CastValue(object, InputValue.BumpIsNormal)) is not bool
    ):
        raise ValueError(
            "part rendering requires the ordinary nontextured classic shader"
        )
    FieldsValue: dict[str, object] = dict.fromkeys(
        (
            "f1c",
            "f20",
            "f24",
            "f2c",
            "f30",
            "f34",
            "f38",
            "f48",
            "f5c",
            "f60",
            "f90",
            "f94",
            "f98",
            "fa8",
            "fac",
            "fb0",
            "fb8",
            "fbc",
            "fc0",
        ),
        0.0,
    )
    FieldsValue.update(dict.fromkeys(("f4c", "f50", "f54", "fdc", "fe0"), -1.0))
    FieldsValue.update(
        dict.fromkeys(("f18", "f28", "f3c", "f78", "fa4", "fb4", "fd0", "fd8"), 1.0)
    )
    FieldsValue.update(
        f00=IdValue & 0xFFFFFFFF,
        f04=IdValue >> 32,
        f08=InputValue.ShaderName,
        f10=InputValue.MappingMode,
        f14=PackedColor,
        f40=InputValue.ColorForm,
        f44=LookScalar(InputValue.Reflectivity, 0.0, 1.0),
        f58=0,
        f68=LocatorValue,
        f70=0xFFFFFF,
        f74=LookScalar(InputValue.Roughness, 0.0, 1.0),
        f80="",
        f88=LookScalar(InputValue.BumpStrength, 0.0, 1e30),
        f8c=LookScalar(InputValue.Displacement, 0.0, 1e30),
        f9c=(int(InputValue.DoubleSided) << 6) | (int(InputValue.BumpIsNormal) << 8),
        fa0=0,
        fd4=90.0,
        fe8="",
    )
    return FieldsValue
