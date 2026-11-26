# native entity visibility starts from the generic constructor before document styles apply
def MakeEntityVis() -> dict[str, object]:
    return {
        "f00": 0xFFFF,
        "f02": 0,
        "f04": 3,
        "f08": {"f00": 0xFFFFFFFF, "f04": 0xFFFF, "f08": {"f06": -1, "f00": -1.0}},
    }
