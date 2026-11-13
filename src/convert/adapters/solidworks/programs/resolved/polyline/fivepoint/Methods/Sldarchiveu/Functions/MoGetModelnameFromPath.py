from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8363, 1, 2401, "primitive:uchar", 0),
            (8368, 4, 2946, "primitive:long", 0),
            (8372, 4, 3007, "primitive:long", 0),
            (8376, 4, 3071, "primitive:long", 0),
            (8398, 4, 3084, "primitive:long", 0),
            (8402, 4, 3179, "primitive:long", 0),
            (8410, 4, 3633, "primitive:long", 0),
        ),
    },
)
