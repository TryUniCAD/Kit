from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5572, 4, 37407, "primitive:long", 0),
            (5576, 4, 37407, "primitive:long", 0),
            (5580, 4, 37407, "primitive:long", 0),
            (5584, 4, 37407, "primitive:long", 0),
            (7563, 4, 37407, "primitive:long", 0),
            (7567, 4, 37407, "primitive:long", 0),
            (7571, 4, 37407, "primitive:long", 0),
            (7575, 4, 37407, "primitive:long", 0),
        ),
    },
)
