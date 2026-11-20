from hashlib import sha256 as HashBytes
from io import BytesIO
from json import dumps as DumpJson
from pathlib import Path as FilePath
from sys import argv as Arguments

from convert import convert as ConvertDoc
from convert import open_document as OpenDocument


# the strict conversion refusal must leave the destination stream intact
def RefusePartText(SourcePath: FilePath) -> str:
    TargetValue = BytesIO(b"unchanged")
    try:
        _ = ConvertDoc(
            SourcePath,
            TargetValue,
            source_format="solidworks.sldprt",
            destination_format="interchange.json",
            strict=True,
            include_tessellation=False,
        )
    except ValueError as ErrorInfo:
        if TargetValue.getvalue() != b"unchanged" or TargetValue.tell() != 0:
            raise ValueError(
                "conversion refusal changed the destination"
            ) from ErrorInfo
        return str(ErrorInfo)
    raise ValueError("strict conversion accepted unsupported literal text")


# the fresh public read publishes property scopes and the active model identity together
def ReadLiteralPart(SourcePath: FilePath, CheckConvert: bool) -> dict[str, object]:
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
    ReportValue: dict[str, object] = {
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
    if CheckConvert:
        ReportValue["conversion"] = RefusePartText(SourcePath)
    return ReportValue


if __name__ == "__main__":
    print(
        DumpJson(
            ReadLiteralPart(
                FilePath(Arguments[1]), "--convert-refusal" in Arguments[2:]
            )
        )
    )
