from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import PartGeometry
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BindThinDoc import BindThinDoc
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinOwner import ReadThinOwner
from interchange.document.Models.DocumentModel import CadDocument


# only a complete cold graph should replace its prior generic native projection
def WithThinDoc(
    DocumentValue: CadDocument, Archive: SldprtArchive, ConfigId: int | None,
    GeometryValue: PartGeometry | None,
) -> CadDocument:
    ClassNames = DocumentValue.metadata.get("native_class_names", ())
    if (
        ConfigId != 0 or not isinstance(ClassNames, tuple)
        or "moRevolutionThin_c" not in ClassNames or not IsCacheAbsent(Archive)
    ):
        return DocumentValue
    try:
        LinkValue = ReadNativeLink(Archive, ConfigId)
        Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        OwnerValue = ReadThinOwner(LinkValue, Manager)
        Projected = BindThinDoc(DocumentValue, LinkValue, OwnerValue)
        Projected.assert_valid()
        return Projected
    except (ValueError, TypeError, KeyError) as ErrorInfo:
        if GeometryValue is not None and GeometryValue.EvidenceValue.get("method") == "typed_parametric_thin_revolve":
            raise SldprtFormat("SOLIDWORKS thin body lacks its complete editable projection") from ErrorInfo
        return DocumentValue
