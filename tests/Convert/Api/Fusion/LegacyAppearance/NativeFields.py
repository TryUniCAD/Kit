from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels
from convert.Formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from tests.Convert.Api.Fusion.LegacyAppearance.CheckFields import CheckFields


# a real pinned native declaration independently constrains the receiving codec
def NativeFields() -> tuple[PropertySpec, ...]:
    RootPath = FilePath(__file__).resolve().parents[5]
    Source = RootPath / "re/Fusion/SavedCuboidRoundTrip/Corpus/BaselineControl.f3d"
    Payload = Source.read_bytes()
    assert (
        HashBytes(Payload).hexdigest()
        == "5f9ad382c5e4b15313a59bebe4201ccd5b87137a3f20ebe85f5e3fba79148ca0"
    )
    Native = ReadDocument(Payload)
    assert len(Native.Materials) == 1
    Package = Native.Materials[0].Package
    Assets = tuple(
        Entry for Entry in Package.Assets if Entry.SchemaName == "GenericSchema"
    )
    assert len(Assets) == 1
    Fields = BuildSchemas(SchemaModels(Package.Schemas))["GenericSchema"]
    CheckFields(Fields, Assets[0])
    return Fields
