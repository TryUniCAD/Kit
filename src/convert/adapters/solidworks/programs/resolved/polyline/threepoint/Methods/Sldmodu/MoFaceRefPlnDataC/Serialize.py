from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8197, 4, 7169, "primitive:long", 1),
            (8225, 8, 7340, "primitive:double", float.fromhex("0x1.b1f1afd131022p-5")),
            (8419, 4, 7169, "primitive:long", 1),
            (8447, 8, 7340, "primitive:double", float.fromhex("0x1.b1f1afd131022p-5")),
        ),
    },
)
