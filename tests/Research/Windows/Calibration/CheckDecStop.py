from pathlib import Path as FilePath

from tests.Research.Calibration.CalRunDetails import TrialDetails


# decoder rejection must stop for the child refusal and show any earlier infrastructure failure
def CheckDecStop(Report: dict[str, object], OutputPath: FilePath) -> None:
    assert Report["stop_reason"] == "child_did_not_complete", (
        Report["stop_reason"],
        TrialDetails(OutputPath / "Calibration.json"),
    )
