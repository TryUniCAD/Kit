from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLineVizC.Serialize import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5516, 4, 166, "primitive:int", -1),
            (5520, 4, 245, "primitive:int", 1),
            (7507, 4, 166, "primitive:int", -1),
            (7511, 4, 245, "primitive:int", 1),
        ),
    },
)
