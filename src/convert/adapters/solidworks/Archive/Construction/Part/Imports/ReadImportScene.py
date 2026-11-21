from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)


# ordinary local import lighting must preserve one explicit ordered scene with no inherited defaults
def ReadImportScene(
    AmbientValue: LightInput | None, LightValues: tuple[LightInput, ...]
) -> tuple[LightInput, ...]:
    if type(CastValue(object, LightValues)) is not tuple or (
        AmbientValue is not None and LightValues
    ):
        raise ValueError("local import requires one ordered authored light source")
    if AmbientValue is not None and (
        type(CastValue(object, AmbientValue)) is not LightInput
        or AmbientValue.KindValue != "ambient"
    ):
        raise ValueError("bare local import admits only a typed authored ambient light")
    Selected = (AmbientValue,) if AmbientValue is not None else LightValues
    if (
        len(Selected) not in (0, 1, 4)
        or any(
            type(CastValue(object, LightValue)) is not LightInput
            for LightValue in Selected
        )
        or tuple(LightValue.KindValue for LightValue in Selected)
        not in (
            (),
            ("ambient",),
            ("ambient", "directional", "directional", "directional"),
        )
    ):
        raise ValueError("local import scene is outside the ordinary light profile")
    return Selected
