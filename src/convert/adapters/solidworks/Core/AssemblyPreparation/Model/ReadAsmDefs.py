from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmDef import (
    CheckAsmDef,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmConfig import (
    ReadAsmConfig,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument
from interchange.Records.RecordConfig import Configuration


# repeated occurrences need one uniquely owned child document and independent root and child configuration identities
def ReadAsmDefs(
    Document: CadDocument, GraphValue: AssemblyData, ConfigValue: Configuration
) -> tuple[ComponentDef, ComponentDef, CadDocument]:
    RequireAsm(
        len(GraphValue.definitions) == 2 and len(GraphValue.documents) == 1,
        "only one complete repeated direct part dependency is admitted",
    )
    Definitions = {Value.id: Value for Value in GraphValue.definitions}
    RootValue = Definitions[GraphValue.root_definition_id]
    (ChildValue,) = (
        Value for Value in GraphValue.definitions if Value.id != RootValue.id
    )
    RequireAsm(
        str(RootValue.kind) == "assembly"
        and RootValue.name == Document.metadata["name"]
        and str(ChildValue.kind) == "part",
        "definition kinds or root identity differ",
    )
    for Value in GraphValue.definitions:
        CheckAsmDef(Value)
    RequireAsm(
        not RootValue.document_id
        and not RootValue.body_ids
        and (RootValue.configuration_name, RootValue.configuration_id)
        == (ConfigValue.name, ConfigValue.id),
        "root definition ownership or configuration differs",
    )
    (Embedded,) = GraphValue.documents
    ChildDocument = Embedded.document
    RequireAsm(
        ChildValue.document_id == Embedded.id and ChildDocument.assembly is None,
        "the complete owned neutral part is missing",
    )
    RequireAsm(
        ChildValue.name == ChildDocument.metadata.get("name")
        and ChildValue.body_ids == tuple(Value.id for Value in ChildDocument.bodies),
        "child definition name or body references differ",
    )
    ChildConfig = ReadAsmConfig(ChildDocument)
    RequireAsm(
        (ChildValue.configuration_name, ChildValue.configuration_id)
        == (ChildConfig.name, ChildConfig.id),
        "child selected configuration differs",
    )
    return RootValue, ChildValue, ChildDocument
