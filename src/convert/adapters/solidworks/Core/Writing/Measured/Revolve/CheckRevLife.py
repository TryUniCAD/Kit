from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.CheckRevNumbers import (
    CheckRevNumbers,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.CheckRevPhase import (
    CheckRevPhase,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevEvidence import (
    RevEvidence,
)


# bind observed angle driver edit and clean native saved derivative to the same candidate and actual fresh reopen
def CheckRevLife(Evidence: RevEvidence, Digest: str) -> tuple[str, str]:
    if Evidence.IsEndBatch:
        (NativeCase,) = (
            RowValue
            for RowValue in ReadMeasRows(Evidence.Report.get("cases"), 4)
            if RowValue.get("candidate_sha256") == Digest
        )
        Comparisons = ReadMeasMap(NativeCase.get("comparisons"))
        PhaseValue = NativeCase.get("native_phase_sha256")
        PhaseHashes = (
            CastValue(list[object], PhaseValue) if type(PhaseValue) is list else []
        )
        if (
            NativeCase.get("passed") is not True
            or NativeCase.get("native_phase_failures") != [None, None]
            or not {"reopened", "edited", "edited_fresh_reopen"} <= Comparisons.keys()
            or any(
                ReadMeasMap(RowValue).get("mass_checks") != 6
                for RowValue in Comparisons.values()
            )
            or len(PhaseHashes) != 2
        ):
            raise ValueError("measured revolve lacks its clean edit and fresh reopen")
        PhaseEdit, PhaseReopen = PhaseHashes
        return ReadMeasSha(PhaseEdit), ReadMeasSha(PhaseReopen)
    (CaseValue,) = (
        ReadMeasMap(RowValue)
        for RowValue in ReadMeasMap(Evidence.Summary.get("cases")).values()
        if ReadMeasMap(RowValue).get("generated_sha256") == Digest
    )
    (Edited,) = (
        RowValue
        for RowValue in ReadMeasRows(Evidence.Report.get("cases"), 2)
        if RowValue.get("source_sha256") == Digest
    )
    DerivativeSha = ReadMeasSha(CaseValue.get("edited_sha256"))
    (Reloaded,) = (
        RowValue
        for RowValue in ReadMeasRows(Evidence.Report.get("derivative_reopens"), 2)
        if RowValue.get("source_sha256") == DerivativeSha
    )
    CheckRevPhase(Edited, 2)
    CheckRevPhase(Reloaded, 1)
    Driver = ReadMeasMap(Edited.get("edit"))
    Saved = ReadMeasMap(Edited.get("edited_derivative"))
    Phases = ReadMeasMap(CaseValue.get("phases"))
    if (
        ReadMeasMap(Edited.get("job")).get("phase") != "reopen"
        or ReadMeasMap(Reloaded.get("job")).get("phase") != "edited-reopen"
        or Edited.get("geometry_and_edit_passed") is not True
        or Driver.get("passed") is not True
        or Driver.get("setter_status") != 0
        or not str(Driver.get("name")).startswith("D1@")
        or Driver.get("before_radians")
        != ReadMeasMap(Phases.get("open")).get("angle_radians")
        or Driver.get("after_radians")
        != ReadMeasMap(Phases.get("edited")).get("angle_radians")
        or Driver.get("before_radians") == Driver.get("after_radians")
        or Saved.get("save_status") != [True, 0, 0]
        or Saved.get("sha256") != DerivativeSha
        or Reloaded.get("matches_edited_tree") is not True
    ):
        raise ValueError(
            "measured revolve lacks its clean D1 edit, save and fresh reopen"
        )
    CheckRevNumbers(
        Phases, Edited.get("reopened"), Edited.get("edited"), Reloaded.get("reopened")
    )
    return ReadMeasSha(Edited.get("phase_sha256")), ReadMeasSha(
        Reloaded.get("phase_sha256")
    )
