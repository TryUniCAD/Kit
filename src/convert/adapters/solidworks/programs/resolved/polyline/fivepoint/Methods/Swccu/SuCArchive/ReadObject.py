from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8473, 4, 372, "primitive:long", 5),
            (8493, 4, 372, "primitive:long", 4),
            (8513, 4, 372, "primitive:long", 3),
            (8533, 4, 372, "primitive:long", 2),
            (8553, 4, 372, "primitive:long", 1),
            (8659, 4, 372, "primitive:long", 5),
            (8679, 4, 372, "primitive:long", 1),
            (8699, 4, 372, "primitive:long", 2),
            (8719, 4, 372, "primitive:long", 3),
            (8739, 4, 372, "primitive:long", 4),
            (9095, 4, 372, "primitive:long", 7),
        ),
    },
)
