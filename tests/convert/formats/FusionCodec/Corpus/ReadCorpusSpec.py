from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.NamedType import NamedType
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusData import ReadCorpusData
from tests.convert.formats.FusionCodec.Entities.ReadWire import ReadWire


def ReadCorpusSpec(FileName: str, Targets: tuple[ExternalTarget, ...]) -> EntityProfile:
    Value = ReadCorpusData()
    Entries = tuple(
        Value["Classes"][ClassKey]
        for ClassKey in Value["Profiles"][FileName]["Classes"]
    )
    Classes = tuple(
        ClassSchema(
            Entry["ClassGuid"],
            Entry["BaseGuid"],
            Entry["SchemaVersion"],
            tuple(
                FieldSpec(
                    Field["FieldName"], ReadWire(Field["ValueType"]), Field["IsSaved"]
                )
                for Field in Entry["Members"]
            ),
            Entry["IsValue"],
        )
        for Entry in Entries
    )
    NamedTypes = tuple(
        NamedType(Entry["TypeName"], ReadWire(Entry["ValueType"]))
        for Entry in Value["NamedTypes"]
    )
    return EntityProfile(Value["RootGuid"], Classes, Targets, NamedTypes)
