from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import (
    ReadAnnoView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# the live count uses the actual canonical back annotation while the live pitch uses its reserved unassigned view
def PatAnnoValues(
    ModelValue: ArchiveNode, StyleValue: PatDriveStyle
) -> tuple[dict[str, int], ...]:
    if StyleValue.NameValue == "D3":
        return ({"v": KNoAnno},)
    if StyleValue.NameValue != "D1":
        return ()
    if StyleValue.AnnotationName is None:
        raise ValueError(
            "pattern count display requires the actual canonical Back annotation frame"
        )
    ViewValue = ReadAnnoView(ModelValue, StyleValue.AnnotationName)
    Matrix, Origin = ReadRigidXform(RequireRecord(ViewValue.FieldsValue.get("f368")))
    if (
        Matrix != (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0)
        or Origin != KHingeRoot
    ):
        raise ValueError(
            "pattern count display requires the actual canonical Back annotation frame"
        )
    return ({"v": FieldInt(ViewValue.FieldsValue, "f360")},)
