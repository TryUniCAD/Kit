from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild


# the measured sheet constructor must receive the real drawing allocation boundary and explicit target provenance
def MakeSheetBuild(BuildValue: DrawBuild, FirstValue: int) -> SheetBuild:
    TargetValue = BuildValue.TargetValue
    return SheetBuild(
        BuildValue.SheetValue,
        BuildValue.SheetNames,
        FirstValue,
        BuildValue.CreatedAt,
        TargetValue.DateCode,
        TargetValue.ParasolidVersion,
        TargetValue.FileVersion,
        TargetValue.ServicePack,
        TargetValue.SubservicePack,
    )
