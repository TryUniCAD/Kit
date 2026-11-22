# invalid fresh mass properties must follow constructor state and never imply measured geometry or a populated body cache
def MakeMassProps() -> dict[str, object]:
    FieldsValue: dict[str, object] = dict.fromkeys(
        (
            "f20",
            "f28",
            "f30",
            "f10",
            "f08",
            "f18",
            "f38",
            "f40",
            "f48",
            "f50",
            "f60",
            "f58",
            "f00",
            "fc8",
            "fd0",
            "fd8",
        ),
        0.0,
    )
    FieldsValue.update(
        {
            "f1c0": 1,
            "f1c4": 0,
            "f1c8": 0,
            "f1cc": 0,
            "f1e0": 0,
            "f134": 0,
            "f138": 0,
            "f13c": 0,
            "f140": 0,
            "f148": "",
            "f150": "",
            "f1f0": 0,
            "f68": {"x": 1.0, "y": 0.0, "z": 0.0},
            "f80": {"x": 0.0, "y": 1.0, "z": 0.0},
            "f98": {"x": 0.0, "y": 0.0, "z": 1.0},
            "f15c": 1,
            "f128": 0,
        }
    )
    return FieldsValue
