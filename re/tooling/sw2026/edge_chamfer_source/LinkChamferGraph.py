from dataclasses import replace
from math import degrees
from xml.etree.ElementTree import SubElement, fromstring

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import BindStockMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyDimMut import MakeKeyDimMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import MakeMgrHeader
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPartFromPlan
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import PutAnnoCatalog
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.UseChmfCtxMut import UseChmfCtxMut
from convert.adapters.solidworks.Archive.Resolved.WriteMbsMut import WriteMbsMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfMode import CheckChmfMode

from ChamferEdgeOwners import make_edge_fields, make_stock_selection, node
from MakeChamferDrivers import make_drivers_mut, require

VERSION = 19000
CONTEXT = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 1}


def build_graph(document, request):
    plan = ProjectBlind(document, ReadLineLoop)
    require(set(request) == {"case", "size_mm", "feature", "epoch", "locator", "shape", "catalog", "presentation"}
            and plan.NameValue == request["case"], "chamfer build requires the exact modeled stock and display inputs")
    locator, epoch = request["locator"], request["epoch"]
    settings = replace(MakePartRecipe(plan, epoch), OutputValue=SelfFileInput(locator, epoch))
    candidate = MakeBlindPartFromPlan(document, settings, plan)
    selection = make_stock_selection(candidate, request["shape"])
    system = candidate.SystemValue
    model = system.RootValue
    stock = candidate.BossValue.FeatureValue
    headers = (candidate.HeaderValue, candidate.TopHeader)
    require(headers[0].FieldsValue["f08"] == headers[1].FieldsValue["f08"]
            and candidate.ResolvedValue.RootsValue[-1] is stock,
            "committed stock map must own its two agreeing generated header frontiers")
    ids = PersistentIds(headers[0].FieldsValue["f08"])
    PutAnnoCatalog(model, VERSION, tuple(AnnoViewInput(row["name"], row["basis"]) for row in request["catalog"]),
                   None, (None,))
    feature = node("Chamfer_c", {})
    InitFeatureMut(feature, request["feature"], model, settings.TargetValue)
    feature.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    feature.FieldsValue.update({name: [] for name in KAtomLists})
    feature.FieldsValue.update(f35c=0, f368={"n": 0, "items": []}, f388={"n": 0, "items": []},
                               f4a0=1, f6e0=None, f758=None, f780={"n": 0, "items": []}, f7a0=0,
                               f860=0, f8a0=10, f878=0, f8c0=1, f87c=0, has_f808=0, f8f0=1,
                               f8c8={"n": 0, "items": []})
    feature.FieldsValue.update(dict.fromkeys(
        ("f820", "f8b0", "f8b8", "f828", "f830", "f838", "f840", "f848", "f850", "f858"), None))
    drivers = make_drivers_mut(model, feature, request["shape"], request["presentation"], ids)
    ids.AllocateMut(feature)
    atom = BindStockMut(model.FieldsValue["fd88"], stock)
    atom.FieldsValue["f130"] = feature.FieldsValue["f08"]
    feature.FieldsValue["f538"] = atom
    SetCfgStampMut(candidate.CurrentConfig, ids)
    for header in headers:
        header.FieldsValue["f08"] = ids.NextValue
        logs = header.FieldsValue["f20"].FieldsValue
        logs["items"] = (*logs["items"], *(MakeRootLog(n, settings.HeaderValue) for n in (stock, feature)))
    fields, locator_owner = make_edge_fields(candidate, feature, atom, selection, headers)
    feature.FieldsValue.update(fields)
    CheckChmfMode(feature)
    system.ManagerValue.FieldsValue["f658"] = 1
    return candidate, feature, atom, drivers, selection, locator_owner


def write_roots(roots, extra, seed, link):
    ctx = MakeResolvedCtx(VERSION, seed, link, None)
    UseChmfCtxMut(ctx)
    maps = ArchiveMaps(seed.CounterValue, seed)
    writer = BodyWriter(maps, ctx, WriteBodyMut)
    writer.OutputValue.extend(EncodeScalar(seed.CounterValue, "u32"))
    writer.OutputValue.extend(EncodeCount(len(roots)))
    for root in roots:
        WriteNodeMut(writer, root)
    WriteMbsMut(writer, FindModelRoot(seed), extra)
    return bytes(writer.OutputValue), maps.Snapshot()


def cold_keywords(raw, feature, drivers):
    document = fromstring(raw[1:])
    row = SubElement(document, "Feature", {"id": str(feature.FieldsValue["f08"]),
                                           "Name": ReadNodeName(feature), "Type": "Chamfer"})
    d1, d2 = (entry.ParameterValue.FieldsValue["f58"] for entry in drivers)
    MakeKeyDimMut(row, KeywordDim("D1", d1 * 1000, None))
    MakeKeyDimMut(row, KeywordDim("D2", degrees(d2), "degree"))
    return FrameKeywords(document, True)


def emit_cold(candidate, bevel, drivers):
    fields = bevel.FieldsValue
    CheckChmfMode(bevel)
    require(fields.get("f8c8") == {"n": 0, "items": []}
            and fields["f880"]["ff0"]["items"][0]["o"].FieldsValue["f70"] == 0
            and fields["has_f3d0"] == 0,
            "fresh chamfer requires empty kernel options and unassigned live handles")
    header, top = candidate.HeaderValue, candidate.TopHeader
    config, graph = WriteConfigMut(candidate.SystemValue.RootValue, VERSION, header)
    manager = candidate.SystemValue.ManagerValue
    roots = candidate.ResolvedValue.RootsValue + (bevel,)
    resolved, snapshot = write_roots(roots, {"n": 0, "fcd8": []}, graph.MapValue, CONTEXT)
    manager_header = MakeMgrHeader(manager, candidate.ManagerHeader.FieldsValue["f60"])
    streams = dict(candidate.StreamsValue)
    streams.update({
        "Header2": WriteHeadGraph(top, VERSION),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(header, VERSION),
        "Contents/Config-0": config,
        "Contents/CMgr": WriteCmgrMut(manager, VERSION),
        "Contents/CMgrHdr2": WriteMgrHeader(manager_header, VERSION)[0],
        KResolvedFeaturesStream: resolved,
        KeywordsStream: cold_keywords(streams[KeywordsStream], bevel, drivers),
    })
    return BuildSldprt(streams, FormatVersion=4), streams, graph.MapValue.CounterValue, snapshot.CounterValue
