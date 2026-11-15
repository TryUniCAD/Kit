from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10028, 4, 1928, "primitive:long", 0),
            (10032, 4, 1948, "primitive:long", -1),
            (10036, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
