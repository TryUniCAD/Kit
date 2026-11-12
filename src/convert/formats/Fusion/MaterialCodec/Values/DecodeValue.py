from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue
from convert.formats.Fusion.MaterialCodec.Values.DecodeScalar import DecodeScalar
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


def DecodeValue(ReaderMut: MaterialReader, Field: PropertySpec) -> KMaterialValue:
    if Field.IsMultiple:
        return tuple(
            DecodeScalar(ReaderMut, Field) for _ in range(ReaderMut.ReadCount())
        )
    return DecodeScalar(ReaderMut, Field)
