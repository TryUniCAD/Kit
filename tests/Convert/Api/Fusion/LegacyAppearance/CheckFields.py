from json import loads as LoadJson
from pathlib import Path as FilePath

from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields


# the native inventory must match explicit named expectations before decoding new values
def CheckFields(Fields: tuple[PropertySpec, ...], Asset: MaterialAsset) -> None:
    Expected = LoadJson(
        FilePath(__file__).with_name("ExpectedValues.json").read_text(encoding="utf-8")
    )
    Definition = SelectFields(Fields, True)
    Properties = SelectFields(Fields, False)
    assert len(Definition) == 8 and len(Properties) == 40
    assert tuple(Entry.FieldName for Entry in Definition) == tuple(
        Expected["definition"]
    )
    assert tuple(Entry.FieldName for Entry in Properties) == tuple(
        Expected["properties"]
    )
    assert tuple(Entry.FieldName for Entry in Asset.Definitions) == tuple(
        Expected["definition"]
    )
    assert tuple(Entry.FieldName for Entry in Asset.Properties) == tuple(
        Expected["properties"]
    )
    assert all(Entry.UnitName is None for Entry in (*Definition, *Properties))
    assert sum(Entry.ConnectMode == "single" for Entry in Properties) == 11
    assert all(
        Entry.Connections is None for Entry in (*Asset.Definitions, *Asset.Properties)
    )
