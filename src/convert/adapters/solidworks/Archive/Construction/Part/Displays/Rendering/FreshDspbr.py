from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.LookScalar import (
    LookScalar,
)


# the native basic shader initializer assigns every inactive or absent property in this nontextured profile
def FreshDspbr() -> dict[str, object]:
    FieldsValue: dict[str, object] = dict.fromkeys(
        (
            "f00",
            "f08",
            "f20",
            "f30",
            "f40",
            "f58",
            "fb0",
            "f118",
            "f120",
            "f140",
            "f148",
            "f150",
        ),
        "",
    )
    FieldsValue.update(
        dict.fromkeys(
            (
                "f28",
                "f2c",
                "f38",
                "f3c",
                "f48",
                "f4c",
                "f50",
                "f60",
                "f7c",
                "f80",
                "f90",
                "f94",
                "f98",
                "fa8",
                "fac",
                "fc4",
                "fd8",
                "fe8",
                "ff8",
                "ffc",
            ),
            0.0,
        )
    )
    FieldsValue.update(dict.fromkeys(("fc8", "fd0"), 0))
    FieldsValue.update(dict.fromkeys(("f54", "f128", "f158", "f15c"), 1.0))
    for PrefixValue in ("f10", "f64", "f70", "f84", "f9c", "fb8", "fdc", "fec", "f108"):
        FieldsValue.update(
            {
                f"{PrefixValue}_{IndexValue}": 0.0 if PrefixValue == "fec" else 1.0
                for IndexValue in range(3)
            }
        )
    FieldsValue.update(
        fcc=1,
        fd4=1.5,
        f100=LookScalar(0.4, 0.0, 1.0),
        f104=2.0,
        f12c=LookScalar(0.02, 0.0, 1.0),
    )
    return FieldsValue
