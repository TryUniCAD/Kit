from convert.adapters.solidworks.Archive.Definition.ModelDefRead import ModelDefRead
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef


# the ordinary read boundary requires canonical tags and rejects broader definition owners
def ReadOrdinaryDef(DataValue: bytes, VersionValue: int) -> ModelDefRead:
    return ReadModelDef(DataValue, VersionValue, OrdinaryOnly=True)
