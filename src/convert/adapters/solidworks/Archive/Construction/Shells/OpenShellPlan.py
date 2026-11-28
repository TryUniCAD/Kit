from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)


# a shell keeps the stock topology and the wall driver as independent construction inputs
@DataClass(frozen=True, slots=True)
class OpenShellPlan:
    StockValue: BlindPlan
    FeatureName: str
    ThicknessM: float
