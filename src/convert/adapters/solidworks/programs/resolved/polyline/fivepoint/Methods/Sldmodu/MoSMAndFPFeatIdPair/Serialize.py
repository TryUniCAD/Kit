from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KOwnerSites,
)


KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (682, 1, 4524, "primitive:uchar", 0),
            (801, 1, 4524, "primitive:uchar", 0),
            (5679, 1, 4524, "primitive:uchar", 0),
            (7753, 1, 4524, "primitive:uchar", 0),
        ),
    },
)
