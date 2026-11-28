from typing import TypeAlias

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)

# both proved contours use the same part model and archive streams
KPartPlan: TypeAlias = BlindPlan | CirclePlan
