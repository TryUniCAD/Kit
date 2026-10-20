# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange.enums.EnumBase import WireEnum
from interchange.features.FeatureContract import FeatureDef
from interchange.core.ModelBase import ModelDataMut
from interchange.records.RecordParameter import ParameterValue
from interchange.geometry.models.VectorSpace import SpaceVector


# extrusion bounds preserve editable termination intent instead of only distance
class ExtrudeEnd(WireEnum):
    KBlind = "blind"
    KThroughAll = "through_all"
    KUpToFirst = "up_to_first"
    KUpToLast = "up_to_last"
    KUpToFace = "up_to_face"
    KUpToShape = "up_to_shape"
    KUpToVertex = "up_to_vertex"
    KTwoLengths = "two_lengths"
    KMidPlane = "mid_plane"
    KOffsetSurface = "offset_from_surface"
    KNative = "native"


# extrusions retain directional and termination choices needed for reconstruction
@ModelDataMut(
    DefaultMap={
        "EndCondition": ExtrudeEnd.KBlind,
        "IsReversed": False,
        "IsSymmetric": False,
        "Direction": None,
        "SecondLength": None,
        "SecondEndCondition": None,
        "Offset": None,
        "SecondOffset": None,
        "DraftAngle": None,
        "SecondDraftAngle": None,
        "UpToReference": "",
        "SecondUpToRef": "",
    }
)
class ExtrudeFeature(FeatureDef):
    Length: ParameterValue
    EndCondition: ExtrudeEnd | str
    IsReversed: bool
    IsSymmetric: bool
    Direction: SpaceVector | None
    SecondLength: ParameterValue | None
    SecondEndCondition: ExtrudeEnd | str | None
    Offset: ParameterValue | None
    SecondOffset: ParameterValue | None
    DraftAngle: ParameterValue | None
    SecondDraftAngle: ParameterValue | None
    UpToReference: str
    SecondUpToRef: str
