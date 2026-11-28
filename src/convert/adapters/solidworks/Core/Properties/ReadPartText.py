from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Properties.ReadPropManager import (
    ReadPropManager,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.PartTextData import PartTextData
from convert.adapters.solidworks.Core.Properties.ReadConfigProps import ReadConfigProps
from convert.adapters.solidworks.Core.Properties.ReadCoreProps import ReadCoreProps
from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps
from convert.adapters.solidworks.Core.Properties.ReadLegacyEmptyProps import (
    ReadLegacyProps,
)
from interchange.document.Models.DocumentModel import CadDocument


# all optional property scopes must qualify together before any dictionary reaches the public document
def ReadPartText(
    Document: CadDocument,
    Archive: SldprtArchive,
    *,
    LinkedConfig: ConfigGraph | None = None,
) -> PartTextData | None:
    VersionValue = ContainerMo(Archive.streams)
    if VersionValue == 18000:
        ReadLegacyProps(Archive)
        return None
    if VersionValue != 19000:
        raise ValueError("part text properties require ordinary archive version 19000")
    ManagerValue = Archive.get("Contents/CusProps")
    if ManagerValue is not None:
        ReadPropManager(ManagerValue, VersionValue, SavedEmpty=LinkedConfig is not None)
    SummaryValue = Archive.get("docProps/core.xml")
    DocumentValue = Archive.get("docProps/custom.xml")
    SummaryFields = None if SummaryValue is None else ReadCoreProps(SummaryValue)
    DocumentFields = (
        None if DocumentValue is None else ReadCustomProps(DocumentValue, False)
    )
    ConfigFields = ReadConfigProps(Document, Archive, VersionValue)
    if SummaryFields is None and DocumentFields is None and not ConfigFields:
        return None
    GraphValue = LinkedConfig if LinkedConfig is not None else ReadPartConfig(Archive)
    if ConfigFields and (
        GetFileRef(GraphValue.HeaderValue.FieldsValue.get("f38")).ConfigValue
        != Document.configurations[0].name
    ):
        raise ValueError(
            "part configuration properties differ from the saved ModelHeader name"
        )
    return PartTextData(SummaryFields, DocumentFields, ConfigFields)
