from dataclasses import dataclass as MakeDataClass
from hashlib import sha256 as HashBytes
from xml.etree.ElementTree import Element as XmlElement

from convert.adapters.freecad.BodyLineage.BoxNativeOwner import BoxNativeOwner
from convert.adapters.freecad.Native import (
    BrepSidecars,
    ElemData,
    NativeArchive,
    NativeObject,
    ReadStringHash,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole


# two actual shape properties and their single sidecar define the qualified join
@MakeDataClass(frozen=True, slots=True)
class BoxShapeOwner:
    BodyShape: BrepPayload
    ChildShape: BrepPayload
    MapData: bytes


# a same named member cannot substitute for a document property that owns another shape
def FindShapeData(
    Document: CadDocument,
    OwnerData: BoxNativeOwner,
    ObjectValue: NativeObject,
    PropValue: XmlElement,
    PartValue: XmlElement,
    OwnerField: str,
    OwnerId: str,
) -> BrepPayload:
    FileName = PartValue.attrib["file"]
    SourceData = OwnerData.ArchiveValue.entries[FileName]
    Matches = tuple(
        Payload
        for Payload in Document.brep_payloads
        if Payload.role is PayloadRole.KBrep
        and Payload.attributes.get("freecad_object") == ObjectValue.name
        and Payload.attributes.get("freecad_property") == "Shape"
    )
    if len(Matches) != 1 or not SourceData:
        raise ValueError("FreeCAD box has an ambiguous or empty shape payload")
    (Payload,) = Matches
    Attributes = Payload.attributes
    if (
        Payload.source_stream != FileName
        or Payload.data != SourceData
        or Payload.sha256 != HashBytes(SourceData).hexdigest()
        or Attributes.get("freecad.native_document_sha256") != Document.source.sha256
        or Attributes.get("freecad_object_type") != ObjectValue.type_id
        or Attributes.get("freecad_property_data") != ElemData(PropValue)
        or Attributes.get("freecad_part_attributes") != PartValue.attrib
        or Attributes.get(OwnerField) != OwnerId
    ):
        raise ValueError(
            "FreeCAD shape payload disagrees with its actual document owner"
        )
    return Payload


# the optional legacy element map must carry no competing indexed names
def ReadBodyMapName(Nodes: list[XmlElement], ArchiveValue: NativeArchive) -> str:
    if tuple(Value.tag for Value in Nodes) != ("Part", "ElementMap", "ElementMap2"):
        raise ValueError("FreeCAD Body Shape lacks one actual ElementMap2 owner")
    PartValue, Legacy, Mapping = Nodes
    Markers = list(Legacy)
    if (
        PartValue.get("HasherIndex") != "0"
        or Legacy.attrib != {"new": "1", "count": "1"}
        or len(Markers) != 1
        or Markers[0].tag != "Element"
        or Markers[0].attrib != {"key": "Dummy", "value": "Dummy"}
        or len(Markers[0])
        or set(Mapping.attrib) != {"file"}
        or len(Mapping)
    ):
        raise ValueError("FreeCAD Body Shape has an ambiguous element map owner")
    Hasher = ReadStringHash(ArchiveValue)
    if Hasher is None or Hasher["entries"] != []:
        raise ValueError("FreeCAD Body Shape has unsupported string ids")
    return Mapping.attrib["file"]


# property structure must be explicit before a child member can be matched
def ReadShapeNodes(ObjectValue: NativeObject) -> tuple[XmlElement, list[XmlElement]]:
    PropValue = ObjectValue.properties["Shape"]
    Nodes = list(PropValue)
    if (
        PropValue.get("type") != "Part::PropertyPartShape"
        or not Nodes
        or Nodes[0].tag != "Part"
        or not Nodes[0].get("file")
        or len(Nodes[0])
    ):
        raise ValueError("FreeCAD box shape has no literal Part carrier")
    return PropValue, Nodes


# the native sidecar must still be present on the actual strict source shape
def BindBoxMap(
    OwnerData: BoxNativeOwner,
    BodyShape: BrepPayload,
    PropValue: XmlElement,
    MapName: str,
) -> bytes:
    Entries = OwnerData.ArchiveValue.entries
    MapData = Entries[MapName]
    Sidecars = BrepSidecars(PropValue, BodyShape.source_stream, Entries)
    if (
        Sidecars != [{"source_stream": MapName, "data": MapData}]
        or BodyShape.attributes.get("freecad_sidecars") != Sidecars
    ):
        raise ValueError("FreeCAD Body Shape has no exact retained map sidecar")
    return MapData


# the primitive identity must come from its real shape and body relationship
def ReadBoxShapes(Document: CadDocument, OwnerData: BoxNativeOwner) -> BoxShapeOwner:
    BodyProp, BodyNodes = ReadShapeNodes(OwnerData.BodyObject)
    ChildProp, ChildNodes = ReadShapeNodes(OwnerData.ChildObject)
    MapName = ReadBodyMapName(BodyNodes, OwnerData.ArchiveValue)
    if (
        tuple(Value.tag for Value in ChildNodes) != ("Part", "ElementMap")
        or ChildNodes[1].attrib
        or len(ChildNodes[1])
    ):
        raise ValueError("FreeCAD origin box primitive has its own unqualified names")
    BodyShape = FindShapeData(
        Document,
        OwnerData,
        OwnerData.BodyObject,
        BodyProp,
        BodyNodes[0],
        "body_id",
        OwnerData.BodyValue.id,
    )
    ChildShape = FindShapeData(
        Document,
        OwnerData,
        OwnerData.ChildObject,
        ChildProp,
        ChildNodes[0],
        "feature_id",
        OwnerData.FeatureValue.id,
    )
    if (
        BodyShape.source_stream == ChildShape.source_stream
        or ChildShape.attributes.get("freecad_sidecars")
    ):
        raise ValueError("FreeCAD linked shapes must retain distinct property owners")
    return BoxShapeOwner(
        BodyShape, ChildShape, BindBoxMap(OwnerData, BodyShape, BodyProp, MapName)
    )
