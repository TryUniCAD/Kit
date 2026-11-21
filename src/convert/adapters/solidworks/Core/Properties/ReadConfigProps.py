from re import fullmatch as MatchName

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps
from convert.adapters.solidworks.Core.Properties.ReadPropId import ReadPropId
from convert.adapters.solidworks.Core.Properties.ReadPropOwners import ReadPropOwners
from interchange import CadDocument


# each configuration stream retains its own native id without ordinal or active configuration fallback
def ReadConfigProps(
    Document: CadDocument, Archive: SldprtArchive
) -> dict[int, dict[str, str]]:
    ResultValue: dict[int, dict[str, str]] = {}
    NamesValue = tuple(
        NameValue
        for NameValue in Archive.streams
        if NameValue.startswith("docProps/Config-")
    )
    if not NamesValue:
        return ResultValue
    OwnersValue = ReadPropOwners(Document)
    for NameValue in NamesValue:
        MatchValue = MatchName(
            r"docProps/Config-(0|[1-9][0-9]*)-Properties\.xml", NameValue
        )
        if MatchValue is None:
            raise ValueError(
                "part configuration property stream has an unsupported name"
            )
        IdentValue = ReadPropId(MatchValue.group(1))
        if IdentValue not in OwnersValue or IdentValue in ResultValue:
            raise ValueError(
                "part configuration property stream has a stale or duplicate owner"
            )
        ResultValue[IdentValue] = ReadCustomProps(Archive.require(NameValue), True)
    return ResultValue
