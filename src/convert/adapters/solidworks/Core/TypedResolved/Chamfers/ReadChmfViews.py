from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfFrame import (
    KChmfViewName,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import (
    ReadAnnoView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfViewAxes import (
    ChmfViewAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# an independent distance branch must own an ordered second annotation view with its actual swapped basis
def ReadChmfViews(PartValue: ChmfPartRead) -> tuple[ArchiveNode, ...]:
    LinkValue = PartValue.LinkValue
    ModelValue = LinkValue.ConfigValue.RootValue
    Fields = ModelValue.FieldsValue
    ModeWord = PartValue.OwnersValue.ModeWord
    Names = (
        (KChmfViewName, "Chamfer Second Driver View")
        if ModeWord == 2
        else (KChmfViewName,)
    )
    Views = tuple(ReadAnnoView(ModelValue, NameValue) for NameValue in Names)
    Catalog = RequireNative(Fields.get("fa48"), "suObList").FieldsValue
    if (
        tuple(RowValue.get("o") for RowValue in NativeRows(Catalog.get("items")))
        != Views
    ):
        raise ValueError("chamfer has an alternate ordered annotation catalog")
    if ModeWord != 1 and (
        Fields.get("feb4") != KNoAnno
        or Fields.get("nec8") != 1
        or NativeRows(Fields.get("fec0")) != ({"v": KNoAnno},)
        or tuple(ViewValue.FieldsValue.get("f360") for ViewValue in Views)
        != tuple(range(KNoAnno + 1, KNoAnno + 1 + len(Views)))
    ):
        raise ValueError("chamfer has an alternate annotation selection or identity")
    for Index, ViewValue in enumerate(Views):
        Matrix, Origin = ReadRigidXform(NativeRecord(ViewValue.FieldsValue.get("f368")))
        Basis = tuple(
            (Matrix[AxisIndex], Matrix[AxisIndex + 3], Matrix[AxisIndex + 6])
            for AxisIndex in range(3)
        )
        if Basis != ChmfViewAxes(PartValue, Secondary=bool(Index)) or Origin != (
            0.0,
            0.0,
            0.0,
        ):
            raise ValueError("chamfer has an alternate signed display placement")
    CheckTreeAlias(LinkValue, Views)
    return Views
