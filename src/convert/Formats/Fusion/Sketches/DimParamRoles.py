# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from dataclasses import replace as Replace

from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import Parameter


# uniquely bound native driving dimensions establish editable parameters without promoting unresolved sketch measurements
def PromoteDimDrive(
    Sketches: tuple[Sketch, ...],
    Parameters: tuple[Parameter, ...],
    Issues: tuple[Diagnostic, ...],
) -> tuple[Parameter, ...]:
    Unqualified = {
        IssueValue.entity_id
        for IssueValue in Issues
        if IssueValue.code.startswith("fusion.sketch.dimension.")
    }
    UsesByParam = Counter(
        RuleValue.parameter_id
        for SketchValue in Sketches
        for RuleValue in SketchValue.constraints
    )
    DrivingIds = {
        RuleValue.parameter_id
        for SketchValue in Sketches
        if SketchValue.id not in Unqualified
        for RuleValue in SketchValue.constraints
        if RuleValue.driving is True
        and RuleValue.kind
        in (
            ConstraintKind.KDistance.value,
            ConstraintKind.KDistanceX.value,
            ConstraintKind.KDistanceY.value,
            ConstraintKind.KDiameter.value,
            ConstraintKind.KRadius.value,
        )
        and UsesByParam[RuleValue.parameter_id] == 1
    }
    if not DrivingIds:
        return Parameters
    return tuple(
        (
            Replace(ParamValue, role=ParameterRole.KDriving)
            if ParamValue.id in DrivingIds
            and ParamValue.role is ParameterRole.KReference
            else ParamValue
        )
        for ParamValue in Parameters
    )
