# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.core.ModelBase import ModelBase, ModelDataMut


# planar vectors keep sketch coordinates distinct from spatial geometry
@ModelDataMut
class PlaneVector(ModelBase):
    XCoord: float
    YCoord: float
