from collections.abc import Mapping
from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiTestPaths import KSamplePath

KMetadataCases = (
    "Canonical",
    "Alias",
    "Nested",
    "Tuple",
    "List",
    "Set",
    "FrozenSet",
    "EmptyBytes",
    "EmptyText",
    "NullValue",
    "NestedEmpty",
)


def BuildMetadata(RecordKind: str) -> CadDocument:
    Metadata: Mapping[str, object]
    if RecordKind in ("EmptyBytes", "EmptyText", "NullValue"):
        Metadata = {
            "solidworks_source_bytes": {
                "EmptyBytes": b"",
                "EmptyText": "",
                "NullValue": None,
            }[RecordKind]
        }
    elif RecordKind == "NestedEmpty":
        Metadata = {"analysis": {"solidworks_source_bytes": None}}
    else:
        Content = KSamplePath.read_bytes()
        Cases: dict[str, Mapping[str, object]] = {
            "Canonical": {"solidworks_source_bytes": Content},
            "Alias": {"vendor_archive": Content},
            "Nested": {"analysis": {"source": {"archive": Content}}},
            "Tuple": {"analysis": ("source", {"archive": Content})},
            "List": {"analysis": ["source", {"archive": Content}]},
            "Set": {"analysis": {Content}},
            "FrozenSet": {"analysis": frozenset((Content,))},
        }
        Metadata = Cases[RecordKind]
    return ReplaceData(
        MakeFusionDoc(DocumentSpec("Typed metadata history", "height", 20.0)),
        metadata=Metadata,
    )
