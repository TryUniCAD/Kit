from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoThreedViewC.Serialize import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2369, 4, 4892, "primitive:long", 0),
            (2373, 4, 4957, "primitive:long", 0),
            (2587, 4, 4892, "primitive:long", 0),
            (2591, 4, 4957, "primitive:long", 0),
        ),
    },
)
