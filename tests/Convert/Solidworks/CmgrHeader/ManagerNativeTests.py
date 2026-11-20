from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.CmgrHeader.RunMgrWire import RunMgrWire

# existing disclosed fixtures carry their own native container and stream identities
KFixtureRoot = FilePath(__file__).resolve().parents[4] / "re/solidworks/v2026/corpus"

# exact source and stream hashes distinguish the independent directory inputs
KNativeCases = (
    (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "caa3cb00d615faa644ca20786ae98ff6a4896237648e90c6ed431694f86bb352",
    ),
    (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "9073ac9c452c912ff17b7e788b0e2f4715c9253eb4032fa3771566f2767c4225",
    ),
)


# both actual manager directories must reemit all their bytes with the same map
def TestNativeDir(TmpPath: FilePath) -> None:
    for FixtureName, SourceHash, StreamHash in KNativeCases:
        SourcePath = KFixtureRoot / FixtureName
        ReportPath = TmpPath / f"{SourcePath.stem}.json"
        Outcome = RunMgrWire(
            "document", SourcePath, ReportPath, ("--source-sha256", SourceHash)
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        ReportValue = LoadJson(ReportPath.read_text(encoding="utf-8"))
        assert ReportValue["source_sha256"] == SourceHash
        assert ReportValue["container_version"] == 4
        assert ReportValue["archive_version"] == 19000
        assert ReportValue["sha256"] == StreamHash
        assert ReportValue["bytes"] == 137
        assert ReportValue["root_index"] == 2
        assert ReportValue["entry_indices"] == [1, 2, 3, 4]
        assert ReportValue["next_index"] == 5
        assert ReportValue["row_count"] == 1
        assert ReportValue["row_indices"] == [4]
