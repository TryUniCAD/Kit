from datetime import datetime as DateTime


# the database creation instant uses UnQLite's native zero-based month and two-second granularity
def EncodeUnqliteClock(Created: DateTime) -> int:
    if Created.tzinfo is not None or not 1980 <= Created.year <= 2107:
        raise ValueError("UnQLite creation requires an explicit DOS-range wall clock")
    return (
        (Created.year - 1980) << 25
        | (Created.month - 1) << 21
        | Created.day << 16
        | Created.hour << 11
        | Created.minute << 5
        | Created.second // 2
    )


# a decoded clock uses the same month basis without reading model header time fields
def DecodeUnqliteClock(ClockValue: int) -> DateTime:
    if type(ClockValue) is not int or not 0 <= ClockValue <= 0xFFFFFFFF:
        raise ValueError("invalid UnQLite clock word")
    return DateTime(
        1980 + (ClockValue >> 25),
        ((ClockValue >> 21) & 15) + 1,
        (ClockValue >> 16) & 31,
        (ClockValue >> 11) & 31,
        (ClockValue >> 5) & 63,
        (ClockValue & 31) * 2,
    )
