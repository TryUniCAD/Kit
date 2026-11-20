from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from pathlib import Path as FilePath
from sys import argv as Arguments

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
        "text": (
            DocumentValue.metadata["document_summary"],
            DocumentValue.metadata["custom_properties"],
            ConfigValue.attributes["custom_properties"],
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
    print(DumpJson(ReadLiteralPart(FilePath(Arguments[1]))))
