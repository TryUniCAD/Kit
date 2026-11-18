from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from interchange.Features.FeatureExtrude import ExtrudeEnd


# one blind solid boss and a reversed blind solid cut define the proven body producing operations
def CheckCutModes(BossValue: ExtrudeOwner, CutValue: ExtrudeOwner) -> None:
    for OwnerValue, IsCut in ((BossValue, False), (CutValue, True)):
        Fields = OwnerValue.NodeValue.FieldsValue
        Flags = Fields.get("f28")
        if (
            OwnerValue.ModeValue != ExtrudeEnd.KBlind
            or OwnerValue.IsReversed is not IsCut
            or OwnerValue.ParentsValue != (OwnerValue.ProfileValue,)
            or Fields.get("f810") != (1 if IsCut else -1)
            or type(Flags) is not int
            or Flags & 0x7FFFFFFF != (0x400201CA if IsCut else 0x40000140)
            or Fields.get("f838") != 0.0
            or Fields.get("f6e0") is not None
            or Fields.get("f758") is not None
            or Fields.get("f7a0") != 0
            or not IsLineState(Fields.get("f780"))
        ):
            raise ValueError("cut history has an unsupported solid extrusion mode")
    if (
        BossValue.DepthValue.Parameter is CutValue.DepthValue.Parameter
        or BossValue.DepthValue.Dimension is CutValue.DepthValue.Dimension
        or BossValue.DepthValue.Dimension.FieldsValue.get("f50")
        == CutValue.DepthValue.Dimension.FieldsValue.get("f50")
    ):
        raise ValueError("boss and cut require distinct driving depth owners")
    if any(
        CutValue.EndValue.FieldsValue.get(NameValue) is not None
        for NameValue in ("f20", "fc8", "fd0")
    ):
        raise ValueError("ordinary blind cut has an alternate retained end control")
