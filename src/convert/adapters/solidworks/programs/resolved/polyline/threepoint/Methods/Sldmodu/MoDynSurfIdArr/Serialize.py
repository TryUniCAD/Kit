from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDynSurfIdArr.Serialize import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7906, 4, 4583, "primitive:long", 0),
            (7910, 4, 4596, "primitive:long", 0),
            (8079, 4, 4583, "primitive:long", 1),
            (8083, 4, 4596, "primitive:long", 0),
        ),
    },
)
