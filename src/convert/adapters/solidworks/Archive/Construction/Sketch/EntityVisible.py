# native visibility and absent inherited width must come from constructor rules rather than saved presentation rows
def EntityVisible() -> dict[str, object]:
    return {
        "f00": 0xFFFF,
        "f02": 0x1F,
        "f04": 3,
        "f08": {"f00": 0xFFFFFFFF, "f04": 0xFFFF, "f08": {"f06": -1, "f00": -1.0}},
    }
