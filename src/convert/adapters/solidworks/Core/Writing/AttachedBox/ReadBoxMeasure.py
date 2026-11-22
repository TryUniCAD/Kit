from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    AttachedBoxPlan,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxMeasure import BoxMeasure
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxMeasPins import (
    KBoxSummarySha,
    KBoxTrialSha,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.ReadBoxRecord import (
    ReadBoxRecord,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.CheckBoxLives import (
    CheckBoxLives,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.CheckBoxTrial import (
    CheckBoxTrial,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# a verified terminal report must be the exact raw lifecycle carried by the caller receipt
def ReadBoxResult(RawValue: object, Summary: dict[str, object]) -> dict[str, object]:
    Hashes = ReadMeasMap(Summary.get("raw_evidence_sha256"))
    if ReadMeasSha(Hashes.get("Result.json")) != KBoxTrialSha:
        raise ValueError("attached box native summary binds a different terminal")
    Record = ReadBoxRecord(RawValue, KBoxTrialSha, "terminal")
    if (
        Record.get("schema") != "kit.sw2026.attached-box-axes-native.v1"
        or Record.get("passed") is not True
        or Record.get("controls_healthy") is not True
        or Record.get("candidate_unchanged") is not True
        or Record.get("oracle_build") != KOraclePart["build"]
        or Record.get("oracle_sha256") != KOraclePart["sha256"]
        or Record.get("job_sha256") != Summary.get("job_sha256")
    ):
        raise ValueError(
            "attached box measurement lacks its exact passing oracle terminal"
        )
    return Record


# the supplied offline evidence must qualify this source and no unmeasured archive
def ReadBoxMeasure(
    SettingsValue: WriteOptions, PlanValue: AttachedBoxPlan
) -> BoxMeasure:
    CreationTime, Envelope, OptionsValue = ReadMeasInput(SettingsValue)
    if set(Envelope) != {"summary", "native_result"}:
        raise ValueError(
            "attached box requires its specific offline native measurement"
        )
    Summary = ReadBoxRecord(Envelope["summary"], KBoxSummarySha, "summary")
    if (
        Summary.get("schema") != "kit.sw2026.attached-box-axes-native-receipt.v1"
        or Summary.get("passed") is not True
        or Summary.get("controls_healthy") is not True
        or Summary.get("oracle_build") != KOraclePart["build"]
        or Summary.get("oracle_sha256") != KOraclePart["sha256"]
        or Summary.get("source_sha256") != PlanValue.SourceDocument.source.sha256
        or CreationTime != PlanValue.PartSource.CreationEpoch
        or Summary.get("creation_epoch") != CreationTime
        or Summary.get("runtime_input_file_reads") != 0
    ):
        raise ValueError(
            "attached box native measurement does not bind this intact source"
        )
    _ = ReadMeasSha(Summary.get("job_sha256"))
    _ = ReadMeasSha(Summary.get("build_sha256"))
    Terminal = ReadBoxResult(Envelope["native_result"], Summary)
    Candidate = ReadMeasMap(Summary.get("candidate"))
    Digest = ReadMeasSha(Candidate.get("sha256"))
    Locator = Candidate.get("native_path")
    SizeValue = Candidate.get("bytes")
    if (
        Candidate.get("immutable") is not True
        or type(Locator) is not str
        or Locator != Terminal.get("native_destination")
        or Digest != Terminal.get("candidate_sha256")
        or type(SizeValue) is not int
        or SizeValue <= 0
    ):
        raise ValueError("attached box measurement has a different archive or locator")
    Phases = CheckBoxLives(Terminal, Summary)
    CheckBoxTrial(Phases, Summary, PlanValue)
    Hashes = ReadMeasMap(Summary.get("raw_evidence_sha256"))
    return BoxMeasure(
        OptionsValue, Locator, Digest, SizeValue, ReadMeasSha(Hashes.get("Result.json"))
    )
