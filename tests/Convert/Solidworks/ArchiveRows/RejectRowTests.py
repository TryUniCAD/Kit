from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveRows.RunRows import RunRows


# the repeat limit and framework framing must reject before a result is published
def TestBadRows(TmpPath: FilePath) -> None:
    for LabelName, PayloadValue, ErrorText in (
        (
            "FrameworkEscape",
            b"\x00\x00" + b"\xff" * 6,
            "framework count has no complete unsigned long long",
        ),
        (
            "OversizedCount",
            PackValues("<HI", 0xFFFF, 10_000_001),
            "implausible SOLIDWORKS body repeat 10000001",
        ),
    ):
        WirePath = TmpPath / f"{LabelName}.bin"
        ReadPath = TmpPath / f"{LabelName}.json"
        _ = WirePath.write_bytes(PayloadValue)
        Outcome = RunRows("read", WirePath, ReadPath)
        assert Outcome.returncode != 0
        assert ErrorText in Outcome.stderr
        assert not ReadPath.exists()
