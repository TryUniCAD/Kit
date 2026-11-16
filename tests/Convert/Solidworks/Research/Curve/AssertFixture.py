from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import PurePosixPath as PosixPath
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KCurveCorpus


# every prepared native file must retain the locked discovery identity and exact bytes
def AssertFixture(Entry: dict[str, object], Locked: dict[str, object]) -> None:
    FileName = CastValue(str, Entry["file"])
    FileEntry = KCurveCorpus / FileName
    SpecData = CastValue(dict[str, object], Entry["spec"])
    assert FileName == f"{Entry['name']}.SLDPRT"
    assert FileEntry.parent.resolve() == KCurveCorpus.resolve()
    assert not FileEntry.is_symlink()
    assert Entry["split"] == Locked["split"] in {"discovery", "control"}
    assert SpecData["name"] == Entry["name"] == Locked["name"]
    assert SpecData["split"] == Entry["split"]
    assert Entry["configurations"] == ["Config-0"]
    assert Entry["source_sha256"] == Locked["sha256"]
    assert Entry["source_manifest_sha256"] == Locked["manifest_sha256"]
    assert (
        Entry["source_manifest"]
        == PosixPath(CastValue(str, Locked["file"]))
        .with_name("Manifest.json")
        .as_posix()
    )
    assert HashBytes(FileEntry.read_bytes()).hexdigest() == Entry["sha256"]
