# local dimension handles use the native null component reference constructor before receiving their actual dimension pointer
def MakeLocalRef(VersionValue: int) -> dict[str, object]:
    FieldsValue: dict[str, object] = dict.fromkeys(
        (
            "f68",
            "f18",
            "f1c",
            "f20",
            "f30",
            "f70",
            "f84",
            "fa0",
            "f34",
            "f48",
            "has_fb0",
            "has_fb8",
            "has_fc0",
            "has_fc8",
            "has_fd0",
        ),
        0,
    )
    FieldsValue.update(dict.fromkeys(("f90", "f94", "f98", "f9c"), -1))
    FieldsValue.update({"f58": None, "f4c": VersionValue})
    return FieldsValue
