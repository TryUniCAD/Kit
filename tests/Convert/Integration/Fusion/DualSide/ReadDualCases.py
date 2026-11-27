import json as JsonLib
from pathlib import Path

from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCase import ReadDualCase


# each saved independent edit and held out source remains an integration input
def ReadDualCases() -> tuple[DualCase, ...]:
    RootPath = Path(__file__).resolve().parents[5]
    Campaign = RootPath / "re/Fusion/TwoSidedDraft20261127"
    Capture = JsonLib.loads((Campaign / "Capture.json").read_text())
    Results: list[DualCase] = []
    for CaseValue in Capture["cases"]:
        Observations = {
            Value["stage"]: Value["value"] for Value in CaseValue["observations"]
        }
        for Archive in CaseValue["archives"]:
            Source = (Campaign / "Native" / Archive["file"]).resolve()
            if not Source.is_relative_to(Campaign / "Native"):
                raise ValueError("Native drafted source escapes its campaign")
            Suffix = Source.stem.removeprefix(CaseValue["id"])
            Stage = (
                "restore_draft_second"
                if Suffix == "_restored"
                else Suffix.lstrip("_") or "baseline"
            )
            Results.append(
                ReadDualCase(
                    Source,
                    Archive["sha256"],
                    Source.stem,
                    Observations[Stage],
                )
            )
    return tuple(Results)
