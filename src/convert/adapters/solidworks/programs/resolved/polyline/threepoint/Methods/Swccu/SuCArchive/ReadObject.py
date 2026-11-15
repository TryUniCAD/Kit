from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7957, 4, 372, "primitive:long", 3),
            (7977, 4, 372, "primitive:long", 2),
            (7997, 4, 372, "primitive:long", 1),
            (8103, 4, 372, "primitive:long", 3),
            (8123, 4, 372, "primitive:long", 1),
            (8143, 4, 372, "primitive:long", 2),
            (8491, 4, 372, "primitive:long", 7),
        ),
    },
)
