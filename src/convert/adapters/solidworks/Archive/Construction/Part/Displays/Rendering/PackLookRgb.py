from typing import cast as CastValue


# documented packed color channels must be present with exact unsigned byte values
def PackLookRgb(ChannelsValue: tuple[int, ...]) -> int:
    if (
        type(CastValue(object, ChannelsValue)) is not tuple
        or len(ChannelsValue) != 3
        or any(
            type(CastValue(object, Value)) is not int or not 0 <= Value <= 255
            for Value in ChannelsValue
        )
    ):
        raise ValueError(
            "appearance color requires exactly three unsigned byte channels"
        )
    RedValue, GreenValue, BlueValue = ChannelsValue
    return RedValue | (GreenValue << 8) | (BlueValue << 16)
