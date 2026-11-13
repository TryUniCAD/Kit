from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.LoadSketchInPlace import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5122, 4, 3308, "primitive:long", 1),
            (6041, 4, 3308, "primitive:long", 5),
        ),
    },
)
