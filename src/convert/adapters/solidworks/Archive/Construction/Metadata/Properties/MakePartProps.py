from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakeCoreProps import (
    MakeCoreProps,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakeCustomProps import (
    MakeCustomProps,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.ReadPropRows import (
    ReadPropRows,
)
from convert.adapters.solidworks.Archive.Properties.WriteEmptyProps import (
    WriteEmptyProps,
)


# each ordinary text property scope yields its own computed package stream when present in the neutral model
def MakePartProps(InputsValue: PartTextInput | None) -> dict[str, bytes]:
    if InputsValue is None:
        return {}
    EmptyScopes = InputsValue.EmptyScopes
    if EmptyScopes - {"summary", "document", "configuration"}:
        raise ValueError("part text names an unknown empty property scope")
    DocumentRows = ReadPropRows(InputsValue.DocumentFields)
    ConfigurationRows = ReadPropRows(InputsValue.ConfigurationFields)
    StreamsValue: dict[str, bytes] = {}
    if InputsValue.SummaryFields or "summary" in EmptyScopes:
        StreamsValue["docProps/core.xml"] = MakeCoreProps(InputsValue.SummaryFields)
    if DocumentRows or "document" in EmptyScopes:
        StreamsValue["docProps/custom.xml"] = MakeCustomProps(DocumentRows, False)
    if ConfigurationRows or "configuration" in EmptyScopes:
        StreamsValue["docProps/Config-0-Properties.xml"] = MakeCustomProps(
            ConfigurationRows, True
        )
    if InputsValue.HasEmptyFileOwner:
        StreamsValue["Contents/CusProps"] = WriteEmptyProps(19000)
    return StreamsValue
