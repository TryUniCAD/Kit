from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Stocks.ReadStockRec import StockWireSha

# both authenticated stock cases use the corrected evaluator schema
KStockSchema = "kit.sw2026.two-stock-writer-holdout-evaluation.v2"


# both controls and the original writer identity must agree before a slot is selected
def CheckStockRun(
    Freeze: dict[str, object],
    Native: dict[str, object],
    Staged: dict[str, object],
    Epoch: int,
) -> tuple[str, str]:
    Controls = ReadMeasMap(Native.get("control_sha256"))
    if (
        any(Value.get("schema") != KStockSchema for Value in (Freeze, Native, Staged))
        or Freeze.get("written_at") != Epoch
        or any(
            Value.get("oracle_build") != KOraclePart["build"]
            or Value.get("oracle_exe_sha256") != KOraclePart["sha256"]
            for Value in (Freeze, Native)
        )
        or Native.get("freeze_sha256") != Staged.get("freeze_sha256")
        or Native.get("freeze_sha256") != StockWireSha(Freeze)
        or Native.get("stage_sha256") != StockWireSha(Staged)
        or not all(
            Freeze.get(NameValue) == Native.get(NameValue) == Staged.get(NameValue)
            for NameValue in ("writer_revision", "evaluator_revision")
        )
        or Native.get("source_lock_sha256") != Freeze.get("source_lock_sha256")
        or Native.get("writer_src_tree") != Freeze.get("writer_src_tree")
        or Native.get("passed") is not True
        or Native.get("controls_passed") is not True
        or Native.get("native_candidate_records") != 4
        or Native.get("qualified_holdout_cases") != 2
        or set(Controls) != {"Before", "After"}
    ):
        raise ValueError("selected stock measurement has a different native run")
    return ReadMeasSha(Controls["Before"]), ReadMeasSha(Controls["After"])


# qualification follows the actual candidate open edit save and fresh reopen comparison
def CheckStockLife(CaseValue: dict[str, object]) -> tuple[str, str]:
    Comparisons = ReadMeasMap(CaseValue.get("comparison"))
    Phases = ReadMeasMap(CaseValue.get("native_phases"))
    if (
        CaseValue.get("lifecycle_passed") is not True
        or CaseValue.get("full_native_tree_equal") is not True
        or CaseValue.get("comparison_failures") != {}
        or set(Comparisons) != {"initial", "edited", "reopened"}
        or set(Phases) != {"Open", "Reopen"}
    ):
        raise ValueError("selected stock measurement lacks a complete native lifecycle")
    for RowValue in Comparisons.values():
        Comparison = ReadMeasMap(RowValue)
        if (
            Comparison.get("checks") != 24
            or Comparison.get("full_tree_equal") is not True
        ):
            raise ValueError(
                "selected stock measurement lacks full tree and body checks"
            )
    Opens = tuple(ReadMeasMap(Phases[NameValue]) for NameValue in ("Open", "Reopen"))
    if any(
        Phase.get("passed") is not True or Phase.get("open") != [True, 0, 0]
        for Phase in Opens
    ):
        raise ValueError("selected stock measurement contains a failed native open")
    return ReadMeasSha(Opens[0].get("sha256")), ReadMeasSha(Opens[1].get("sha256"))
