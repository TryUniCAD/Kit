# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.core.ModelBase import ModelBase, ModelDataMut


# topology summaries expose counts without requiring every caller to inspect boundary data
@ModelDataMut(
    DefaultMap={
        "SolidCount": 0,
        "ShellCount": 0,
        "FaceCount": 0,
        "EdgeCount": 0,
        "VertexCount": 0,
        "Volume": None,
        "SurfaceArea": None,
        "BoundingBox": None,
        "IsValid": None,
    }
)
class TopologyCounts(ModelBase):
    SolidCount: int
    ShellCount: int
    FaceCount: int
    EdgeCount: int
    VertexCount: int
    Volume: float | None
    SurfaceArea: float | None
    BoundingBox: BoundingBox | None
    IsValid: bool | None
