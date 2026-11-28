from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoBack,
    KPatAnnoLeft,
    KPatAnnoTop,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    KAnnoWorld,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import (
    ReadAnnoView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# editable displays need the assigned annotation identity from their own part catalog
def PatAnnoValues(
    ModelValue: ArchiveNode, StyleValue: PatDriveStyle, *, PitchView: str | None = None
) -> tuple[dict[str, int], ...]:
    if StyleValue.NameValue not in ("D1", "D3"):
        return ()
    if StyleValue.NameValue == "D3" and PitchView is None:
        return ({"v": KNoAnno},)
    Basis = KPatAnnoBack
    ErrorMessage = (
        "pattern count display requires the actual canonical Back annotation frame"
    )
    if PitchView is not None:
        if PitchView not in ("*Top", "*Left"):
            raise ValueError(
                "principal pattern requires a witnessed pitch annotation role"
            )
        Basis = (
            KAnnoWorld
            if StyleValue.NameValue == "D1"
            else (KPatAnnoTop if PitchView == "*Top" else KPatAnnoLeft)
        )
        ErrorMessage = (
            "principal pattern display requires its actual canonical annotation frame"
        )
    if StyleValue.AnnotationName is None:
        raise ValueError(ErrorMessage)
    ViewValue = ReadAnnoView(ModelValue, StyleValue.AnnotationName)
    Matrix, Origin = ReadRigidXform(RequireRecord(ViewValue.FieldsValue.get("f368")))
    Expected = tuple(
        Basis[Column][RowIndex] for RowIndex in range(3) for Column in range(3)
    )
    if Matrix != Expected or Origin != KHingeRoot:
        raise ValueError(ErrorMessage)
    return ({"v": FieldInt(ViewValue.FieldsValue, "f360")},)
