from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoReferenceCurveC.Serialize import (
    KOwnerSites,
)

KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7154, 4, 3909, "primitive:ulong", 6),
            (7158, 4, 3928, "primitive:long", -1),
            (7162, 4, 3941, "primitive:long", 0),
            (7166, 4, 3954, "primitive:long", 0),
            (7170, 4, 3967, "primitive:ulong", 5),
            (7174, 4, 3986, "primitive:ulong", 5),
            (7182, 2, 4030, "primitive:ushort", 0),
            (7184, 4, 4154, "primitive:ulong", 4294967295),
            (7188, 4, 4250, "primitive:ulong", 0),
            (7196, 4, 4466, "primitive:long", 0),
            (7200, 4, 4482, "primitive:long", 0),
            (7204, 4, 4540, "primitive:long", 0),
        ),
    },
)
