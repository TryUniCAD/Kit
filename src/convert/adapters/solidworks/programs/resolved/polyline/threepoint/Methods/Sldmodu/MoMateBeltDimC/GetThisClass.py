from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoMateBeltDimC.GetThisClass import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9976, 4, 290, "primitive:ulong", 8),
            (9980, 4, 350, "primitive:ulong", 16),
            (9984, 4, 363, "primitive:ulong", 1),
            (9988, 4, 376, "primitive:ulong", 1),
        ),
    },
)
