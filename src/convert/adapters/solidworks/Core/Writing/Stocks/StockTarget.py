from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import MatchMeasPath


# a named standalone stream must retain the exact locator already measured by the native observer
def StockTarget(
    TargetValue: KTargetType, OptionsValue: WriteOptions, LocatorValue: str
) -> FilePath | None:
    FinalValue = OptionsValue.values.get("final_destination")
    if isinstance(TargetValue, (str, FilePath)):
        return MatchMeasPath(
            TargetValue,
            FinalValue,
            LocatorValue,
            "selected stock requires its actual measured final path",
        )
    if (
        not IsBinaryTarget(TargetValue)
        or type(FinalValue) is not str
        or FinalValue != LocatorValue
    ):
        raise ValueError("selected stock stream requires its exact measured locator")
    return None
