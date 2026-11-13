from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10632, 4, 1928, "primitive:long", 0),
            (10636, 4, 1948, "primitive:long", -1),
            (10640, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
