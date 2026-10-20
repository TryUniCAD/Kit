# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Owners.Synthetic.ModelHeaderUserAndLogPreamble import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram = (
    KOwnerSites,
    {
        "Contents/Config-0-ModelHeader": (
            (
                41,
                14,
                "ModelHeaderUserAndLogPreamble",
                "direct:7H",
                (1, 65279, 1279, 111, 100, 105, 110),
            ),
        ),
    },
)
