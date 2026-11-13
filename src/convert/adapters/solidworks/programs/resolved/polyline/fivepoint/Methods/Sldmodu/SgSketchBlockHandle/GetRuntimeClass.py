from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5594, 4, 15663, "primitive:long", 0),
            (5598, 4, 15826, "primitive:long", 0),
            (5602, 4, 16481, "primitive:long", 0),
            (7585, 4, 15663, "primitive:long", 0),
            (7589, 4, 15826, "primitive:long", 0),
            (7593, 4, 16481, "primitive:long", 0),
        ),
    },
)
