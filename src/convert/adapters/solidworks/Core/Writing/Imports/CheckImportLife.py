from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# an imported solid can prove clean rebuild and persistent topology across native save
def CheckImportLife(
    CaseValue: dict[str, object], NumericChecks: int
) -> tuple[str, str]:
    CleanValue = {"error": 0, "returned_document": True, "warning": 0}
    if (
        ReadMeasMap(CaseValue.get("initial_diagnostics")) != CleanValue
        or ReadMeasMap(CaseValue.get("reopen_diagnostics")) != CleanValue
        or CaseValue.get("persistent_feature_identity") is not True
        or CaseValue.get("numeric_candidate_checks") != NumericChecks
        or ReadMeasMap(CaseValue.get("geometry"))
        != ReadMeasMap(CaseValue.get("reopen_geometry"))
    ):
        raise ValueError("local solid measurement has an incomplete native lifecycle")
    StateValues = tuple(
        ReadMeasMap(CaseValue.get(NameValue))
        for NameValue in ("cold", "rebuilt", "reopen")
    )
    ColdValue, Rebuilt, Reopen = StateValues
    if (
        any(RowValue.get("needs_rebuild") != 0 for RowValue in StateValues)
        or ColdValue.get("save_flag") is not False
        or Rebuilt.get("save_flag") is not True
        or Reopen.get("save_flag") is not False
        or Rebuilt.get("update_stamp") != Reopen.get("update_stamp")
    ):
        raise ValueError("local solid measurement has inconsistent rebuild state")
    Observations = CaseValue.get("native_observation_hashes")
    if not isinstance(Observations, (tuple, list)):
        raise ValueError("local solid measurement needs separate observations")
    ObservationValues = CastValue(Sequence[object], Observations)
    if len(ObservationValues) != 2:
        raise ValueError("local solid measurement needs separate observations")
    Result = (ReadMeasSha(ObservationValues[0]), ReadMeasSha(ObservationValues[1]))
    if Result[0] == Result[1]:
        raise ValueError("local solid measurement needs independent observations")
    _ = ReadMeasSha(CaseValue.get("native_saved_sha256"))
    return Result
