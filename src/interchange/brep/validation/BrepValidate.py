# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.brep.validation.BrepBodyValidate import GetBodyErrors
from interchange.brep.validation.BrepCurveValidate import GetCurveErrors
from interchange.brep.validation.BrepEdgeValidate import GetEdgeErrors
from interchange.brep.validation.BrepFaceValidate import GetFaceErrors
from interchange.brep.validation.BrepIdentityValidate import GetBrepIds
from interchange.brep.validation.BrepLoopValidate import GetLoopErrors
from interchange.brep.validation.BrepPcurveValidate import GetPcurveErrors
from interchange.brep.validation.BrepShellValidate import GetShellErrors
from interchange.brep.validation.BrepSurfaceValidate import GetSurfErrors
from interchange.brep.validation.BrepView import BrepView


# validation orchestration preserves deterministic diagnostics across focused topology checks
def GetBrepErrors(
    ModelValue: BrepView, DesignBodyIds: frozenset[str]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    if (
        not isinstance(ModelValue.SchemaVersion, str)
        or not ModelValue.SchemaVersion.strip()
        or ModelValue.SchemaVersion != ModelValue.SchemaVersion.strip()
    ):
        ErrorValues.append("B-rep schema version must be a non-empty string")
    IdentitySets, IdentityErrors = GetBrepIds(ModelValue)
    ErrorValues.extend(IdentityErrors)
    for CurveValue in ModelValue.Curves:
        ErrorValues.extend(GetCurveErrors(CurveValue, IdentitySets["Surfaces"]))
    for PcurveValue in ModelValue.Pcurves:
        ErrorValues.extend(GetPcurveErrors(PcurveValue))
    for SurfaceValue in ModelValue.Surfaces:
        ErrorValues.extend(GetSurfErrors(SurfaceValue, IdentitySets["Surfaces"]))
    ErrorValues.extend(GetEdgeErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetLoopErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetFaceErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetShellErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetBodyErrors(ModelValue, IdentitySets, DesignBodyIds))
    return tuple(ErrorValues)
