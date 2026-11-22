from math import isclose as IsClose

from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    AttachedBoxPlan,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxTrialScope import (
    KBoxTrialStates,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxTrialState import (
    BoxTrialState,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# the candidate and reopened comparison must account for every separately edited native save
def CheckBoxTrial(
    Phases: dict[str, object], Summary: dict[str, object], PlanValue: AttachedBoxPlan
) -> None:
    Generated = ReadMeasMap(Phases.get("generated"))
    Reopen = ReadMeasMap(Phases.get("reopen"))
    Counts = ReadMeasMap(Summary.get("native_numeric_checks"))
    if Generated.get("generated_open_status") != [0, 0] or any(
        PhaseValue.get("first_failure") is not None
        or PhaseValue.get("dialogs") != []
        or PhaseValue.get("controller_diagnostics") != []
        or type(PhaseValue.get("numeric_checks")) is not int
        or Counts.get(NameValue) != PhaseValue.get("numeric_checks")
        for NameValue, PhaseValue in (("generated", Generated), ("reopen", Reopen))
    ):
        raise ValueError(
            "attached box measurement lacks clean native candidate observations"
        )
    Files = ReadMeasMap(Generated.get("files"))
    OriginalRows = ReadMeasMap(Generated.get("observations"))
    ReopenedRows = ReadMeasMap(Reopen.get("observations"))
    if (
        set(Files) != set(KBoxTrialStates)
        or Reopen.get("files") != Files
        or set(OriginalRows) != set(KBoxTrialStates)
        or set(ReopenedRows) != set(KBoxTrialStates)
        or ReadMeasNum(Counts.get("generated")) <= 0
        or ReadMeasNum(Counts.get("reopen")) <= 0
    ):
        raise ValueError(
            "attached box measurement lacks coverage for all independent edits"
        )
    VerifyBoxEdits(OriginalRows, ReopenedRows, PlanValue)
    Records = ReadMeasMap(Summary.get("raw_evidence_sha256"))
    for StateName, FileValue in Files.items():
        RowValue = ReadMeasMap(FileValue)
        ByteCount = RowValue.get("bytes")
        if (
            type(ByteCount) is not int
            or ByteCount <= 0
            or RowValue.get("sha256") != ReadMeasSha(Records.get(StateName + ".SLDPRT"))
        ):
            raise ValueError("attached box native save changed before fresh reopen")


# each of the three ordinary equation free drivers changes alone and keeps the complete tree
def VerifyBoxEdits(
    OriginalRows: dict[str, object],
    ReopenedRows: dict[str, object],
    PlanValue: AttachedBoxPlan,
) -> None:
    Length, Width, Height = PlanValue.PartSource.DimensionsValue
    Initial = (Length * 0.001, Width * 0.001, Height * 0.001)
    TreeValue = ReadMeasMap(OriginalRows["Original"]).get("tree")
    for IndexValue, StateName in enumerate(KBoxTrialStates, start=-1):
        Preview = ReadMeasMap(OriginalRows[StateName])
        Reopened = ReadMeasMap(ReopenedRows[StateName])
        Spans, Nodes = BoxTrialState(Preview, PlanValue, Initial)
        if (
            Preview.get("tree") != TreeValue
            or (Spans, Nodes) != BoxTrialState(Reopened, PlanValue, None)
            or any(
                IsClose(Actual, Expected, rel_tol=1e-12, abs_tol=0.0)
                == (DriverIndex == IndexValue)
                for DriverIndex, (Actual, Expected) in enumerate(
                    zip(Spans, Initial, strict=True)
                )
            )
        ):
            raise ValueError(
                "attached box measured edit changed owners, tree or unrelated drivers"
            )
