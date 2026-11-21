from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.XmlWalkState import (
    XmlWalkState,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


# each reachable generated definition needs its own correctly typed file identity while repeated placements share the same xml file record
def AddTargetFiles(StateValue: XmlWalkState, HeaderValue: Element) -> None:
    for TargetValue in StateValue.FileValues:
        FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
        FileKey = ReadFileKey(FileValue)
        _ = SubElement(
            HeaderValue,
            "swFile",
            {
                "id": str(StateValue.NodeIds[id(TargetValue.RootValue)][1]),
                "swDocType": "ASSEMBLY" if FileKey[2] == 3 else "PART",
                "swCreationTime": str(FileKey[3]),
                "swPath": FileKey[1],
            },
        )
