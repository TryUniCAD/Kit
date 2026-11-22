from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from pathlib import Path as FilePath

from convert import open_document as OpenDocument


# the fresh public read publishes property scopes and the active model identity together
def ReadLiteralPart(SourcePath: FilePath) -> dict[str, object]:
    DocumentValue = OpenDocument(
        SourcePath,
        source_format="solidworks.sldprt",
        strict=True,
        include_tessellation=False,
    )
    (ConfigValue,) = DocumentValue.configurations
    (BodyValue,) = DocumentValue.bodies
    BrepValue = DocumentValue.brep
    if BrepValue is None:
        raise ValueError("the literal text fixture must retain its actual geometry")
    return {
        "source_sha256": HashBytes(SourcePath.read_bytes()).hexdigest(),
        "status": DocumentValue.metadata["solidworks.part_text_properties"],
        "diagnostics": tuple(
            DiagnosticValue.code for DiagnosticValue in DocumentValue.diagnostics
        ),
        "text": (
            DocumentValue.metadata.get("document_summary"),
            DocumentValue.metadata.get("custom_properties"),
            ConfigValue.attributes.get("custom_properties"),
        ),
        "text_scopes": (
            "document_summary" in DocumentValue.metadata,
            "custom_properties" in DocumentValue.metadata,
            "custom_properties" in ConfigValue.attributes,
        ),
        "configuration": (
            ConfigValue.name,
            ConfigValue.active,
            ConfigValue.attributes["native_configuration_id"],
        ),
        "body": (
            BodyValue.id,
            BodyValue.topology.solid_count,
            len(BrepValue.bodies),
            sum(Region.solid for Region in BrepValue.regions),
        ),
    }


if __name__ == "__main__":
    CorpusPath = FilePath(__file__).resolve().parents[4] / "re/solidworks/v2026/corpus"
    print(
        DumpJson(
            ReadLiteralPart(CorpusPath / "part-properties/CircularProperties.SLDPRT")
        )
    )
