from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AnglePlaneInput import (
    AnglePlaneInput,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    CheckPatStyles,
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import (
    PatAngleStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoBack,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    ReadAnnoBasis,
)


# explicit annotation styles must stay attached to the three actual editable controls
def ReadPatPresent(
    InputValue: PatPresentInput,
    AngleName: str,
    AngleValue: float,
    AngleParamId: str,
    CountParamId: str,
    PitchParamId: str,
) -> AnglePlaneInput:
    if type(InputValue) is not PatPresentInput:
        raise ValueError("expected typed authored pattern presentation")
    Label = InputValue.AngleStyle
    if type(Label) is not PatAngleStyle or (
        Label.ParamId,
        InputValue.CountParamId,
        InputValue.PitchParamId,
    ) != (AngleParamId, CountParamId, PitchParamId):
        raise ValueError(
            "presentation is not bound to the actual active parameter owners"
        )
    if (
        Label.AnnotationName != "*Back"
        or type(CastValue(object, Label.DesignIntent)) is not bool
        or type(Label.SelectedLeader) is not int
        or not -(1 << 31) <= Label.SelectedLeader < (1 << 31)
        or Label.ShiftValue != KHingeRoot
        or any(type(Value) is not float for Value in Label.ShiftValue)
    ):
        raise ValueError(
            "ordinary angular datum needs its Back annotation signed leader and zero shifted point"
        )
    if (
        type(CastValue(object, InputValue.AnnoValues)) is not tuple
        or not 1 <= len(InputValue.AnnoValues) <= 3
        or type(CastValue(object, InputValue.ShownAnnos)) is not tuple
        or any(
            type(ViewValue) is not AnnoViewInput
            or type(ViewValue.NameValue) is not str
            or not ViewValue.NameValue
            or "\x00" in ViewValue.NameValue
            for ViewValue in InputValue.AnnoValues
        )
    ):
        raise ValueError("expected an explicit ordered typed annotation catalog")
    Views = {
        ViewValue.NameValue: ReadAnnoBasis(ViewValue.BasisValue)
        for ViewValue in InputValue.AnnoValues
    }
    if (
        len(Views) != len(InputValue.AnnoValues)
        or Views.get(Label.AnnotationName) != KPatAnnoBack
        or any(
            NameValue is not None
            and (type(NameValue) is not str or NameValue not in Views)
            for NameValue in (InputValue.ActiveAnno, *InputValue.ShownAnnos)
        )
        or len(set(InputValue.ShownAnnos)) != len(InputValue.ShownAnnos)
    ):
        raise ValueError(
            "annotation view and active membership must bind the actual Back catalog"
        )
    if type(CastValue(object, InputValue.StyleValues)) is not tuple or any(
        type(StyleValue) is not PatDriveStyle for StyleValue in InputValue.StyleValues
    ):
        raise ValueError(
            "pattern requires six explicitly styled driving or dormant display owners"
        )
    CheckPatStyles(InputValue.StyleValues)
    return AnglePlaneInput(
        AngleName,
        AngleValue,
        False,
        Label.AnnotationName,
        Label.DesignIntent,
        Label.SelectedLeader,
        Label.ShiftValue,
    )
