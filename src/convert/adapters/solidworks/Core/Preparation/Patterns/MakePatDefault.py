from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    KPatDriveSlots,
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import (
    PatAngleStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoBack,
    KPatAnnoTop,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    FrontStockBox,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)


# seed geometry and live parameter identities determine the ordinary authored presentation
def MakePatDefault(
    SeedValue: FrontStockBox,
    AngleParamId: str,
    CountParamId: str,
    PitchParamId: str,
) -> PatPresentInput:
    Lower, Upper = SeedValue.BoundsValue
    Points: dict[str, KDatumVector] = {
        "D1": ((Lower[0] + Upper[0]) / 2.0, (Lower[1] + Upper[1]) / 2.0, 0.0),
        "D2": Lower,
    }
    Styles = tuple(
        PatDriveStyle(
            NameValue,
            "*Back" if NameValue == "D1" else None,
            Points.get(NameValue, KHingeRoot),
            True,
            0,
        )
        for _, NameValue, _ in KPatDriveSlots
    )
    return PatPresentInput(
        PatAngleStyle(AngleParamId, "*Back", True, 0, KHingeRoot),
        CountParamId,
        PitchParamId,
        Styles,
        (AnnoViewInput("*Top", KPatAnnoTop), AnnoViewInput("*Back", KPatAnnoBack)),
        None,
        (None,),
    )
