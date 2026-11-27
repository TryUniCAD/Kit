from collections.abc import Mapping
from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Mates.RequireCylRefs import RequireCylRefs
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# each active cylinder and independent support wrapper must retain their ordered mate and geometry ownership
def RequireCylEnds(FieldsValue: Mapping[str, object]) -> None:
    SupportRows = ReadRows(FieldsValue.get("f3c8"))
    ActiveRows = ReadRows(FieldsValue.get("f410"))
    if len(SupportRows) != 2 or len(ActiveRows) != 2:
        raise BodyUnsupported("ordinary concentric mate requires two endpoint pairs")
    MateId = FieldInt(FieldsValue, "f08")
    Wrappers: set[ArchiveNode] = set()
    for Index, (SupportRow, ActiveRow) in enumerate(
        zip(SupportRows, ActiveRows, strict=True)
    ):
        Support = RequireNode(SupportRow.get("o"), "moCylinderRef_w")
        Active = RequireNode(ActiveRow.get("o"), "moCylinderRef_w")
        Stored = Support.FieldsValue
        Selected = Active.FieldsValue
        Radius = RequireScalar(Selected.get("f100"))
        if (
            FieldInt(SupportRow, "k") != Index
            or FieldInt(Selected, "f74") != MateId
            or FieldInt(Stored, "has_f108") != 0
            or FieldInt(Selected, "has_f108") != 1
            or not IsFinite(Radius)
            or Radius <= 0.0
            or any(
                Stored.get(NameValue) != Selected.get(NameValue)
                for NameValue in ("fd0", "fe8", "f100")
            )
        ):
            raise BodyUnsupported("concentric endpoint and support state differs")
        RequireCylRefs(Stored, Selected)
        Wrappers.update((Support, Active))
    if len(Wrappers) != 4:
        raise BodyUnsupported(
            "concentric wrappers must own four actual archive objects"
        )
