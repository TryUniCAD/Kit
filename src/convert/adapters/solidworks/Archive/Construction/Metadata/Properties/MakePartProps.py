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


# each ordinary text property scope yields its own computed package stream when present in the neutral model
def MakePartProps(InputsValue: PartTextInput | None) -> dict[str, bytes]:
    if InputsValue is None:
        return {}
    DocumentRows = ReadPropRows(InputsValue.DocumentFields)
    ConfigurationRows = ReadPropRows(InputsValue.ConfigurationFields)
    StreamsValue: dict[str, bytes] = {}
    if InputsValue.SummaryFields:
        StreamsValue["docProps/core.xml"] = MakeCoreProps(InputsValue.SummaryFields)
    if DocumentRows:
        StreamsValue["docProps/custom.xml"] = MakeCustomProps(DocumentRows, False)
    if ConfigurationRows:
        StreamsValue["docProps/Config-0-Properties.xml"] = MakeCustomProps(
            ConfigurationRows, True
        )
    return StreamsValue
