# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# spatial bounds support planning without forcing complete geometry traversal
@ModelDataMut
class BoundingBox(ModelBase):
    Minimum: SpaceVector
    Maximum: SpaceVector
