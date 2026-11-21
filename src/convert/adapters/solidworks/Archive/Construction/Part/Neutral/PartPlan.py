from typing import TypeAlias

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)

from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)

# the shared part archive consumes actual planar profiles without conflating their analytic geometry
KPartPlan: TypeAlias = BlindPlan | CirclePlan | ThroughStock
