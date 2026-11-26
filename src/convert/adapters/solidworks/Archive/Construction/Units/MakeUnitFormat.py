from typing import cast as CastValue


# each native unit owns fresh formatting state with precision supplied by the document rather than a saved row
def MakeUnitFormat(DecimalPlaces: int) -> dict[str, object]:
    if (
        type(CastValue(object, DecimalPlaces)) is not int
        or not 0 <= DecimalPlaces <= 16
    ):
        raise ValueError(
            "native unit precision must be an integer from zero through sixteen"
        )
    return {
        "f08": 0,
        "f0c": DecimalPlaces,
        "f10": 1,
        "f18": 0.01,
        "f20": 10,
        "f24": 1,
        "f28": 1,
        "f30": 0.78539816339745,
        "f6c": 0,
        "f70": 1,
        "f74": 1,
        "f7c": 0,
        "f88": 0.0,
    }
