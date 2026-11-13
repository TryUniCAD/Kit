from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRefPlnDataC.SerializePlaneData import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (3638, 8, 541, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (3680, 8, 773, "primitive:double", float.fromhex("0x1.a786c226809d5p-6")),
            (3688, 8, 856, "primitive:double", float.fromhex("-0x1.a786c226809d5p-6")),
            (3696, 8, 910, "primitive:double", float.fromhex("0x1.205bc01a36e2fp-6")),
            (3704, 8, 964, "primitive:double", float.fromhex("-0x1.205bc01a36e2fp-6")),
            (3714, 4, 1160, "primitive:long", 0),
            (3718, 4, 1233, "primitive:long", -4),
            (3722, 4, 1254, "primitive:long", -4),
            (3726, 1, 1461, "primitive:uchar", 0),
            (3751, 4, 1719, "primitive:long", 1),
            (3755, 4, 1790, "primitive:long", 0),
            (3759, 2, 1855, "primitive:ushort", 0),
            (4132, 8, 541, "primitive:double", float.fromhex("0x0.0p+0")),
            (4246, 8, 773, "primitive:double", float.fromhex("0x1.a786c226809d5p-6")),
            (4254, 8, 856, "primitive:double", float.fromhex("-0x1.a786c226809d5p-6")),
            (4262, 8, 910, "primitive:double", float.fromhex("0x1.4467381d7dbf4p-8")),
            (4270, 8, 964, "primitive:double", float.fromhex("-0x1.4467381d7dbf4p-8")),
            (4280, 4, 1160, "primitive:long", 0),
            (4284, 4, 1233, "primitive:long", -4),
            (4288, 4, 1254, "primitive:long", -4),
            (4292, 1, 1461, "primitive:uchar", 0),
            (4317, 4, 1719, "primitive:long", 1),
            (4321, 4, 1790, "primitive:long", 0),
            (4325, 2, 1855, "primitive:ushort", 0),
            (4702, 8, 541, "primitive:double", float.fromhex("0x0.0p+0")),
            (4816, 8, 773, "primitive:double", float.fromhex("0x1.4467381d7dbf4p-8")),
            (4824, 8, 856, "primitive:double", float.fromhex("-0x1.4467381d7dbf4p-8")),
            (4832, 8, 910, "primitive:double", float.fromhex("0x1.205bc01a36e2fp-6")),
            (4840, 8, 964, "primitive:double", float.fromhex("-0x1.205bc01a36e2fp-6")),
            (4850, 4, 1160, "primitive:long", 0),
            (4854, 4, 1233, "primitive:long", -4),
            (4858, 4, 1254, "primitive:long", -4),
            (4862, 1, 1461, "primitive:uchar", 0),
            (4887, 4, 1719, "primitive:long", 1),
            (4891, 4, 1790, "primitive:long", 0),
            (4895, 2, 1855, "primitive:ushort", 0),
        ),
    },
)
