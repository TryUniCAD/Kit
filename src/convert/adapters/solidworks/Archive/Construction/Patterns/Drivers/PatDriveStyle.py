from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    KHingeRoot,
)

# the native one direction feature keeps four dormant displays alongside its two live dimensions
KPatDriveSlots = (
    ("f1258", "D1", True),
    ("f1260", "D3", False),
    ("f1268", "D2", True),
    ("f1270", "D4", False),
    ("f1318", "D5", False),
    ("f1320", "D6", False),
)


# every pattern display has its own explicitly modeled presentation
@DataClass(frozen=True, slots=True)
class PatDriveStyle:
    NameValue: str
    AnnotationName: str | None
    LabelValue: KDatumVector
    DesignIntent: bool
    SelectedLeader: int


# the six display owners must retain the roles of the selected pattern profile
def CheckPatStyles(
    Styles: tuple[PatDriveStyle, ...], *, PitchView: str | None = None
) -> None:
    if len(Styles) != len(KPatDriveSlots):
        raise ValueError(
            "pattern requires six explicitly styled driving or dormant display owners"
        )
    Views = {"D1": "*Back" if PitchView is None else "*Front", "D3": PitchView}
    for StyleValue, (_, NameValue, _) in zip(Styles, KPatDriveSlots, strict=True):
        Labels = StyleValue.LabelValue
        if (
            StyleValue.NameValue != NameValue
            or type(CastValue(object, Labels)) is not tuple
            or len(CastValue(tuple[float, ...], Labels)) != 3
            or any(type(Value) is not float or not abs(Value) < 1e3 for Value in Labels)
            or Labels[2] != 0.0
            or type(CastValue(object, StyleValue.DesignIntent)) is not bool
            or type(StyleValue.SelectedLeader) is not int
            or not -(1 << 31) <= StyleValue.SelectedLeader < (1 << 31)
            or StyleValue.AnnotationName != Views.get(NameValue)
            or NameValue == "D3"
            and Labels != KHingeRoot
        ):
            if PitchView is None:
                raise ValueError(
                    "pattern display style is outside the oblique Back count and unassigned pitch profile"
                )
            raise ValueError(
                "principal pattern requires the Front count and its signed pitch view"
            )
