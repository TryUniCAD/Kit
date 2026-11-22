from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxTrialScope import (
    KBoxTrialPhases,
    KBoxTrialRecords,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# a measured publication requires all four successful controlled exact build lifetimes
def CheckBoxLives(
    Terminal: dict[str, object], Summary: dict[str, object]
) -> dict[str, object]:
    Phases = ReadMeasMap(Terminal.get("phases"))
    Processes = ReadMeasMap(Summary.get("processes"))
    Records = ReadMeasMap(Summary.get("raw_evidence_sha256"))
    if (
        set(Phases) != set(KBoxTrialPhases)
        or set(Processes) != set(KBoxTrialPhases)
        or Terminal.get("distinct_processes") != len(KBoxTrialPhases)
        or Summary.get("native_process_count") != len(KBoxTrialPhases)
    ):
        raise ValueError("attached box measurement lacks its four controlled lifetimes")
    Previous = 0
    for PhaseName, RecordName in zip(KBoxTrialPhases, KBoxTrialRecords, strict=True):
        Stage = ReadMeasMap(Phases[PhaseName])
        Identity = ReadMeasMap(Stage.get("oracle_identity"))
        Process = Identity.get("process_id")
        TimeValue = Identity.get("process_creation_filetime")
        if (
            Stage.get("passed") is not True
            or Stage.get("record_sha256") != ReadMeasSha(Records.get(RecordName))
            or Identity.get("version_matches") is not True
            or Identity.get("file_version") != Terminal.get("oracle_build")
            or Identity.get("sha256") != Terminal.get("oracle_sha256")
            or Identity.get("pe_machine") != "0x8664"
            or type(Process) is not int
            or Process <= 0
            or type(TimeValue) is not int
            or TimeValue <= Previous
            or Processes[PhaseName]
            != {"process_id": Process, "process_creation_filetime": TimeValue}
        ):
            raise ValueError(
                "attached box measurement disagrees with its actual process receipt"
            )
        Previous = TimeValue
    return Phases
