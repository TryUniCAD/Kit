# native features inherit visual settings through constructor enums rather than copied appearances
def FeatureVisible() -> dict[str, object]:
    return {
        "f00": 65535,
        "f02": 0,
        "f04": 3,
        "f08": {
            "f00": 4294967295,
            "f04": 65535,
            "f08": {"f06": -1, "f00": -1.0},
        },
    }
