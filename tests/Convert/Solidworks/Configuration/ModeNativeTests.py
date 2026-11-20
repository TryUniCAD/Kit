from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunModeCase import RunModeCase

# the two physical part controls retain distinct mode values and map counters
KNativeModes = (("ladder", 12, 1, 97, 108, 80), ("concave", 10, 0, 90, 94, None))


# the shared reader consumes exact native spans and preserves the actual part owner
def TestNativeModes() -> None:
    for (
        CaseName,
        Threshold,
        Identity,
        EarlyCount,
        LateCount,
        BoundsSize,
    ) in KNativeModes:
        ReportValue = RunModeCase(CaseName)
        ModesValue = CastValue(list[dict[str, object]], ReportValue["normalizations"])
        assert [RowValue["field"] for RowValue in ModesValue] == [
            "fd44",
            "fd48",
            "f152c",
        ]
        assert [
            (RowValue["wire"], RowValue["value"], RowValue["counter"])
            for RowValue in ModesValue
        ] == [
            (Threshold, Threshold, EarlyCount),
            (0, 0, EarlyCount),
            (Identity, Identity, LateCount),
        ]
        LeavesValue = CastValue(dict[str, dict[str, object]], ReportValue["leaves"])
        assert LeavesValue["moComponent_c"]["fields"] == {
            "owner": {"class": "moPart_c", "schema": 1, "index": 2}
        }
        assert LeavesValue["moComponent_c"]["bytes"] == 2
        assert LeavesValue["su_CStringArray"]["bytes"] == 126
        assert LeavesValue["utLineWidth_c.Serialize0"]["fields"] == {
            "f06": 0,
            "f00": -1.0,
        }
        assert LeavesValue.get("mgBBox_c.restore", {}).get("bytes") == BoundsSize
