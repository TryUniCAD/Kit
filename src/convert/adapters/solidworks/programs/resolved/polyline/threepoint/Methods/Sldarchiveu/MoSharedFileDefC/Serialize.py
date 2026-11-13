from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldarchiveu.MoSharedFileDefC.Serialize import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7827, 2, 973, "primitive:ushort", 2),
            (7829, 1, 995, "primitive:uchar", 0),
            (7846, 1, 1481, "primitive:uchar", 0),
        ),
    },
)
