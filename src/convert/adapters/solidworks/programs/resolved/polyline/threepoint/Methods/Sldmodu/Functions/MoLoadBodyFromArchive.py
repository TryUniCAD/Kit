from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5634, 1, 119, "primitive:uchar", 1),
            (7212, 1, 119, "primitive:uchar", 1),
        ),
    },
)
