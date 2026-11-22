from pathlib import PureWindowsPath

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Stocks.CheckStockLife import (
    CheckStockLife,
    CheckStockRun,
)
from convert.adapters.solidworks.Core.Writing.Stocks.ReadStockRec import (
    CheckStockRec,
    StockWireSha,
)
from convert.adapters.solidworks.Core.Writing.Stocks.StockMeasure import StockMeasure

# the corrected native evaluator opened each exact generated basename in this folder
KStockFolder = PureWindowsPath(r"C:\KitSdkCandidates\TwoStockWriterEvaluation02")


# each measured candidate must belong to the guarded generation and its matching lifecycle
def StockMeasureRow(
    SlotValue: dict[str, object],
    CaseValue: dict[str, object],
    SlotName: str,
    Epoch: int,
    ResultSha: str,
) -> StockMeasure:
    CandidateSha = ReadMeasSha(SlotValue.get("sha256"))
    SizeValue = SlotValue.get("bytes")
    NameValue = f"TwoStockHoldout{SlotName.upper()}.SLDPRT"
    if (
        type(SizeValue) is not int
        or SizeValue <= 0
        or SlotValue.get("name") != NameValue
        or CaseValue.get("generated_sha256") != CandidateSha
        or SlotValue.get("runtime_access_attempts") != 0
        or SlotValue.get("generation_guarded_processes") != 2
        or SlotValue.get("cold_sdk_guarded_processes") != 1
        or SlotValue.get("cold_sdk_body_count") != 2
    ):
        raise ValueError(
            "selected stock measurement does not bind the measured archive"
        )
    EditSha, ReopenSha = CheckStockLife(CaseValue)
    return StockMeasure(
        Epoch,
        str(KStockFolder / NameValue),
        SizeValue,
        CandidateSha,
        ResultSha,
        EditSha,
        ReopenSha,
    )


# the request can select only one of the exact authenticated candidate basenames
def ReadStockMeas(
    OptionsValue: WriteOptions, PartName: object
) -> tuple[StockMeasure, WriteOptions]:
    Epoch, Receipt, PreparedOptions = ReadMeasInput(OptionsValue)
    CheckStockRec(Receipt)
    if type(PartName) is not str:
        raise ValueError("selected stock requires its exact authored basename")
    Freeze = ReadMeasMap(Receipt.get("freeze"))
    Native = ReadMeasMap(Receipt.get("native"))
    Staged = ReadMeasMap(Receipt.get("staged"))
    Controls = CheckStockRun(Freeze, Native, Staged, Epoch)
    Slots = ReadMeasMap(Staged.get("slots"))
    Cases = ReadMeasMap(Native.get("cases"))
    if set(Slots) != {"a", "b"} or set(Cases) != set(Slots):
        raise ValueError("selected stock measurement has a different slot inventory")
    ResultSha = StockWireSha(Native)
    SlotsValue = tuple(
        StockMeasureRow(
            ReadMeasMap(Slots[SlotName]),
            ReadMeasMap(Cases[SlotName]),
            SlotName,
            Epoch,
            ResultSha,
        )
        for SlotName in ("a", "b")
    )
    Digests = {
        PhaseSha
        for Entry in SlotsValue
        for PhaseSha in (Entry.EditSha, Entry.ReopenSha)
    }
    if len(Digests.union(Controls)) != 6:
        raise ValueError(
            "selected stock measurement lacks distinct fresh native phases"
        )
    Matches = tuple(
        Entry
        for Entry in SlotsValue
        if PureWindowsPath(Entry.LocatorValue).stem == PartName
    )
    if len(Matches) != 1:
        raise ValueError(
            "selected stock has no exact native measurement for its authored basename"
        )
    return Matches[0], PreparedOptions
