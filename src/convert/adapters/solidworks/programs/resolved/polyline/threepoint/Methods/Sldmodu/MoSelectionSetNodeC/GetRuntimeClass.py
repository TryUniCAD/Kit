from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSelectionSetNodeC.GetRuntimeClass import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": ((1105, 4, 851, "primitive:long", 1),),
    },
)
