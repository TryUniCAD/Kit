from dataclasses import dataclass as DataClass


# the classic shader preserves its own reflectivity roughness and bump parameters
@DataClass(frozen=True, slots=True)
class ClassicLook:
    ShaderName: str
    MappingMode: int
    ColorForm: int
    Reflectivity: float
    Roughness: float
    BumpStrength: float
    Displacement: float
    DoubleSided: bool
    BumpIsNormal: bool
