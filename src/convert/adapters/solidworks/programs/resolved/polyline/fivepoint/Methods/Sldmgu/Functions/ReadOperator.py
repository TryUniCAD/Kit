from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmgu.Functions.ReadOperator import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5528, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (5536, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (5544, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (7519, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (7527, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (7535, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (10978, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (10986, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (10994, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (11034, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (11042, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (11050, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
