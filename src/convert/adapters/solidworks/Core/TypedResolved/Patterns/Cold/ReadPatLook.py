from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoBack,
    KPatAnnoTop,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    KAnnoWorld,
    ReadAnnoBasis,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Core.Common import FreezeMapping


# each local display annotation edge must join the actual named view or its reserved unassigned slot
def PatDisplayView(
    Fields: Mapping[str, object], ViewIds: Mapping[int, str], ControlName: str
) -> str | None:
    RowsValue = NativeRows(Fields.get("f2b0"))
    KeysValue = tuple(RowValue.get("v") for RowValue in RowsValue)
    BackIds = tuple(
        Identity for Identity, NameValue in ViewIds.items() if NameValue == "*Back"
    )
    Wanted = (
        BackIds
        if ControlName in ("angle", "D1")
        else (KNoAnno,) if ControlName == "D3" else ()
    )
    if Fields.get("n2b0") != len(Wanted) or KeysValue != Wanted:
        raise ValueError("cold pattern display has another annotation owner")
    return "*Back" if ControlName in ("angle", "D1") else None


# exposed labels describe authored display semantics rather than serializable native field records
def ReadPatLabel(
    Display: ArchiveNode, ViewIds: Mapping[int, str], ControlName: str
) -> Mapping[str, object]:
    Fields = Display.FieldsValue
    RawLabel = (
        Fields.get("ff68")
        if ControlName == "angle"
        else NativeRecord(Fields.get("f6a0")).get("f38")
    )
    Label = ReadVector(RawLabel)
    return FreezeMapping(
        {
            "name": ControlName,
            "annotation": PatDisplayView(Fields, ViewIds, ControlName),
            "label_m": Label,
            "design_intent": bool(FieldInt(Fields, "fb60") & 0x100),
            "selected_leader": FieldInt(Fields, "ff80"),
        }
    )


# source presentation keeps ordered native catalog bases and the actual live and dormant display owners
def ReadPatLook(
    LinkValue: NativeLink, OwnerValue: PatternOwner
) -> Mapping[str, object]:
    PartFields = LinkValue.ConfigValue.RootValue.FieldsValue
    Catalog = RequireNative(PartFields.get("fa48"), "suObList")
    Backdrop = {"*Back": KPatAnnoBack, "*Front": KAnnoWorld, "*Top": KPatAnnoTop}
    ViewsValue: list[Mapping[str, object]] = []
    ViewIds: dict[int, str] = {}
    for Index, RowValue in enumerate(
        NativeRows(Catalog.FieldsValue.get("items")), KNoAnno + 1
    ):
        Fields = RequireNative(RowValue.get("o"), "moAnnotationView_c").FieldsValue
        NameValue = Fields.get("f358")
        Matrix, Offset = ReadRigidXform(NativeRecord(Fields.get("f368")))
        Basis = ReadAnnoBasis(
            (
                (Matrix[0], Matrix[3], Matrix[6]),
                (Matrix[1], Matrix[4], Matrix[7]),
                (Matrix[2], Matrix[5], Matrix[8]),
            )
        )
        if (
            type(NameValue) is not str
            or Backdrop.get(NameValue) != Basis
            or any(Offset)
            or FieldInt(Fields, "f360") != Index
            or Fields.get("f370") != IdentityXform()
            or Fields.get("n380") != 0
            or any(
                Fields.get(NameValue) is not None
                for NameValue in ("f3d0", "f3e8", "f2f0")
            )
        ):
            raise ValueError("cold pattern annotation frame or identity differs")
        ViewsValue.append(FreezeMapping({"name": NameValue, "basis": Basis}))
        ViewIds[Index] = NameValue
    Datum = RequireNative(
        OwnerValue.DatumValue.PlaneValue.FieldsValue.get("f6f8"),
        "moConstraintCoincLineAtAnglePlaneRefplaneData_c",
    )
    Display = RequireNative(Datum.FieldsValue.get("f150"), "moDisplayAngularDim_c")
    return FreezeMapping(
        {
            "views": tuple(ViewsValue),
            "angle": ReadPatLabel(Display, ViewIds, "angle"),
            "drivers": tuple(
                ReadPatLabel(Driver.DisplayValue, ViewIds, Driver.NativeName)
                for Driver in OwnerValue.DriversValue
            ),
        }
    )
