from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import PurePosixPath as PosixPath
from typing import cast as CastValue
from tests.convert.solidworks.research.ArchiveProcess import KRepoRoot
from tests.convert.solidworks.research.Curve.Fields.AssertDigest import AssertDigest


# recorded implementation fingerprints must identify the actual reviewed inventory source files
def AssertFieldCode(Report: dict[str, object]) -> None:
    SerialPath = KRepoRoot / "re/tooling/sw2026/serial"
    Expected = (
        {
            (SerialPath / FileName).relative_to(KRepoRoot).as_posix()
            for FileName in (
                "FieldScan.py",
                "Core.py",
                "Schema.py",
                "Classes.py",
                "Streams.py",
                "RoundTrip.py",
                "Dsl.py",
                "AnnotationWire.py",
            )
        }
        | {
            SourcePath.relative_to(KRepoRoot).as_posix()
            for SourcePath in (SerialPath / "defs").glob("*.py")
        }
        | {
            "src/convert/adapters/solidworks/Archive/Counts/" + FileName
            for FileName in ("EncodeCount.py", "ReadCount.py")
        }
        | {
            "src/convert/adapters/solidworks/Archive/Tags/" + FileName
            for FileName in ("ArchiveTag.py", "EncodeTag.py", "ReadTag.py")
        }
        | {
            "src/convert/adapters/solidworks/Archive/Strings/" + FileName
            for FileName in ("CStringValue.py", "EncodeString.py", "ReadString.py")
        }
    )
    Records = CastValue(list[dict[str, object]], Report["implementation"])
    Names = [CastValue(str, Record["file"]) for Record in Records]
    assert len(Names) == len(set(Names))
    assert set(Names) == Expected
    for Record in Records:
        NameValue = CastValue(str, Record["file"])
        Relative = PosixPath(NameValue)
        assert not Relative.is_absolute() and ".." not in Relative.parts
        SourcePath = KRepoRoot.joinpath(*Relative.parts)
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(KRepoRoot.resolve())
        assert (
            AssertDigest(Record["sha256"])
            == HashBytes(SourcePath.read_bytes()).hexdigest()
        )
