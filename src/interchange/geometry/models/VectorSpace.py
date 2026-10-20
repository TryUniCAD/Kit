# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.core.ModelBase import ModelBase, ModelDataMut


# spatial vectors give every geometry subsystem one coordinate contract
@ModelDataMut
class SpaceVector(ModelBase):
    XCoord: float
    YCoord: float
    ZCoord: float
