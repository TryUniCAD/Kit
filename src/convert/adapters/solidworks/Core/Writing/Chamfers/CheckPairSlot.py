from convert.adapters.solidworks.Core.Writing.Chamfers.CheckPairPhase import (
    CheckPairPhase,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# each measured stock must preserve its actual input identity and edited save through the fresh reopen
def CheckPairSlot(
    CaseValue: dict[str, object], BuildValue: dict[str, object], SlotValue: int
) -> tuple[str, str]:
    CaseHash = ReadMeasSha(CaseValue.get("candidate_sha256"))
    SavedHash = ReadMeasSha(CaseValue.get("edited_sha256"))
    Checks = (43, 21) if SlotValue == 0 else (45, 22)
    ModeWord = 18 if SlotValue == 0 else 2
    if (
        type(CaseValue.get("slot")) is not int
        or CaseValue.get("slot") != SlotValue
        or CaseValue.get("passed") is not True
        or type(CaseValue.get("tree_rows")) is not int
        or CaseValue.get("tree_rows") != 26
        or ReadMeasSha(BuildValue.get("archive_sha256")) != CaseHash
        or SavedHash == CaseHash
        or type(BuildValue.get("mode_word")) is not int
        or BuildValue.get("mode_word") != ModeWord
        or type(BuildValue.get("guarded_processes")) is not int
        or BuildValue.get("guarded_processes") != 2
        or type(BuildValue.get("runtime_external_reads")) is not int
        or BuildValue.get("runtime_external_reads") != 0
    ):
        raise ValueError(
            "distance chamfer measurement has an unowned candidate or edited save"
        )
    EditValue, Reopen = ReadMeasRows(CaseValue.get("phases"), 2)
    return (
        CheckPairPhase(EditValue, "reopen-edit-save", Checks[0], SavedHash),
        CheckPairPhase(Reopen, "edited-reopen", Checks[1], SavedHash),
    )
