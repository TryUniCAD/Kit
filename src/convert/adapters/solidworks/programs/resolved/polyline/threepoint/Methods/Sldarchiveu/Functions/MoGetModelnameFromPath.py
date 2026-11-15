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
            (7847, 1, 2401, "primitive:uchar", 0),
            (7852, 4, 2946, "primitive:long", 0),
            (7856, 4, 3007, "primitive:long", 0),
            (7860, 4, 3071, "primitive:long", 0),
            (7882, 4, 3084, "primitive:long", 0),
            (7886, 4, 3179, "primitive:long", 0),
            (7894, 4, 3633, "primitive:long", 0),
        ),
    },
)
