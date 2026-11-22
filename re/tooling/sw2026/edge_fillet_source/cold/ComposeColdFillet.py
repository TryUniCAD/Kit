from dataclasses import replace

from ColdFilletGraph import make_fillet
from ColdFilletIntent import FEATURE_NAME
from ColdFilletWire import LINK, VERSION, read_cold_resolved, write_cold_resolved
from FilletModel import require

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Construction.Chamfers.EmitChmfPart import MakeChmfKey
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import MakeMgrHeader
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import EmitPartArchive
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindByPlan
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import MakePartKeys
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

BODY_MAP = {"n": 0, "fcd8": []}


def compose_fillet(intent):
    document = intent.document
    plan = ProjectPlain(document)
    settings = replace(MakePartRecipe(plan, intent.locator.SavedAt), OutputValue=intent.locator)
    CheckPartInput(document, settings, plan, (FEATURE_NAME,))
    stock = MakeBlindByPlan(document, settings, plan)
    feature, driver = make_fillet(stock, intent, settings)
    manager_header = MakeMgrHeader(stock.SystemValue.ManagerValue, settings.OutputValue.SavedAt)
    stock_roots = tuple(ArchiveNode.RequireNode(value) for value in stock.ResolvedValue.RootsValue)
    keywords = MakePartKeys(stock.SystemValue, stock_roots, settings, plan,
                           AdditionalRows=(replace(MakeChmfKey(feature, (driver,)), KindValue="Fillet"),))
    streams, config, _ = EmitPartArchive(
        stock.SystemValue, stock_roots, (stock.HeaderValue, stock.TopHeader, manager_header),
        stock.DefinitionValue, settings, keywords, BodyMapFields=BODY_MAP,
    )
    resolved, written, written_map = write_cold_resolved((*stock_roots, feature), config.MapValue, BODY_MAP)
    streams[KResolvedFeaturesStream] = resolved
    data = BuildSldprt(streams, FormatVersion=4)
    archive = SldprtArchive.from_bytes(data)
    require(all(archive.require(name) == value for name, value in streams.items()),
            "cold fillet container lost its generated logical streams")
    header = ReadHeaderGraph(archive.require("Contents/Config-0-ModelHeader"), VERSION)
    read_config = ReadConfigMut(archive.require("Contents/Config-0"), VERSION, header)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION)
    require(MakeLinkContext(read_config, manager) == LINK, "resolved fillet does not have its actual manager context")
    roots, decoded, decoded_map = read_cold_resolved(archive.require(KResolvedFeaturesStream), read_config.MapValue)
    top_header = ReadHeaderGraph(archive.require("Header2"), VERSION)
    require(decoded["self_path"] == intent.locator.PathName
            and decoded["stock_birth"] == DatumTime(header, decoded["stock_id"])
            == DatumTime(top_header, decoded["stock_id"]) == intent.locator.SavedAt,
            "the edge historical owner or self locator differs from the generated headers")
    reserialized, checked, checked_map = write_cold_resolved(roots, read_config.MapValue, BODY_MAP)
    require(resolved == reserialized and written == decoded == checked and written_map == decoded_map == checked_map,
            "typed cold fillet graph did not round-trip exactly")
    refusals = {
        "default_resolved": check_refusal(lambda: ReadNativeLink(archive, 0), "unsupported SOLIDWORKS body class Fillet_c schema 1"),
        "saved_resolved": check_refusal(lambda: ReadNativeLink(archive, 0, ReadFillets=True), "unsupported SOLIDWORKS fillet"),
        "trailing_typed_bytes": check_refusal(
            lambda: read_cold_resolved(resolved + b"\x00", read_config.MapValue),
            "finish at its actual empty inline body map",
        ),
    }
    return data, streams, decoded, decoded_map, refusals


def check_refusal(action, reason):
    try:
        action()
    except (BodyUnsupported, ValueError) as error:
        require(reason in str(error), f"unexpected cold fillet refusal: {error}")
        return str(error)
    raise ValueError("cold fillet proof expected an explicit refusal")
