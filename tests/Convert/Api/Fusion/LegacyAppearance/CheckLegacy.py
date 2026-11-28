from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from convert.Formats.Fusion.MaterialCodec.Records.DecodeFields import DecodeFields
from convert.Formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader
from tests.Convert.Api.Fusion.LegacyAppearance.LegacyValue import LegacyValue
from tests.Convert.Api.Fusion.LegacyAppearance.NativeFields import NativeFields


# native receiving fields must recover every authored value without sender assumptions
def CheckLegacy(Output: FilePath, Glossiness: float = -0.0) -> None:
    Expected = LoadJson(
        FilePath(__file__).with_name("ExpectedValues.json").read_text(encoding="utf-8")
    )
    Expected["properties"]["generic_glossiness"] = Glossiness
    Fields = NativeFields()
    for GroupName, FileName, IsDefinition in (
        ("definition", "Definition.bin", True),
        ("properties", "Properties.bin", False),
    ):
        Payload = (Output / FileName).read_bytes()
        Values = DecodeFields(MaterialReader(Payload), Fields, IsDefinition)
        Observed = {Entry.FieldName: LegacyValue(Entry.Value) for Entry in Values}
        assert all(Entry.Connections is None for Entry in Values)
        assert tuple(Observed) == tuple(Expected[GroupName])
        assert DumpJson(Observed, allow_nan=False) == DumpJson(
            Expected[GroupName], allow_nan=False
        )
