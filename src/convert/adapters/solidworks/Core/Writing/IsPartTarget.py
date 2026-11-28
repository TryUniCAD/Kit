from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Container.Format import KPartSuffix


# target selection and native end evidence must agree on the actual authored part destination
def IsPartTarget(NameValue: str, TargetValue: KTargetType) -> bool:
    if isinstance(TargetValue, (str, FilePath)):
        PathValue = FilePath(TargetValue)
        return (
            PathValue.suffix.casefold() == KPartSuffix and PathValue.stem == NameValue
        )
    return IsBinaryTarget(TargetValue)
