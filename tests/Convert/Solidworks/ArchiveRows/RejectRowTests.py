from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveRows.RunRows import RunRows


# the repeat limit and framework framing must reject before a result is published
def TestBadRows(TmpPath: FilePath) -> None:
    for LabelName, PayloadValue, ErrorText, Checkpoint in (
        (
            "FrameworkEscape",
            b"\x00\x00" + b"\xff" * 6,
            "framework count has no complete unsigned long long",
            2,
        ),
        (
            "OversizedCount",
            PackValues("<HI", 0xFFFF, 10_000_001),
            "implausible SOLIDWORKS body repeat 10000001",
            0,
        ),
        (
            "SplitTruncated",
            PackValues("<HHiI", 0, 0, 0, 9),
            "truncated SOLIDWORKS archive field at 12",
            8,
        ),
        (
            "CombinedLimit",
            PackValues("<HHiIIII", 0, 0, 0, 0, 0, 1, 0),
            "implausible SOLIDWORKS body repeat 4294967296",
            16,
        ),
    ):
        WirePath = TmpPath / f"{LabelName}.bin"
        ReadPath = TmpPath / f"{LabelName}.json"
        _ = WirePath.write_bytes(PayloadValue)
        Outcome = RunRows("read", WirePath, ReadPath)
        assert Outcome.returncode != 0
        assert ErrorText in Outcome.stderr
        assert (
            f"array checkpoint {Checkpoint}, cursor {Checkpoint}, scope intact True"
            in Outcome.stderr
        )
        assert not ReadPath.exists()
