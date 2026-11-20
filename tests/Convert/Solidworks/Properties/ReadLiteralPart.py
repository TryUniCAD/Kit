from hashlib import sha256 as HashBytes
from io import BytesIO
from json import dumps as DumpJson
from pathlib import Path as FilePath
from sys import argv as Arguments

from convert import convert as ConvertDoc
from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Archive import EncodeClass
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive


# the strict conversion refusal must leave the destination stream intact
def RefusePartText(SourceData: FilePath | bytes) -> str:
    TargetValue = BytesIO(b"unchanged")
    try:
        _ = ConvertDoc(
            SourceData,
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


# the wheel control must cross the strict conversion boundary only after verifying text absence
def ReadLegacyText(SourcePath: FilePath) -> dict[str, object]:
    SourceData = SourcePath.read_bytes()
    TargetValue = BytesIO()
    Converted = ConvertDoc(
        SourcePath,
        TargetValue,
        source_format="solidworks.sldprt",
        destination_format="interchange.json",
        strict=True,
    )
    StreamsValue = SldprtArchive.from_bytes(SourceData).streams
    CoreValue = StreamsValue["docProps/core.xml"]
    ClosingTag = b"</cp:coreProperties>"
    if CoreValue.count(ClosingTag) != 1:
        raise ValueError("missing native legacy summary root")
    StreamsValue["docProps/core.xml"] = CoreValue.replace(
        ClosingTag, b"<dc:title>Authored legacy text</dc:title>" + ClosingTag
    )
    Unsupported = BuildSldprt(StreamsValue, Template=SourceData)
    StreamsValue["docProps/core.xml"] = CoreValue
    ManagerName = "Contents/CusProps"
    ManagerValue = StreamsValue[ManagerName]
    ActualTag = EncodeClass("moCusPropContainer_c", 1)
    if ManagerValue.count(ActualTag) != 1:
        raise ValueError("missing native keyed property owner")
    StreamsValue[ManagerName] = ManagerValue.replace(
        ActualTag, EncodeClass("moCusPropMgr_c", 1)
    )
    WrongOwner = BuildSldprt(StreamsValue, Template=SourceData)
    Rejected = OpenDocument(
        WrongOwner, source_format="solidworks.sldprt", include_tessellation=False
    )
    DiagnosticValue = next(
        ItemValue.message
        for ItemValue in Rejected.diagnostics
        if ItemValue.code == "solidworks.part_text_properties_unavailable"
    )
    if len(Rejected.bodies) != 1 or Rejected.brep is None:
        raise ValueError("binary property refusal lost the prior geometry")
    return {
        "source_sha256": HashBytes(SourceData).hexdigest(),
        "output_bytes": len(TargetValue.getvalue()),
        "status": Converted.document.metadata.get("solidworks.part_text_properties"),
        "unsupported": RefusePartText(Unsupported),
        "binary_refusal": RefusePartText(WrongOwner),
        "binary_diagnostic": DiagnosticValue,
    }


# the subprocess modes share the same native input locator
def RunLiteralText() -> None:
    SourcePath = FilePath(Arguments[1])
    print(
        DumpJson(
            ReadLegacyText(SourcePath)
            if "--legacy-empty" in Arguments[2:]
            else ReadLiteralPart(SourcePath, "--convert-refusal" in Arguments[2:])
        )
    )


if __name__ == "__main__":
    RunLiteralText()
