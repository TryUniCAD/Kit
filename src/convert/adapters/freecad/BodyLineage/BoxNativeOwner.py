from dataclasses import dataclass as MakeDataClass
from uuid import UUID
from xml.etree.ElementTree import Element as XmlElement

from convert.adapters.freecad.BodyLineage.CheckBoxParams import CheckBoxParams
from convert.adapters.freecad.Native import (
    LoadNative,
    NativeArchive,
    NativeObject,
    NativeObjectA,
    NativeSource,
    TransformA,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentPayload import GetPayloadIds
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.Payloads.PayloadRoles import PayloadRole


# the supplied document and archive objects must prove the same actual ownership
@MakeDataClass(frozen=True, slots=True)
class BoxNativeOwner:
    ArchiveValue: NativeArchive
    BodyObject: NativeObject
    ChildObject: NativeObject
    BodyValue: DesignBody
    FeatureValue: FeatureStep
    DocumentUuid: str


# the source document binding locates one authenticated in memory native archive
def ReadBoxArchive(Document: CadDocument) -> NativeArchive:
    Source = Document.source
    if (
        Source.format_id != "freecad.fcstd"
        or Source.container_version != "1"
        or Source.attributes != {"freecad_schema_version": "4"}
        or not Source.application_version.startswith(("1.0R", "1.1R"))
        or Document.units != "mm"
    ):
        raise ValueError("unsupported FreeCAD origin box source schema or release")
    DocumentIds = GetPayloadIds(Document)
    Payloads = tuple(Document.brep_payloads[Index] for Index in DocumentIds)
    Documents = tuple(
        Value for Value in Payloads if Value.role is PayloadRole.KDocument
    )
    if len(Payloads) != 2 or len(Documents) != 1 or Documents[0].data is None:
        raise ValueError("FreeCAD origin box has no exact retained document binding")
    DataValue = Documents[0].data
    ArchiveValue = LoadNative(DataValue)
    if NativeSource(DataValue, Source.path, ArchiveValue) != Source:
        raise ValueError(
            "FreeCAD origin box source metadata disagrees with its archive"
        )
    return ArchiveValue


# the actual document identity must come from its typed archive property
def ReadBoxUuid(ArchiveValue: NativeArchive) -> str:
    Properties = ArchiveValue.root.findall("./Properties/Property[@name='Uid']")
    if len(Properties) != 1 or Properties[0].get("type") != "App::PropertyUUID":
        raise ValueError("FreeCAD origin box has no unique document UUID property")
    Nodes = list(Properties[0])
    if len(Nodes) != 1 or Nodes[0].tag != "Uuid":
        raise ValueError("FreeCAD origin box has an unsupported document UUID owner")
    ValueText = Nodes[0].get("value", "")
    if str(UUID(ValueText)) != ValueText:
        raise ValueError("FreeCAD origin box has a noncanonical document UUID")
    return ValueText


# single local link records exclude fallback list and external reference meanings
def ReadLocalLink(Owner: NativeObject, NameValue: str) -> str:
    LinkValue = ReadBoxScalar(Owner, NameValue, "App::PropertyLink", "Link")
    if set(LinkValue.attrib) != {"value"}:
        raise ValueError("FreeCAD origin box has a nonlocal or ambiguous owner link")
    return LinkValue.attrib["value"]


# one native property tag must own its scalar without a competing child
def ReadBoxScalar(
    Owner: NativeObject, NameValue: str, TypeName: str, NodeName: str
) -> XmlElement:
    PropValue = Owner.properties[NameValue]
    Nodes = list(PropValue)
    if (
        PropValue.get("type") != TypeName
        or len(Nodes) != 1
        or Nodes[0].tag != NodeName
        or len(Nodes[0])
    ):
        raise ValueError("FreeCAD origin box has an ambiguous native scalar owner")
    return Nodes[0]


# body membership and the tip must both identify the same actual child
def CheckNativeTip(BodyObj: NativeObject, Child: NativeObject) -> None:
    GroupProp = BodyObj.properties["Group"]
    GroupNodes = list(GroupProp)
    if (
        GroupProp.get("type") != "App::PropertyLinkList"
        or len(GroupNodes) != 1
        or GroupNodes[0].tag != "LinkList"
        or GroupNodes[0].attrib != {"count": "1"}
    ):
        raise ValueError("FreeCAD origin box has an ambiguous native body group")
    Links = list(GroupNodes[0])
    if (
        len(Links) != 1
        or Links[0].tag != "Link"
        or Links[0].attrib != {"value": Child.name}
        or len(Links[0])
        or ReadLocalLink(BodyObj, "Tip") != Child.name
        or ReadLocalLink(BodyObj, "BaseFeature")
        or ReadLocalLink(Child, "BaseFeature")
    ):
        raise ValueError("FreeCAD body group and tip do not own the same base free box")


# raw placement nodes must explicitly agree with the fixed primitive frame
def CheckBoxPlace(Owner: NativeObject, PropName: str) -> None:
    PlaceValue = ReadBoxScalar(
        Owner, PropName, "App::PropertyPlacement", "PropertyPlacement"
    )
    Fields = ("Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3", "A", "Ox", "Oy", "Oz")
    if set(PlaceValue.attrib) != set(Fields):
        raise ValueError("FreeCAD origin box has incomplete placement fields")
    Values = tuple(float(PlaceValue.attrib[NameValue]) for NameValue in Fields)
    if (
        Values != (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        or TransformA(PlaceValue) != KTransformIdentity
    ):
        raise ValueError("FreeCAD origin box has an alternate attachment or placement")


# supported owner links must not silently skip an attached primitive or another stock
def CheckBoxAttach(BodyObj: NativeObject, Child: NativeObject) -> None:
    Attachment = Child.properties["AttachmentSupport"]
    Support = list(Attachment)
    ModeValue = ReadBoxScalar(Child, "MapMode", "App::PropertyEnumeration", "Integer")
    if (
        Child.dependencies != (BodyObj.name,)
        or ModeValue.attrib != {"value": "0"}
        or Attachment.get("type") != "App::PropertyLinkSubList"
        or len(Support) != 1
        or Support[0].tag != "LinkSubList"
        or Support[0].attrib != {"count": "0"}
        or len(Support[0])
        or "Support" in Child.properties
    ):
        raise ValueError("FreeCAD origin box has an alternate attachment or placement")
    CheckBoxPlace(BodyObj, "Placement")
    CheckBoxPlace(Child, "Placement")
    CheckBoxPlace(Child, "AttachmentOffset")


# indexed child rows need actual distinct numeric archive object identities
def ReadBoxXmlId(Owner: NativeObject) -> int:
    ValueText = Owner.object_id
    if (
        not ValueText.isascii()
        or not ValueText.isdecimal()
        or ValueText.startswith("0")
    ):
        raise ValueError("FreeCAD origin box has an invalid archive object id")
    return int(ValueText)


# matching full retained records prevents body labels from substituting different owners
def FindBoxObject(
    ArchiveValue: NativeArchive, RecordValue: object, TypeName: str
) -> NativeObject:
    Candidates = tuple(
        Value
        for Value in ArchiveValue.objects
        if Value.type_id == TypeName and NativeObjectA(Value) == RecordValue
    )
    if len(Candidates) != 1:
        raise ValueError(
            "FreeCAD neutral record does not identify a unique archive owner"
        )
    return Candidates[0]


# matching the strict neutral ids keeps the ownership join tied to the source reader
def CheckBoxIds(
    BodyValue: DesignBody,
    FeatureValue: FeatureStep,
    BodyObj: NativeObject,
    Child: NativeObject,
) -> None:
    if (
        BodyValue.id != f"freecad:body:{BodyObj.name}"
        or FeatureValue.id != f"freecad:feature:{Child.name}"
        or BodyValue.provenance is None
        or FeatureValue.provenance is None
        or BodyValue.provenance.native_id != BodyObj.name
        or FeatureValue.provenance.native_id != Child.name
        or BodyValue.attributes.get("tip") != Child.name
    ):
        raise ValueError(
            "FreeCAD origin box neutral ownership differs from its archive"
        )


# one actual shared feature timeline limits this association to its witnessed source
def ReadBoxOwners(Document: CadDocument) -> BoxNativeOwner:
    if (
        Document.brep is None
        or len(Document.bodies) != 1
        or len(Document.feature_timeline) != 1
        or Document.assembly is not None
    ):
        raise ValueError(
            "FreeCAD origin box lineage requires one actual solid and primitive"
        )
    (BodyValue,) = Document.bodies
    (FeatureValue,) = Document.feature_timeline
    Definition = FeatureValue.definition
    if (
        not isinstance(Definition, NativeFeature)
        or Definition.format_id != Document.source.format_id
        or Definition.type_id != "PartDesign::AdditiveBox"
        or FeatureValue.suppressed
        or FeatureValue.sketch_id is not None
        or FeatureValue.input_feature_ids
        or FeatureValue.selection_ids
        or BodyValue.final_feature_id != FeatureValue.id
    ):
        raise ValueError(
            "FreeCAD origin box lineage requires its actual active AdditiveBox"
        )
    ArchiveValue = ReadBoxArchive(Document)
    BodyObj = FindBoxObject(
        ArchiveValue, BodyValue.attributes.get("freecad"), "PartDesign::Body"
    )
    Child = FindBoxObject(ArchiveValue, Definition.object_data, Definition.type_id)
    CheckBoxIds(BodyValue, FeatureValue, BodyObj, Child)
    CheckNativeTip(BodyObj, Child)
    CheckBoxAttach(BodyObj, Child)
    CheckBoxParams(Document.parameters, Child, FeatureValue)
    return BoxNativeOwner(
        ArchiveValue, BodyObj, Child, BodyValue, FeatureValue, ReadBoxUuid(ArchiveValue)
    )
