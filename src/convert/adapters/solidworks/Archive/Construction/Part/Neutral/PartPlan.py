from typing import TypeAlias

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)

# the shared part archive consumes either actual planar profile without conflating their analytic geometry
KPartPlan: TypeAlias = BlindPlan | CirclePlan
