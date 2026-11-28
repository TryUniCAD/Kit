from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.solidworks.Container.Format import KAsmFormatId, KPartFormatId
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ColdConfig import (
    ColdConfig,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ColdNestedLeaf import (
    ColdNestedLeaf,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument, ComponentDoc
from interchange.Records.RecordConfig import Configuration


# only the source joined to each definition can supply its intended title configuration and portable part
def ReadColdMembers(
    Document: CadDocument,
) -> tuple[
    tuple[ComponentDef, ...], tuple[ComponentDoc, ...], dict[str, Configuration]
]:
    GraphValue = Document.assembly
    if GraphValue is None:
        raise ValueError("reopened nested member inventory is unavailable")
    Embedded = {Value.id: Value for Value in GraphValue.documents}
    Parts: list[ComponentDoc] = []
    Definitions: list[ComponentDef] = []
    Configs: dict[str, Configuration] = {}
    for Value in GraphValue.definitions:
        IsRoot = Value.id == GraphValue.root_definition_id
        IsPart = Value.kind == "part"
        Member = None if IsRoot else Embedded.pop(Value.document_id, None)
        if not IsRoot and Member is None:
            raise ValueError("reopened nested definition lacks its owned document")
        SourceValue = Document if Member is None else Member.document
        Locator = FilePath(SourceValue.source.path)
        if (
            SourceValue.source.format_id != (KPartFormatId if IsPart else KAsmFormatId)
            or not Locator.is_absolute()
            or Locator.stem != Value.name
            or str(Locator) != Value.source_path
        ):
            raise ValueError(
                "reopened nested member lacks its exact resolved source identity"
            )
        Config = ColdConfig(Value, SourceValue)
        Configs[Value.id] = Config
        if IsPart and Member is not None:
            Parts.append(
                ReplaceValue(Member, document=ColdNestedLeaf(SourceValue, Value.name))
            )
        Definitions.append(
            ReplaceValue(
                Value,
                document_id=Value.document_id if IsPart else "",
                configuration_id=Config.id,
                source_path="",
                source_format_id="",
                source_sha256="",
                bounding_box=None,
                attributes=FreezeMapping(),
                provenance=None,
            )
        )
    if Embedded:
        raise ValueError("reopened nested assembly has an unowned source document")
    return tuple(Definitions), tuple(Parts), Configs
