from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import (
    PatAngleStyle,
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
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.document.Models.DocumentModel import CadDocument


# retain the observed semantic view names and signed label coordinates independently of archive fields
def ReadLabelStyle(Fields: Mapping[str, object]) -> PatDriveStyle:
    NameValue = Fields.get("name")
    AnnoValue = Fields.get("annotation")
    Intent = Fields.get("design_intent")
    Leader = Fields.get("selected_leader")
    Label = Fields.get("label_m")
    if (
        type(NameValue) is not str
        or (AnnoValue is not None and type(AnnoValue) is not str)
        or type(Intent) is not bool
        or type(Leader) is not int
        or type(Label) is not tuple
    ):
        raise ValueError("cold linear pattern needs owned presentation semantics")
    ShiftX, ShiftY, ShiftZ = CastValue(tuple[object, ...], Label)
    return PatDriveStyle(
        NameValue,
        AnnoValue,
        (RequireScalar(ShiftX), RequireScalar(ShiftY), RequireScalar(ShiftZ)),
        Intent,
        Leader,
    )


# a readback presentation remaps only to the actual neutral angle count and pitch owners
def ReadPatLook(
    Document: CadDocument, AngleId: str, CountId: str, PitchId: str
) -> PatPresentInput:
    Details = NativeRecord(Document.metadata.get("solidworks.typed_linear_pattern"))
    Looks = NativeRecord(Details.get("presentation"))
    AngleLabel = ReadLabelStyle(NativeRecord(Looks.get("angle")))
    ViewsValue: list[AnnoViewInput] = []
    for ViewValue in NativeRows(Looks.get("views")):
        NameValue = ViewValue.get("name")
        if type(NameValue) is not str:
            raise ValueError("cold linear pattern annotation has no name")
        ViewsValue.append(
            AnnoViewInput(NameValue, ReadAnnoBasis(ViewValue.get("basis")))
        )
    if AngleLabel.NameValue != "angle" or AngleLabel.AnnotationName is None:
        raise ValueError("cold linear pattern angle has no annotation owner")
    return PatPresentInput(
        PatAngleStyle(
            AngleId,
            AngleLabel.AnnotationName,
            AngleLabel.DesignIntent,
            AngleLabel.SelectedLeader,
            AngleLabel.LabelValue,
        ),
        CountId,
        PitchId,
        tuple(ReadLabelStyle(Fields) for Fields in NativeRows(Looks.get("drivers"))),
        tuple(ViewsValue),
        None,
        (None,),
    )
