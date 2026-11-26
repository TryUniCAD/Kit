from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Views.ReadViewPair import ReadViewPair
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# the saved document pose must come from the complete typed definition owners
def ReadPartView(DataValue: bytes, VersionValue: int) -> ViewInput:
    Definition = ReadModelDef(DataValue, VersionValue).GraphValue.DocumentValue
    FieldsValue = Definition.FieldsValue
    return ReadViewPair(FieldsValue["fae8"], FieldsValue["faf0"])
