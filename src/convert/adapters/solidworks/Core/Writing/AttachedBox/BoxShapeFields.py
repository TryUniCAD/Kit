from convert.adapters.freecad.BodyLineage.BoxNativeOwner import ReadBoxScalar
from convert.adapters.freecad.Native import NativeArchive, NativeObject
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole


# each audited cache must be the actual archive member of its one source property
def BoxShapeFields(
    ArchiveValue: NativeArchive,
    OwnerValue: NativeObject,
    PropertyName: str,
    PayloadValue: BrepPayload,
) -> bytes:
    PartValue = ReadBoxScalar(
        OwnerValue, PropertyName, "Part::PropertyPartShape", "Part"
    )
    if set(PartValue.attrib) != {"file"}:
        raise ValueError("FreeCAD attached shape has an unsupported member owner")
    MemberName = PartValue.attrib["file"]
    SourceValue = ArchiveValue.entries.get(MemberName)
    Attributes = PayloadValue.attributes
    if (
        not SourceValue
        or PayloadValue.role is not PayloadRole.KBrep
        or PayloadValue.format_id != "opencascade"
        or PayloadValue.source_stream != MemberName
        or PayloadValue.data != SourceValue
        or Attributes.get("freecad_object") != OwnerValue.name
        or Attributes.get("freecad_property") != PropertyName
        or Attributes.get("freecad_part_attributes") != PartValue.attrib
        or "freecad_sidecars" in Attributes
        or PayloadValue.provenance is None
        or PayloadValue.provenance.native_id != f"{OwnerValue.name}.{PropertyName}"
    ):
        raise ValueError("FreeCAD attached shape disagrees with its actual property")
    return SourceValue
