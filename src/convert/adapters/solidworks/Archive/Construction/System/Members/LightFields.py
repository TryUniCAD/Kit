from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)


# semantic light setters determine the whole current tail without saved attribute dictionaries
def LightFields(InputValue: LightInput) -> dict[str, object]:
    Result: dict[str, object] = {
        "f35c": 0,
        "f0c": 0,
        "f390": InputValue.AmbientValue,
        "f398": InputValue.DiffuseValue,
        "f3a0": InputValue.SpecularValue,
        "f3a8": InputValue.ColourValue,
        "state": 0,
        "f428": 1,
        "f36c": 0,
        "f4f0": int(InputValue.UseCartesian),
        "f4f8": InputValue.ExternalName,
        "f384#0": int(InputValue.EnabledInPv),
        "f384": int(InputValue.EnabledInPv),
        "f388": int(InputValue.KeepInScene),
        "f478": InputValue.PvBrightness,
        "f488": int(InputValue.PvShadows),
        "f490": InputValue.PvQuality,
        "f500": {"n": 0, "props": []},
    }
    if InputValue.DirectionValue is not None:
        Result["f3b0"] = dict(
            zip(("x", "y", "z"), InputValue.DirectionValue, strict=True)
        )
        Result["f498"] = InputValue.ShadowSoftness
    return Result
