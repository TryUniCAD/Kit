from dataclasses import dataclass as MakeDataClass


# drafted sections need their exact moments as well as volume and surface area
@MakeDataClass(frozen=True, slots=True)
class DraftMass:
    Volume: float
    Area: float
    Center: tuple[float, float, float]
    Inertia: tuple[float, float, float]
    CrossTerms: tuple[float, float, float]
