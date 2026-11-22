from typing import cast as CastValue

from tests.Convert.Solidworks.Archive.RunHistoryCase import RunHistoryCase


# independent physical history streams keep their measured lengths maps and exact wire hashes
def TestHistorySave() -> None:
    ExpectedCases = (
        (
            "ladder",
            1541,
            2,
            101,
            "8bdb6a02f4043b6addfb3acd0ff11dbbaf28f1190fb0627b19fb372e4673ee70",
        ),
        (
            "annulus",
            1561,
            2,
            101,
            "16c51ae30278ce2f4c0d34eaa0bcdfbb78b244e0a33b1cbfbfaea37395281b26",
        ),
        (
            "concave",
            23,
            0,
            187,
            "7665bb419e28ffeeccb167d92644744cb45b352b44fc575e898a1d1e1d45eb14",
        ),
    )
    for CaseName, BioBytes, BioCount, HistBytes, BioSha in ExpectedCases:
        ReportValue = RunHistoryCase(CaseName)
        StreamsValue = CastValue(dict[str, dict[str, object]], ReportValue["streams"])
        Biography = StreamsValue["Biography"]
        HistoryValue = StreamsValue["History"]
        assert (Biography["bytes"], Biography["n"], Biography["sha256"]) == (
            BioBytes,
            BioCount,
            BioSha,
        )
        assert Biography["counter"] == 3 and HistoryValue["counter"] == 5
        assert HistoryValue["bytes"] == HistBytes
        assert HistoryValue["version"] == [19000]
        assert HistoryValue["date_counts"] == [1]
        assert HistoryValue["map"] == [
            [1, "RuntimeClass", "moVersionHistory_c"],
            [2, "ArchiveNode", "moVersionHistory_c"],
            [3, "RuntimeClass", "moDateCodeHistory_c"],
            [4, "ArchiveNode", "moDateCodeHistory_c"],
        ]
        assert Biography["exact_reemission"] is HistoryValue["exact_reemission"] is True
