from struct import pack as PackValues

from tests.Convert.Solidworks.CmgrHeader.MakeMgrDesc import MakeMgrDesc


# signed and unsigned words must remain independent of the native body layout
def MakeMgrInput() -> dict[str, object]:
    return {
        "saved_at": 3_001_234_567,
        "sort_word": -21,
        "rows": [
            {
                "f08": 1,
                "f10": "P\u03bb",
                "f30": -25,
                "f38": 4_000_000_012,
                "f18": "Stock",
                "f34": -1,
                "f40": 1,
                "f20": "Note",
                "f28": "",
                "f44": -3,
                "f48": 7,
                "f50": 3_000_000_000,
                "f4c": 101,
            },
            0,
        ],
    }


# the wire expectation fixes the order and independent class and object slots
def MakeMgrWire() -> bytes:
    return (
        MakeMgrDesc("dmConfigMgrHeader_c")
        + PackValues("<H", 2)
        + MakeMgrDesc("dmConfigHeader_c")
        + PackValues("<i", 1)
        + b"\xff\xfe\xff\x02P\x00\xbb\x03"
        + PackValues("<iI", -25, 4_000_000_012)
        + b"\xff\xfe\xff\x05"
        + "Stock".encode("utf-16-le")
        + PackValues("<ii", -1, 1)
        + b"\xff\xfe\xff\x04"
        + "Note".encode("utf-16-le")
        + b"\xff\xfe\xff\x00"
        + PackValues("<iiII", -3, 7, 3_000_000_000, 101)
        + PackValues("<HIi", 4, 3_001_234_567, -21)
    )
