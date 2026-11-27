from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from tests.Convert.Integration.Fusion.DualFrameSnapshots.CheckFramedSnap import (
    CheckFramedSnap,
)
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# encoded identity transform and world local sheet counterexamples must refuse without deleting any source record
@TestMark.parametrize(
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
def CheckFrameBad(ModeName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    StudyPath = (
        RootPath
        / "re/Fusion/DecodedPromotion20261127/DualFrameSnapshots/Counterexamples"
    )
    Report = LoadJson((StudyPath / "Counterexamples.json").read_text())
    Counter = next(
        Value for Value in Report["counterexamples"] if Value["mode"] == ModeName
    )
    Source = StudyPath / Counter["file"]
    assert Source.resolve().is_relative_to(StudyPath.resolve())
    Payload = Source.read_bytes()
    assert HashBytes(Payload).hexdigest() == Counter["sha256"]
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "frame")
    with RaisesError(ValueError):
        CheckFramedSnap(Payload, Sample.Frame)
