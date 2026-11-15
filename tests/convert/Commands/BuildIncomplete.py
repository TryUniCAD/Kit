from dataclasses import replace as ReplaceData

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.document.models.DocumentModel import CadDocument
from tests.interchange.fixtures.AssemblyFixture import BuildAssembly


def BuildIncomplete(RecordKind: str) -> CadDocument:
    Document = BuildAssembly()
    assert Document.assembly is not None
    Assembly = Document.assembly
    if RecordKind in (
        "MissingReference",
        "ExternalReference",
        "NativeComponent",
        "ResolvedReference",
        "SourceUnresolved",
    ):
        Definition = Assembly.definitions[-1]
        if RecordKind in ("MissingReference", "ExternalReference"):
            Definition = ReplaceData(
                Definition,
                kind=(
                    ComponentKind.KReference
                    if RecordKind == "MissingReference"
                    else ComponentKind.KPart
                ),
                document_id="",
                body_ids=(),
                source_path="missing.part",
            )
        elif RecordKind == "NativeComponent":
            Definition = ReplaceData(Definition, kind=ComponentKind.KNative)
        elif RecordKind == "SourceUnresolved":
            Definition = ReplaceData(Definition, attributes={"source_resolved": False})
        else:
            Definition = ReplaceData(Definition, kind=ComponentKind.KReference)
        Assembly = ReplaceData(
            Assembly, definitions=(*Assembly.definitions[:-1], Definition)
        )
    elif RecordKind == "TransformUnresolved":
        Instance = ReplaceData(
            Assembly.instances[0], attributes={"transform_resolved": False}
        )
        Assembly = ReplaceData(Assembly, instances=(Instance, *Assembly.instances[1:]))
    else:
        FieldName = (
            "transform_status"
            if RecordKind == "NativeTransforms"
            else "constraint_status"
        )
        Assembly = ReplaceData(
            Assembly,
            attributes={
                FieldName: (
                    "native-only" if RecordKind == "NativeTransforms" else "unresolved"
                )
            },
        )
    return ReplaceData(Document, assembly=Assembly)
