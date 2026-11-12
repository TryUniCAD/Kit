from importlib.resources import files as PackageFiles
from json import loads as ReadJson
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.SchemaData import (
    SchemaData,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def ReadSchemaNode(Value: SchemaData) -> SchemaNode:
    return SchemaNode(
        Value["TagName"],
        tuple((Entry[0], Entry[1]) for Entry in Value["Attributes"]),
        tuple(ReadSchemaNode(Child) for Child in Value["Children"]),
    )


def ReadMatSchema() -> tuple[SchemaNode, ...]:
    Resource = PackageFiles(
        "convert.formats.Fusion.DocumentCodec.Materials.Vocabulary"
    ).joinpath("MaterialSchemas.json")
    Values = CastValue(dict[str, SchemaData], ReadJson(Resource.read_bytes()))
    return tuple(ReadSchemaNode(Value) for Value in Values.values())
