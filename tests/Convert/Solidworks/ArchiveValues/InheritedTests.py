from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveValues.MakeValueWire import MakeValueWire
from tests.Convert.Solidworks.ArchiveValues.RunBodyValues import RunBodyValues

# the linked record only opens a body through inherited class slot three
KLinkBytes = PackValues("<H", 0x8003) + b"\xff\xfe\xff\x01L\x00" + PackValues("<H", 4)


# the fresh processes must reconstruct the same prefix from actual graph bytes
def MakeSeedInput(TmpPath: FilePath) -> tuple[str, ...]:
    PrimaryPath = TmpPath / "Primary.bin"
    _ = PrimaryPath.write_bytes(MakeValueWire(b"\xff\xfe\xff\x01P\x00"))
    return "--seed-primary", str(PrimaryPath)


# seeded links must reuse the original object and class identities
def TestSeedValues(TmpPath: FilePath) -> None:
    SeedArgs = MakeSeedInput(TmpPath)
    SourcePath = TmpPath / "Authored.json"
    WirePath = TmpPath / "Linked.bin"
    ReadPath = TmpPath / "Read.json"
    _ = SourcePath.write_text(DumpJson({"label": "L"}), encoding="utf-8")
    WriteResult = RunBodyValues("write", SourcePath, WirePath, SeedArgs)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert WirePath.read_bytes() == KLinkBytes
    ReadResult = RunBodyValues("read", WirePath, ReadPath, SeedArgs)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8")) == {
        "label": "L",
        "inherited_index": 4,
        "root_index": 5,
        "base": 5,
        "next": 6,
    }


# sparse inherited prefixes need real ownership before entering the body codec
def TestSparseLink(TmpPath: FilePath) -> None:
    SeedArgs = (*MakeSeedInput(TmpPath), "--sparse-seed")
    SourcePath = TmpPath / "Authored.json"
    WirePath = TmpPath / "Linked.bin"
    _ = SourcePath.write_text(DumpJson({"label": "L"}), encoding="utf-8")
    _ = WirePath.write_bytes(KLinkBytes)
    for ModeName, InputPath, ErrorText in (
        ("write", SourcePath, "archive object must be an archive node"),
        ("read", WirePath, "SOLIDWORKS stream has an unresolved external object"),
    ):
        OutputPath = TmpPath / f"{ModeName}.out"
        ResultValue = RunBodyValues(ModeName, InputPath, OutputPath, SeedArgs)
        assert ResultValue.returncode != 0
        assert ErrorText in ResultValue.stderr
        assert not OutputPath.exists()
