# profile display visibility has a distinct native constructor from ordinary sketch entity presentation
def MakeOriginVis() -> dict[str, object]:
    return {
        "f00": 0xFFFF,
        "f02": 0,
        "f04": 3,
        "f08": {"f00": 0xFFFFFFFF, "f04": 0, "f08": {"f06": 0, "f00": -1.0}},
    }
