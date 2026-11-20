from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Ends.ReadEndMode import IsEndListEmpty
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from interchange.Features.FeatureExtrude import ExtrudeEnd


# role checks exclude joins and alternate ends before body pointers define the portable history
def CheckStockMode(
    OwnerValue: ExtrudeOwner, ProfileValue: ArchiveNode, SolidMode: int
) -> None:
    IsCut = SolidMode == 1
    Fields = OwnerValue.NodeValue.FieldsValue
    EndFields = OwnerValue.EndValue.FieldsValue
    Flags = Fields.get("f28")
    if (
        OwnerValue.ParentsValue != (ProfileValue,)
        or OwnerValue.ProfileValue is not ProfileValue
        or OwnerValue.ModeValue != (ExtrudeEnd.KThroughAll if IsCut else ExtrudeEnd.KBlind)
        or OwnerValue.IsReversed != IsCut
        or OwnerValue.SecondModeValue is not None
        or Fields.get("f810") != SolidMode
        or type(Flags) is not int
        or Flags & 0x7FFFFFFF != (0x400201CA if IsCut else 0x40000140)
        or Fields.get("f838") != 0.0
        or Fields.get("f6e0") is not None
        or Fields.get("f758") is not None
        or Fields.get("f7a0") != 0
        or not IsLineState(Fields.get("f780"))
        or any(
            EndFields.get(NameValue) is not None
            for NameValue in ("f20", "fc8", "fd0", "f138", "f90")
        )
        or not all(
            IsEndListEmpty(EndFields, NameValue) for NameValue in ("f28", "f48")
        )
    ):
        raise ValueError("two stock lineage has an alternate profile or extrusion mode")
    if not IsCut and (Fields.get("f544") != 0 or Fields.get("has_f548") != 0):
        raise ValueError("independent stock retains unsupported selection scope")
