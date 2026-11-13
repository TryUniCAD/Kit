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
            (
                7644,
                20,
                "SketchOneFirstChainEntityIndices",
                "direct:5i",
                (4, 3, 2, 1, 5),
            ),
            (7666, 4, "SketchOneSecondChainEntityIndices", "direct:1i", 0),
        ),
    },
)
