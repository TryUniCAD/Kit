# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# orthogonal frames preserve placement without assuming one vendor coordinate convention
@ModelDataMut(
    DefaultMap={
        "Origin": SpaceVector(0.0, 0.0, 0.0),
        "XAxis": SpaceVector(1.0, 0.0, 0.0),
        "YAxis": SpaceVector(0.0, 1.0, 0.0),
        "ZAxis": SpaceVector(0.0, 0.0, 1.0),
    }
)
class Transform(ModelBase):
    Origin: SpaceVector
    XAxis: SpaceVector
    YAxis: SpaceVector
    ZAxis: SpaceVector
