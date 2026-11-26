from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveValues.MakeValueWire import MakeValueWire
from tests.Convert.Solidworks.ArchiveValues.RunBodyValues import RunBodyValues


# longer length prefixes must fail before a body field takes ownership
def TestTextReject(TmpPath: FilePath) -> None:
    for LabelName, LabelFrame in (
        ("WideWord", b"\xff\xfe\xff\xff\x01\x00" + b"a\x00"),
        ("AnsiDword", b"\xff\xff\xff\x01\x00\x00\x00" + b"a"),
    ):
        WirePath = TmpPath / f"{LabelName}.bin"
        ReadPath = TmpPath / f"{LabelName}.json"
        _ = WirePath.write_bytes(MakeValueWire(LabelFrame))
        ResultValue = RunBodyValues("read", WirePath, ReadPath)
        assert ResultValue.returncode != 0
        assert (
            "SOLIDWORKS body text has a noncanonical length prefix"
            in ResultValue.stderr
        )
        assert "text checkpoint 19, cursor 19, fields intact True" in ResultValue.stderr
        assert not ReadPath.exists()
