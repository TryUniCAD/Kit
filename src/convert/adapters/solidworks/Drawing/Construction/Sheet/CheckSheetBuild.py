from convert.adapters.solidworks.Drawing.Construction.Sheet.CheckDrawText import (
    CheckDrawText,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild


# construction must reject unproved paper releases and invalid provenance before allocating native owners
def CheckSheetBuild(BuildValue: SheetBuild) -> None:
    InputValue = BuildValue.InputValue
    CheckDrawText(InputValue.NameValue, True)
    CheckDrawText(InputValue.PropertyView, True)
    for NameValue in (
        BuildValue.NamesValue.PlaneName,
        BuildValue.NamesValue.ProfileName,
        BuildValue.NamesValue.DetailName,
    ):
        CheckDrawText(NameValue, False)
    if InputValue.PaperSize != "ansi-a-landscape" or InputValue.LengthUnit not in (
        "mm",
        "cm",
        "m",
        "in",
        "ft",
        "angstrom",
        "nm",
        "um",
        "mil",
        "microinch",
    ):
        raise ValueError(
            "drawing sheet construction requires its qualified paper and length units"
        )
    for ScaleValue in (InputValue.NumeratorValue, InputValue.DenominatorValue):
        if type(ScaleValue) is not int or not 1 <= ScaleValue <= 999999:
            raise ValueError(
                "drawing sheet scale requires positive integral numerator and denominator"
            )
    if (
        any(
            type(FieldValue) is not int
            for FieldValue in (
                BuildValue.ArchiveVersion,
                BuildValue.ServicePack,
                BuildValue.SubservicePack,
            )
        )
        or BuildValue.ArchiveVersion != 19000
        or BuildValue.ServicePack != 5
        or BuildValue.SubservicePack != 2
    ):
        raise ValueError(
            "drawing sheet construction requires the proved 2026 sp05 2 target"
        )
    for FieldValue, LowerValue, UpperValue in (
        (BuildValue.FirstIdValue, 1, 2147483643),
        (BuildValue.CreatedAtValue, 0, 4294967295),
        (BuildValue.DateCodeValue, 0, 2147483647),
        (BuildValue.KernelVersion, 1, 2147483647),
    ):
        if type(FieldValue) is not int or not LowerValue <= FieldValue <= UpperValue:
            raise ValueError(
                "drawing sheet construction has invalid explicit identifier time or target provenance"
            )
