from io import BytesIO
from itertools import product as Product
from math import inf as Infinity, nextafter as NextFloat

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.RoundViewSeries import (
    RoundViewSeries,
)
from convert.adapters.solidworks.Archive.Construction.Views.ViewMatrix import ViewMatrix
from convert.adapters.solidworks.Archive.Construction.Views.ViewPlans import KViewPlans
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.document.Models.DocumentModel import CadDocument

# the platform rounding distinction belongs to the four built in quarter turn views
KMatQuarterViews = frozenset(("*Left", "*Right", "*Top", "*Bottom"))


# an adjacent rounded half angle term can produce the same principal camera on another platform
def QuarterViews(IndexValue: int) -> tuple[dict[str, float], ...]:
    _, Rotations = KViewPlans[IndexValue]
    if len(Rotations) != 1:
        raise ValueError("cold material quarter turns require one standard rotation")
    AxisName, AngleValue = Rotations[0]
    HalfAngle = AngleValue * -0.5
    SineValue = RoundViewSeries(HalfAngle, 1)
    CosineValue = RoundViewSeries(HalfAngle, 0)
    Terms = tuple(
        (Value, NextFloat(Value, Infinity), NextFloat(Value, -Infinity))
        for Value in (SineValue, CosineValue)
    )
    return tuple(
        ViewMatrix(
            (SinValue, 0.0 * SinValue, 0.0 * SinValue, Cosine)
            if AxisName == "x"
            else (0.0 * SinValue, SinValue, 0.0 * SinValue, Cosine)
        )
        for SinValue, Cosine in Product(*Terms)
    )


# only the predicted quarter turn matrices can be normalized for a logical stream comparison
def SwapMatViews(
    RootValue: ArchiveNode, ModelValue: ArchiveNode
) -> tuple[tuple[ArchiveNode, object, dict[str, object]], ...]:
    Incoming = NativeRows(RootValue.FieldsValue.get("f9f8"))
    Modeled = NativeRows(ModelValue.FieldsValue.get("f9f8"))
    if len(Incoming) != len(Modeled) or len(Modeled) != len(KViewPlans):
        raise ValueError("cold material standard view inventory differs")
    Changes: list[tuple[ArchiveNode, object, dict[str, object]]] = []
    for IndexValue, (NameValue, _) in enumerate(KViewPlans):
        if NameValue not in KMatQuarterViews:
            continue
        SavedView = RequireNative(Incoming[IndexValue].get("o"), "moView_c")
        ExpectedView = RequireNative(Modeled[IndexValue].get("o"), "moView_c")
        SourceFrame = SavedView.FieldsValue.get("f368")
        SourceFields = NativeRecord(SourceFrame)
        TargetFields = NativeRecord(ExpectedView.FieldsValue.get("f368"))
        if SourceFields.get("f08") == TargetFields.get("f08"):
            continue
        if SourceFields.get("f08") not in QuarterViews(IndexValue):
            raise ValueError("cold material view differs from its standard rotation")
        TargetFrame = dict(SourceFields) | {"f08": TargetFields["f08"]}
        Changes.append((SavedView, SourceFrame, TargetFrame))
    return tuple(Changes)


# source typed objects are normalized only in a temporary comparison and never supply writer content
def CheckMatCfgWire(
    LinkValue: NativeLink, RootValue: ArchiveNode, Expected: bytes
) -> None:
    Config = LinkValue.ConfigValue
    Changes = SwapMatViews(Config.RootValue, RootValue)
    try:
        for ViewValue, _, FrameValue in Changes:
            ViewValue.FieldsValue["f368"] = FrameValue
        Regenerated, _ = WriteConfigMut(
            Config.RootValue, Config.VersionValue, Config.HeaderValue
        )
    finally:
        for ViewValue, Original, _ in Changes:
            ViewValue.FieldsValue["f368"] = Original
    if not Changes or Regenerated != Expected:
        raise ValueError(
            "cold material configuration contains unrepresented archive state"
        )


# strict readback validates the complete archive against the same model based writer
def CheckMatWire(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    DocumentValue: CadDocument,
    FileValue: SelfFileInput,
) -> None:
    from convert.adapters.solidworks.Core.Preparation.Materials.PrepMatPart import (
        PrepMatPart,
    )

    Candidate = PrepMatPart(
        DocumentValue,
        BytesIO(),
        FileValue.SavedAt,
        WriteOptions(values={"final_destination": FileValue.PathName}),
    )
    Streams = Candidate.StreamsValue
    Incoming = Archive.streams
    ConfigName = LinkValue.ConfigName
    if Incoming.keys() != Streams.keys() or any(
        NameValue != ConfigName and Incoming[NameValue] != ObjectValue
        for NameValue, ObjectValue in Streams.items()
    ):
        raise ValueError("cold material has unrepresented linked stream content")
    if Incoming[ConfigName] != Streams[ConfigName]:
        CheckMatCfgWire(LinkValue, Candidate.ConfigValue.RootValue, Streams[ConfigName])
