# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.enums.EnumBase import WireEnum


# value categories preserve parameter meaning beyond primitive python representation
class ValueKind(WireEnum):
    KLength = "length"
    KAngle = "angle"
    KQuantity = "quantity"
    KNumber = "number"
    KInteger = "integer"
    KBoolean = "boolean"
    KString = "string"


# parameter roles retain whether downstream systems may drive each value
class ParameterRole(WireEnum):
    KDriving = "driving"
    KDriven = "driven"
    KReference = "reference"
    KDerived = "derived"
