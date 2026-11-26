from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.KeywordFrames.RunKeywordFrame import RunKeywordFrame

# exact sources already present in the checkout cover the two framing styles
KFixtureRoot = FilePath(__file__).resolve().parents[4] / "re/solidworks/v2026/corpus"

# logical stream hashes must stay bound to their disclosed source and profile
KKeywordCases = (
    (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "507f9c7c1b6c4a70ea1ab7fe4c3e66b4cbab6f46168dc5e1338c5710499a69ef",
        1739,
        "compact",
    ),
    (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "067f823ee629cb6477d074d1177f65d5b8ca93843bb13c979b0a11ba02e55b28",
        1306,
        "spaced",
    ),
)


# complete replay must pass for native compact and generated spaced evidence
def TestKeySources(TmpPath: FilePath) -> None:
    for NameValue, SourceHash, StreamHash, ByteCount, ModeName in KKeywordCases:
        SourcePath = KFixtureRoot / NameValue
        ReportPath = TmpPath / f"{SourcePath.stem}.json"
        Outcome = RunKeywordFrame(
            "document",
            SourcePath,
            ReportPath,
            ("--source-sha256", SourceHash, "--empty-tags", ModeName),
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        assert LoadJson(ReportPath.read_text(encoding="utf-8")) == {
            "source_sha256": SourceHash,
            "stream_sha256": StreamHash,
            "byte_count": ByteCount,
            "container_version": 4,
            "archive_version": 19000,
            "empty_tags": ModeName,
        }
