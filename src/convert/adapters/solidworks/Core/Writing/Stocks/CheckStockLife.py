from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# attestation requires independent controls and clean generated edit and reopen evidence
def CheckStockLife(
    Receipt: dict[str, object], Summary: dict[str, object]
) -> tuple[str, str]:
    Phases = ReadMeasMap(Summary.get("phases"))
    Counts = ReadMeasMap(Receipt.get("numerical_checks"))
    Roles = {"Before", "Open", "Reopen", "After"}
    if set(Phases) != Roles or set(Counts) != Roles:
        raise ValueError(
            "stock measurement requires both controls and both candidate phases"
        )
    Digests: dict[str, str] = {}
    for RoleValue, RowValue in Phases.items():
        Phase = ReadMeasMap(RowValue)
        CountValue = Counts[RoleValue]
        if (
            Phase.get("passed") is not True
            or Phase.get("first_failure") is not None
            or Phase.get("open") != [True, 0, 0]
            or type(CountValue) is not int
            or CountValue <= 0
        ):
            raise ValueError("stock measurement contains a failed native phase")
        Digests[RoleValue] = ReadMeasSha(Phase.get("sha256"))
    SaveValue = ReadMeasMap(Receipt.get("edited_native_save"))
    _ = ReadMeasSha(SaveValue.get("sha256"))
    SizeValue = SaveValue.get("bytes")
    if (
        len(set(Digests.values())) != 4
        or type(SizeValue) is not int
        or SizeValue <= 0
        or Receipt.get("fresh_reopen_profiles_match") is not True
        or Receipt.get("fresh_reopen_tree_matches") is not True
    ):
        raise ValueError("stock measurement has no matching edited native derivative")
    return Digests["Open"], Digests["Reopen"]
