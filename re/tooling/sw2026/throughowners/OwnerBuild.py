from dataclasses import asdict, replace
from hashlib import sha256
import json
import sys

from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MakeThruOwners import MakeThruOwners
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.CheckThruInput import CheckThruInput
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from OwnerDto import decode, settings, canonical, require
from OwnerFragments import emit, identities, encode_fragments, decode_fragments, readback
from OwnerInspect import inspect


def modify(value, target, probe):
    if probe is None:
        return value, target
    if probe == "foreign_selected_owner":
        return replace(value, ScopeValue=replace(value.ScopeValue, StockValues=(replace(value.ShapeValue.StockValue),))), target
    if probe == "target_unit_mismatch":
        return value, replace(target, DocumentUnits=replace(target.DocumentUnits, LengthUnit="m"))
    if probe == "target_datum_mismatch":
        return value, replace(target, SystemValue=replace(target.SystemValue, PlaneNames=tuple((axis,name+" altered") for axis,name in target.SystemValue.PlaneNames)))
    raise ValueError("unknown owner build probe")


def main(request, phase, guard, root):
    require(set(request) in ({"input","written_at"},{"input","written_at","probe"},{"input","written_at","fragments"}), "owner process has unknown inputs")
    value = decode(request["input"])
    target = settings(value, request["written_at"])
    value, target = modify(value, target, request.get("probe"))
    CheckThruInput(value, target)
    graph = None
    if phase == "build":
        graph = MakeThruOwners(value, target)
        fragments, config, resolved = emit(graph, target)
    elif phase == "audit":
        fragments = decode_fragments(request["fragments"])
        config, resolved, _, _ = readback(fragments)
    else:
        raise ValueError("expected owner build or audit")
    grammar = inspect(value, config, resolved, phase=="build")
    result = {"passed":True,"phase":phase,"input_sha256":sha256(canonical(request["input"])).hexdigest(),"fragments":identities(fragments),"grammar":grammar,"runtime_input_file_reads":0,"full_writer_outputs":0,"source_equivalence":False,"native_acceptance":False,"public_writer_qualified":False,"denied_events":list(guard.denied)}
    if graph is not None:
        require(len(graph.BindValues) == len({item.SourceId for item in graph.BindValues}), "source bindings are not unique")
        bindings = []
        for item in graph.BindValues:
            bindings.append({"source_id":item.SourceId,"role":item.RoleValue,"owner_class":item.OwnerValue.ClassValue.NameValue,"target_class":item.Value.ClassValue.NameValue if isinstance(item.Value,ArchiveNode) else "typed_inline_record"})
        circle = graph.CutValue.ProfileValue.GeometryValue
        require(circle.ArcValue.FieldsValue["_center"] is circle.CenterValue and circle.CenterValue is not circle.MarkerValue, "fresh circle lost its actual center object")
        require(graph.ScopeValue.StockValue is value.ShapeValue.StockValue and graph.ScopeValue.AtomValue is not graph.CutValue.FeatureValue, "source stock and final cut owner were conflated")
        result.update(bindings=bindings,allocator_next=graph.IdsValue.NextValue,fragment_payloads=encode_fragments(fragments))
    research = [name for name,module in tuple(sys.modules.items()) if str(getattr(module,"__file__","")).startswith(str(root/"re")+"/") and name not in {"__main__","OwnerDto","OwnerBuild","OwnerGuard","OwnerFragments","OwnerInspect","OwnerSource","OwnerMutations"}]
    require(not guard.denied and not research, "owner construction imported unrelated research code or accessed runtime input")
    result["sdk_runtime_research_imports"] = 0
    return result
