# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Resolved.Circular.Records import CircularSupport
from convert.adapters.solidworks.Resolved.OriginProfile import OriginProfile
from convert.adapters.solidworks.Resolved.PrincipalDatum import PrincipalDatum
from convert.adapters.solidworks.Resolved.PrincipalRef import PrincipalRef
from convert.adapters.solidworks.Sketch.CircularRecords import (
    CircularDisplay,
    CircularHeader,
    CircularMember,
    CircularOrigin,
    CircularPoint,
    RoundDiameter,
)


# standalone circular sketches need their own complete record without an invented extrusion
@Dataclass(frozen=True, slots=True)
class CircleOnly:
    Profile: CircularHeader
    Datum: PrincipalDatum
    Origin: OriginProfile
    Points: list[CircularPoint]
    Circle: CircularMember
    Diameter: RoundDiameter
    Coincidence: CircularOrigin
    Display: CircularDisplay
    Support: CircularSupport
    Reference: PrincipalRef
    StateWord: int
    EndOffset: int
