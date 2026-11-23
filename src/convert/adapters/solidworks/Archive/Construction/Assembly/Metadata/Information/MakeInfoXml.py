from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.AsmInfoInput import (
    AsmInfoInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.InfoDocValues import (
    InfoDocValues,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.InfoUnitValues import (
    InfoUnitValues,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.SetInfoRowsMut import (
    SetInfoRowsMut,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePropSection import (
    MakePropSection,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.WritePropXml import (
    WritePropXml,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import (
    KInformationNamespace,
    KPropertyValueNamespace,
)


# source comparison and the linked assembly builder need the same ordinary typed information encoding
def MakeInfoXml(
    RootValue: ArchiveNode,
    FilePath: str,
    HeaderPath: str,
    ConfigName: str,
    SavedAt: int,
    InputValue: AsmInfoInput,
) -> bytes:
    RequireRootNode(RootValue, "moAssembly_c")
    if type(InputValue) is not AsmInfoInput:
        raise ValueError("assembly information requires validated local settings")
    FieldsValue = InfoDocValues(
        FilePath, HeaderPath, ReadNodeName(RootValue), ConfigName, SavedAt, InputValue
    ) | InfoUnitValues(RootValue)
    XmlValue = Element(
        "Properties",
        {"xmlns": KInformationNamespace, "xmlns:vt": KPropertyValueNamespace},
    )
    SetInfoRowsMut(MakePropSection(XmlValue, True), FieldsValue)
    return WritePropXml(XmlValue)
