from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# ordinary saved parts may retain an empty renderer wrapper without admitting appearance records
def CheckDefRender(FieldsValue: Mapping[str, object]) -> None:
    PresenceValue = FieldsValue.get("has_pwmaterial")
    RendererValue = FieldsValue.get("f1110")
    if type(PresenceValue) is not int or PresenceValue not in (0, 1):
        raise BodyUnsupported(
            "SOLIDWORKS part Definition has an alternate renderer marker"
        )
    if PresenceValue == 0:
        if RendererValue is not None:
            raise BodyUnsupported(
                "SOLIDWORKS part Definition has an inactive renderer owner"
            )
        return
    if (
        not isinstance(RendererValue, dict)
        or RendererValue.get("f08") != 6
        or RendererValue.get("f0c") != 0
    ):
        raise BodyUnsupported(
            "SOLIDWORKS part Definition has an alternate renderer profile"
        )
    ListValue = RendererValue.get("list")
    if (
        not isinstance(ListValue, dict)
        or ListValue.get("items") != []
        or ListValue.get("n", 0) != 0
    ):
        raise BodyUnsupported("SOLIDWORKS part Definition has renderer objects")
