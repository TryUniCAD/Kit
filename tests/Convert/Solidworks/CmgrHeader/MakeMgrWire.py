from struct import pack as PackValues

from tests.Convert.Solidworks.CmgrHeader.MakeCfgBody import MakeCfgBody
from tests.Convert.Solidworks.CmgrHeader.MakeMgrDesc import MakeMgrDesc

# the first extended vendor count needs the unsigned short escape
KCountThreshold = 0xFFFF


# signed and unsigned words must remain independent of the native body layout
def MakeMgrInput(IsExtended: bool = False) -> dict[str, object]:
    FirstChild = {
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
    }
    RowsValue: list[object] = [FirstChild]
    if IsExtended:
        RowsValue.append({**FirstChild, "f30": 84})
    RowsValue.extend([0] * (KCountThreshold - 2 if IsExtended else 1))
    return {
        "saved_at": 3_001_234_567,
        "sort_word": -21,
        "rows": RowsValue,
    }


# the wire expectation fixes the order and independent class and object slots
def MakeMgrWire(IsExtended: bool = False) -> bytes:
    Children = MakeMgrDesc("dmConfigHeader_c") + MakeCfgBody(-25)
    if IsExtended:
        CountBytes = PackValues("<HI", 0xFFFF, KCountThreshold)
        Children += PackValues("<H", 0x8003) + MakeCfgBody(84)
        AliasCount = KCountThreshold - 2
    else:
        CountBytes = PackValues("<H", 2)
        AliasCount = 1
    return (
        MakeMgrDesc("dmConfigMgrHeader_c")
        + CountBytes
        + Children
        + PackValues("<H", 4) * AliasCount
        + PackValues("<Ii", 3_001_234_567, -21)
    )
