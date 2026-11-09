# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos as CosData, sin as SineValue

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# exact angular directions keep cap and circle parameter origins aligned
def RotateRadial(Frame: Transform, Angle: float) -> SpaceVector:
    Cosine, SineData = CosData(Angle), SineValue(Angle)
    Radial, Tangent = Frame.x_axis, Frame.y_axis
    return SpaceVector(
        Radial.x * Cosine + Tangent.x * SineData,
        Radial.y * Cosine + Tangent.y * SineData,
        Radial.z * Cosine + Tangent.z * SineData,
    )
