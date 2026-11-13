from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgDim.Serialize import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5355, 4, 494, "primitive:long", 17),
            (5359, 2, 516, "primitive:ushort", 2),
            (5361, 2, 539, "primitive:ushort", 0),
            (5363, 2, 576, "primitive:ushort", 0),
        ),
    },
)
