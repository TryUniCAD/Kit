from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.SuObArray.SerializePtr import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3427, 4, 100, "primitive:long", 0),
            (3431, 4, 100, "primitive:long", 0),
            (3445, 4, 100, "primitive:long", 0),
            (3471, 4, 100, "primitive:long", 0),
            (3946, 4, 100, "primitive:long", 0),
            (3950, 4, 100, "primitive:long", 0),
            (3964, 4, 100, "primitive:long", 0),
            (3990, 4, 100, "primitive:long", 0),
            (4516, 4, 100, "primitive:long", 0),
            (4520, 4, 100, "primitive:long", 0),
            (4534, 4, 100, "primitive:long", 0),
            (4560, 4, 100, "primitive:long", 0),
            (8118, 4, 100, "primitive:long", 1),
            (8126, 4, 100, "primitive:long", 0),
            (8144, 4, 100, "primitive:long", 0),
            (9085, 4, 100, "primitive:long", 0),
            (9313, 4, 100, "primitive:long", 0),
            (9464, 4, 100, "primitive:long", 0),
            (10552, 4, 100, "primitive:long", 0),
            (10556, 4, 100, "primitive:long", 0),
        ),
    },
)
