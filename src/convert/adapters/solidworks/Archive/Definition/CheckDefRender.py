from collections.abc import Mapping

from convert.adapters.base.ContractCompat import IsObjectDict
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# each ordinary document kind has its own measured empty renderer wrapper
def CheckDefRender(
    FieldsValue: Mapping[str, object], *, Assembly: bool = False
) -> None:
    KindValue = "assembly" if Assembly else "part"
    PresenceValue = FieldsValue.get("has_pwmaterial")
    RendererValue = FieldsValue.get("f1110")
    if type(PresenceValue) is not int or PresenceValue not in (0, 1):
        raise BodyUnsupported(
            f"SOLIDWORKS {KindValue} Definition has an alternate renderer marker"
        )
    if PresenceValue == 0:
        if RendererValue is not None:
            raise BodyUnsupported(
                f"SOLIDWORKS {KindValue} Definition has an inactive renderer owner"
            )
        return
    if (
        not IsObjectDict(RendererValue)
        or RendererValue.get("f08") != (1 if Assembly else 6)
        or RendererValue.get("f0c") != 0
    ):
        raise BodyUnsupported(
            f"SOLIDWORKS {KindValue} Definition has an alternate renderer profile"
        )
    ListValue = RendererValue.get("list")
    if (
        not IsObjectDict(ListValue)
        or ListValue.get("items") != []
        or ListValue.get("n", 0) != 0
    ):
        raise BodyUnsupported(f"SOLIDWORKS {KindValue} Definition has renderer objects")
