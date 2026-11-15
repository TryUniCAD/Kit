from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoEdgeSurfIdKeeperC.Serialize import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8019, 4, 4055, "primitive:long", 0),
            (8165, 4, 4055, "primitive:long", 0),
            (8339, 4, 4055, "primitive:long", 0),
            (8409, 4, 4055, "primitive:long", 0),
        ),
    },
)
