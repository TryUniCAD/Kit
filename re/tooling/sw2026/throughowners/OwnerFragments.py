from base64 import b64encode, b64decode
from hashlib import sha256

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from OwnerDto import require


def emit(graph, settings):
    system = graph.SystemValue
    SetCfgStampMut(system.ConfigValues[0], graph.IdsValue)
    model, top, manager = MakePartHeaders(system, settings, graph.IdsValue)
    config_data, config = WriteConfigMut(system.RootValue, 19000, model)
    features = (*system.FeatureValues, graph.StockProfile.ProfileValue, graph.StockValue.FeatureValue, graph.CutValue.ProfileValue.ProfileValue, graph.CutValue.FeatureValue)
    context = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": system.ManagerValue.FieldsValue["f658"]}
    resolved_data, resolved = WriteResolMut(features, None, 19000, config.MapValue, context)
    data = {"model_header": WriteHeadGraph(model, 19000), "header2": WriteHeadGraph(top, 19000), "config": config_data, "resolved": resolved_data, "manager": WriteCmgrMut(system.ManagerValue, 19000), "manager_header": WriteMgrHdrMut(manager, 19000)[0]}
    return data, config, resolved


def encode_fragments(values):
    return {key: b64encode(value).decode("ascii") for key, value in values.items()}


def decode_fragments(values):
    require(type(values) is dict and set(values) == {"model_header", "header2", "config", "resolved", "manager", "manager_header"}, "partial owner proof has unexpected stream roles")
    return {key: b64decode(value, validate=True) for key, value in values.items()}


def identities(values):
    return {key: {"bytes": len(value), "sha256": sha256(value).hexdigest()} for key, value in sorted(values.items())}


def readback(values):
    model = ReadHeaderGraph(values["model_header"], 19000)
    top = ReadHeaderGraph(values["header2"], 19000)
    manager = ReadCmgrMut(values["manager"], 19000)
    manager_header = ReadMgrHdrMut(values["manager_header"], 19000)
    config = ReadConfigMut(values["config"], 19000, model)
    context = MakeLinkContext(config, manager)
    resolved = ReadResolvedMut(values["resolved"], 19000, config.MapValue, context)
    rebuilt = {"model_header": WriteHeadGraph(model, 19000), "header2": WriteHeadGraph(top, 19000), "manager": WriteCmgrMut(manager.RootValue, 19000), "manager_header": WriteMgrHdrMut(manager_header.RootValue, 19000)[0], "config": WriteConfigMut(config.RootValue, 19000, model)[0], "resolved": WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, config.MapValue, context)[0]}
    require(rebuilt == values, "generated partial owner archives changed during independent SDK readback")
    for graph in (config, resolved, manager, manager_header):
        require(graph.ReportValue["completed"] and not graph.ReportValue["missing_schemas"] and not graph.ReportValue["provisional_schemas"], "owner fragment has missing or opaque grammar")
    return config, resolved, manager, manager_header
