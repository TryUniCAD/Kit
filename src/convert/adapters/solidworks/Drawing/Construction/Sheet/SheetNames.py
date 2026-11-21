from dataclasses import dataclass as DataClass


# sheet support names belong to authored intent rather than a captured native tree
@DataClass(frozen=True, slots=True)
class SheetNames:
    PlaneName: str
    ProfileName: str
    DetailName: str
