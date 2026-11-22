from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import (
    ReadOccName,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlPoseText import (
    XmlPoseText,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# reference xml retains actual occurrence identity and selected child configuration while reporting only the qualified ordinary resolved visible rigid profile
def XmlRefAttrs(
    Reference: ArchiveNode, ObjectId: int, ModelId: int = 5
) -> dict[str, str]:
    BaseValue, NumberValue = ReadOccName(ReadNodeName(Reference))
    ConfigValue = FieldRecord(Reference.FieldsValue["f3c0"])
    return {
        "id": str(ObjectId),
        "swName": BaseValue,
        "swReferenceNumber": NumberValue,
        "swComponentReference": "",
        "swComponentName": BaseValue,
        "swID": str(Reference.FieldsValue["f08"]),
        "swIsVirtualComponent": "NO",
        "swConfigurationId": str(ConfigValue["f10"]),
        "swConfigurationName": str(ConfigValue["f08"]),
        "swSuppressed": "NO",
        "swHidden": "NO",
        "swFlexible": "NO",
        "swExcludeFromBOM": "NO",
        "swZone": "NO",
        "swModelRef": str(ModelId),
        "swTransform": XmlPoseText(Reference),
        "swTransformStamp": str(Reference.FieldsValue["f3f0"]),
    }
