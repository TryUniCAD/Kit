from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkValue

from tests.Research.Archives.Comparison.NativeSketchOwnership.ChangeSketch import (
    ChangeSketch,
)
from tests.Research.Archives.Comparison.NativeSketchOwnership.ReadSketchPart import (
    KSourceSha,
    ReadSketchPart,
)
from tests.Research.Archives.Comparison.NativeSketchOwnership.VerifyOwner import (
    VerifyOwner,
)
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)

# the issue inventory seal preserves every existing path and reason including the native owner definition
KIssueSha = "17e69a4ab049d41653a39a5348750a0a4c7a48b3b9241cd74a17fbee901886f9"


# comparison must retain all preexisting issues while withholding the unsupported ownership observation
@MarkValue.parametrize("ModeName", ("identity", "span"))
def CheckOwnerLink(TmpPath: FilePath, ModeName: str) -> None:
    Document = ReadSketchPart()
    Arguments = WriteInputs(TmpPath, Document, ChangeSketch(Document, ModeName))
    Report = ReadReport(RunComparison(Arguments), "different", 2)
    Sources = CastValue(dict[str, dict[str, object]], Report["sources"])
    for Source in Sources.values():
        assert Source["source_sha256"] == KSourceSha
        Issues = CastValue(list[dict[str, object]], Source["unresolved"])
        assert len(Issues) == 190
        assert sum(Issue["reason"] == "native_only_record" for Issue in Issues) == 25
        IssueBytes = EncodeJson(
            [(Issue["path"], Issue["reason"]) for Issue in Issues],
            separators=(",", ":"),
        ).encode()
        assert DigestBytes(IssueBytes).hexdigest() == KIssueSha
    Matches = {
        SideName: [
            Entry
            for Entry in CastValue(list[dict[str, object]], Source["observations"])
            if Entry.get("classification") == "reader_reported_native_sketch_owner"
        ]
        for SideName, Source in Sources.items()
    }
    assert not Matches["right"]
    (Observation,) = Matches["left"]
    VerifyOwner(Document, Observation)
