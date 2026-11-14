from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.SketchChainEntityIndices import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7136, 12, "SketchOneFirstChainEntityIndices", "direct:3i", (2, 1, 3)),
            (7150, 4, "SketchOneSecondChainEntityIndices", "direct:1i", 0),
        ),
    },
)
