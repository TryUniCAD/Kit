from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.BasicPbrInput import (
    BasicPbrInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.FreshDspbr import (
    FreshDspbr,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.LookScalar import (
    LookScalar,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PackLookRgb import (
    PackLookRgb,
)


# the nontextured basic shader publishes explicit optical values and derives its reflectance from refraction
def MakeBasicPbr(InputValue: BasicPbrInput) -> dict[str, object]:
    if (
        type(InputValue) is not BasicPbrInput
        or InputValue.VersionName != "2025x"
        or InputValue.ShaderType != "basic"
        or type(CastValue(object, InputValue.ThinWalled)) is not bool
        or type(CastValue(object, InputValue.NormalizeEmission)) is not bool
    ):
        raise ValueError("part rendering requires the opaque nontextured basic shader")
    FieldsValue = FreshDspbr()
    IorValue = LookScalar(InputValue.RefractionIndex, 1.0, 10.0)
    Contrast = LookScalar(IorValue - 1.0, 0.0, 9.0)
    SumValue = LookScalar(IorValue + 1.0, 2.0, 11.0)
    RatioValue = LookScalar(Contrast / SumValue, 0.0, 1.0)
    FieldsValue.update(
        f00=InputValue.VersionName,
        f08=InputValue.ShaderType,
        f28=LookScalar(InputValue.MetallicValue, 0.0, 1.0),
        f2c=LookScalar(InputValue.Roughness, 0.0, 1.0),
        f60=LookScalar(InputValue.SpecularValue, 0.0, 1.0),
        f7c=LookScalar(InputValue.SheenRoughness, 0.0, 1.0),
        fd4=IorValue,
        f12c=LookScalar(RatioValue * RatioValue, 0.0, 1.0),
        fe8=LookScalar(InputValue.AttenuationDistance, 0.0, 1e30),
        f104=LookScalar(InputValue.ThinFilmRefractionIndex, 1.0, 10.0),
        fd0=int(InputValue.ThinWalled),
        fcc=int(InputValue.NormalizeEmission),
    )
    ScaleValue = LookScalar(1.0 / 255.0, 0.0, 1.0)
    for FieldName, ColorValue in (
        ("f10", InputValue.AlbedoRgb),
        ("fdc", InputValue.AttenuationRgb),
        ("f70", InputValue.SheenRgb),
    ):
        _ = PackLookRgb(ColorValue)
        FieldsValue.update(
            {
                f"{FieldName}_{IndexValue}": LookScalar(
                    ChannelValue * ScaleValue, 0.0, 1.0
                )
                for IndexValue, ChannelValue in enumerate(ColorValue)
            }
        )
    return FieldsValue
