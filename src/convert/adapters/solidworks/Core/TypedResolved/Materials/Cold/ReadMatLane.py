from dataclasses import replace as ReplaceValue
from hashlib import sha256 as CalcSha

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.ColdStreamRoles import (
    HasColdStreams,
    KColdChildStreams,
)
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.Materials.BuildMatShape import (
    BuildMatShape,
)
from convert.adapters.solidworks.Core.Preparation.Materials.ColdMatSource import (
    KColdMatSource,
)
from convert.adapters.solidworks.Core.Preparation.Materials.MatSketchModel import (
    ExpandMatSketch,
)
from convert.adapters.solidworks.Core.Preparation.Materials.PlanMatPart import (
    KMatAnchor,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.Cold.CheckMatWire import (
    CheckMatWire,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.Cold.MakeMatReadDoc import (
    MakeMatReadDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatText import (
    ReadMatText,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordSource import CadSource


# the physical density lane must be detected before the ordinary cold reader drops its assignment
def PickMatConfig(Archive: SldprtArchive) -> ArchiveNode | None:
    if not KColdChildStreams <= Archive.streams.keys() or not IsCacheAbsent(Archive):
        return None
    try:
        Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    ConfigValue = Manager.RootValue.FieldsValue.get("f360")
    if not isinstance(ConfigValue, ArchiveNode):
        return None
    Density = ConfigValue.FieldsValue.get("fc50")
    if (type(Density) is float and Density > 0.0) or HasMatIdentity(ConfigValue):
        return ConfigValue
    return None


# a named configuration owner still signals material when its required density is damaged
def HasMatIdentity(ConfigValue: ArchiveNode) -> bool:
    VisualValue = ConfigValue.FieldsValue.get("f78")
    if not isinstance(VisualValue, ArchiveNode):
        return False
    try:
        RecordValue = NativeRecord(VisualValue.FieldsValue.get("f20"))
        return "|" in ReadMatText(RecordValue.get("f20"))
    except (TypeError, ValueError):
        return False


# the public design keeps the actual locator and complete origin graph alongside optional derived geometry
def FinishMatRead(
    Document: CadDocument,
    FileValue: SelfFileInput,
    Label: str,
    Digest: str,
    IncludeBrep: bool,
) -> CadDocument:
    KindValue = Document.metadata.get(KMatAnchor)
    if not isinstance(KindValue, str):
        raise ValueError("cold material has no anchored sketch")
    SketchValue = ExpandMatSketch(Document.sketches[0], KindValue)
    BodyValue = Document.bodies[0]
    BrepValue = None
    if IncludeBrep:
        BrepValue, Topology = BuildMatShape(Document)
        BodyValue = ReplaceValue(BodyValue, topology=Topology)
    Source = CadSource(
        KPartFormatId,
        Label,
        Digest,
        container_version="4",
        attributes={
            KColdMatSource: True,
            "native_locator": FileValue.PathName,
            "written_at": FileValue.SavedAt,
        },
    )
    Result = ReplaceValue(
        Document, source=Source, sketches=(SketchValue,), bodies=(BodyValue,), brep=BrepValue
    )
    Result.assert_valid()
    return ReplaceValue(Result, capabilities=InferCaps(Result))


# physical cold archives are decoded only when their native editable owners and all logical streams agree
def ReadMatLane(
    Archive: SldprtArchive, DataValue: bytes, Label: str, Settings: ReadOptions
) -> CadDocument | None:
    if Settings.extract_raw_brep:
        return None
    Config = PickMatConfig(Archive)
    if Config is None:
        return None
    try:
        if not HasColdStreams(Archive, KColdChildStreams):
            raise ValueError("cold material has an unrepresented stream inventory")
        LinkValue = ReadNativeLink(Archive, 0)
        Design, FileValue = MakeMatReadDoc(LinkValue, Config)
        ConfigValue = Design.configurations[0]
        if Settings.configuration not in (None, ConfigValue.id, ConfigValue.name):
            raise ValueError("requested material part configuration is unavailable")
        CheckMatWire(Archive, LinkValue, Design, FileValue)
        return FinishMatRead(
            Design,
            FileValue,
            Label,
            CalcSha(DataValue).hexdigest(),
            Settings.include_brep,
        )
    except (IndexError, KeyError, TypeError, ValueError, OverflowError) as ErrorValue:
        raise SldprtFormatError(
            f"unsupported SOLIDWORKS cold material: {ErrorValue}"
        ) from ErrorValue
