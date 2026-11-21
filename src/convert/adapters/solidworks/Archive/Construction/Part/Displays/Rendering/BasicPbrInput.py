from dataclasses import dataclass as DataClass


# the basic shader needs independent authored optical values that are absent from the material density model
@DataClass(frozen=True, slots=True)
class BasicPbrInput:
    VersionName: str
    ShaderType: str
    AlbedoRgb: tuple[int, int, int]
    AttenuationRgb: tuple[int, int, int]
    SheenRgb: tuple[int, int, int]
    MetallicValue: float
    Roughness: float
    SpecularValue: float
    SheenRoughness: float
    RefractionIndex: float
    AttenuationDistance: float
    ThinFilmRefractionIndex: float
    ThinWalled: bool
    NormalizeEmission: bool
