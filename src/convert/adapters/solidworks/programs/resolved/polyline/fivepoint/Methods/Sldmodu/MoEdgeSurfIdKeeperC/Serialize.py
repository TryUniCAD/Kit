from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoEdgeSurfIdKeeperC.Serialize import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8575, 4, 4055, "primitive:long", 0),
            (8761, 4, 4055, "primitive:long", 0),
            (8939, 4, 4055, "primitive:long", 0),
            (9013, 4, 4055, "primitive:long", 0),
        ),
    },
)
