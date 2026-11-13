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
            (8793, 4, 7169, "primitive:long", 1),
            (8821, 8, 7340, "primitive:double", float.fromhex("0x1.d7977cb19612cp-5")),
            (9023, 4, 7169, "primitive:long", 1),
            (9051, 8, 7340, "primitive:double", float.fromhex("0x1.d7977cb19612cp-5")),
        ),
    },
)
