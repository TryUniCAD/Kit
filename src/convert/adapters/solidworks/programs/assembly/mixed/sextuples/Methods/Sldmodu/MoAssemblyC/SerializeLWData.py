# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAssemblyC.SerializeLWData import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (4606, 1, 487, "primitive:uchar", 0),
            (4607, 1, 572, "primitive:uchar", 0),
        ),
    },
)
