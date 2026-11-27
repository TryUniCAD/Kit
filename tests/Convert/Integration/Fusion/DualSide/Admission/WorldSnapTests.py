from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument


# the public reader must reject double placement and mismatched mixed space snapshot data
@MarkTests.parametrize(
    "ModeName",
    (
        "body_rotation",
        "body_translation",
        "body_reflection",
        "shared_transform",
        "profile_normal",
        "world_sketch",
    ),
)
def CheckWorldSnap(ModeName: str) -> None:
    Study = (
        Path(__file__).resolve().parents[6]
        / "re/Fusion/DecodedPromotion20261127/DualFrameSnapshots/Counterexamples"
    )
    Report = LoadJson((Study / "Counterexamples.json").read_text())
    CaseValue = next(
        Value for Value in Report["counterexamples"] if Value["mode"] == ModeName
    )
    Source = (Study / CaseValue["file"]).resolve()
    assert Source.is_relative_to(Study.resolve())
    assert HashBytes(Source.read_bytes()).hexdigest() == CaseValue["sha256"]
    with RaisesError(ValueError):
        _ = OpenDocument(Source, strict=True)
