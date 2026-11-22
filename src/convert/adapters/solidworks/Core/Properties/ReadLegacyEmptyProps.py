from re import fullmatch as MatchName

from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropManager
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadCoreProps import ReadCoreProps
from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps


# legacy conversion can preserve text absence only after confirming all physical property owners
def ReadLegacyProps(Archive: SldprtArchive) -> None:
    SeenNames: set[str] = set()
    for RecordValue in Archive.records:
        NameValue, DataValue = RecordValue.name, RecordValue.data
        if NameValue == "Contents/CusProps":
            ReadPropManager(DataValue, 18000)
        elif NameValue == "docProps/core.xml":
            if ReadCoreProps(DataValue):
                raise ValueError("legacy SOLIDWORKS part contains authored summary text")
        elif NameValue == "docProps/custom.xml":
            if ReadCustomProps(DataValue, False):
                raise ValueError("legacy SOLIDWORKS part contains authored document text")
        elif NameValue.startswith("docProps/Config-"):
            if MatchName(r"docProps/Config-(0|[1-9][0-9]*)-Properties\.xml", NameValue) is None:
                raise ValueError("legacy part configuration text stream has an unsupported name")
            if ReadCustomProps(DataValue, True):
                raise ValueError("legacy SOLIDWORKS part contains authored configuration text")
        else:
            continue
        if NameValue in SeenNames:
            raise ValueError("legacy part contains duplicate property scopes")
        SeenNames.add(NameValue)
    if "Contents/CusProps" not in SeenNames:
        raise ValueError("legacy part lacks its native property owner")
