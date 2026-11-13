from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoArrowSizeC.Serialize import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2131, 8, 12508, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2139, 8, 12524, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2149, 4, 12830, "primitive:long", 0),
            (2153, 4, 13006, "primitive:long", 0),
        ),
    },
)
