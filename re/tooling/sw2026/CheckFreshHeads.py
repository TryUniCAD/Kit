from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

from AuthorFreshHead import (
    CASES,
    build_inputs,
    directory_record,
    header_record,
    locator,
    native_node,
)
from CheckManagerDirectory import replay_directory
from CheckStandaloneHeaders import replay_header
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Construction.Header.MakePartHeads import (
    MakePartHeads,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


VERSION = 19000
TOP = "Header2"
MODEL = "Contents/Config-0-ModelHeader"
MANAGER = "Contents/CMgrHdr2"
CONTROLS = {
    "ladder": (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659",
        "9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659",
        "caa3cb00d615faa644ca20786ae98ff6a4896237648e90c6ed431694f86bb352",
    ),
    "concave": (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "0d8551d418c050d4f3d737edac10225af00146037f6eefa2b60511b8db4ad53d",
        "f4cce850be7777c5f6aad10d0bc46bda2e60448fac1ca4cde309df56063516aa",
        "9073ac9c452c912ff17b7e788b0e2f4715c9253eb4032fa3771566f2767c4225",
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def deny_external_access():
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    denied = []

    def audit(event, _args):
        if event in (
            "open", "os.listdir", "os.scandir", "os.system", "os.exec",
            "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen",
        ) or event.startswith("socket."):
            denied.append(event)
            raise PermissionError("part header codec attempted external access")

    sys.addaudithook(audit)
    return denied


def header_observation(data, case, role):
    root = ReadHeaderGraph(data, VERSION)
    fields = root.FieldsValue
    self_node = fields["f38"]
    file = GetFileRef(self_node)
    user, company = fields["f10"], fields["f18"]
    log_list = fields["f20"]
    log, = log_list.FieldsValue["items"]
    stamp, = log.FieldsValue["items"]
    handles = self_node.FieldsValue["shared"]
    words = [
        fields["fec"], fields["f08"], fields["f70"], fields["f50"],
        fields["f48"], self_node.FieldsValue["f60"],
    ]
    require(words == [
        role, case["feature_ids"][-1] + 1, case["created"], case["modified"],
        case["updated"], case["saved"],
    ], "role, persistent allocation or clock provenance changed")
    require(
        file.NameValue == case["name"] and file.PathValue == locator(case)
        and file.ConfigValue == case["configuration"] and file.KindValue == 2
        and handles["f28"] == case["created"]
        and self_node.FieldsValue["refcfg"]["f10"] == case["config_id"]
        and fields["f30"] is None,
        "self identity changed",
    )
    require(
        user.FieldsValue["items"] == (case["author"],)
        and company.FieldsValue["items"] == (case["company"],)
        and log.FieldsValue["f48"] == case["root_id"]
        and log.FieldsValue["name"] == case["name"]
        and stamp.FieldsValue["f18"] == case["created"]
        and stamp.FieldsValue["operation"] == case["revision"],
        "revision identity or attribution changed",
    )
    nodes = (root, user, company, log_list, log, stamp, self_node,
             handles["h18"], handles["h10"])
    indices = [node.IndexValue for node in nodes]
    require(indices == [2, 4, 5, 7, 9, 11, 13, 15, 16], "standalone map changed")
    require(root.EndOffset == len(data) and WriteHeadGraph(root, VERSION) == data,
            "fresh header did not re-emit all bytes")
    return {
        "role": role, "indices": indices, "sha256": sha256(data).hexdigest(),
        "bytes": len(data), "next_persistent_id": fields["f08"],
    }


def direct_slot(root, model_header, top_header):
    self_node = model_header.FieldsValue["f38"]
    require(HeaderRefNodes(model_header, VERSION) == (self_node,),
            "model header did not expose its actual self node")
    require(top_header.FieldsValue["f38"] is self_node,
            "constructed header roles did not share the same self object")
    require(model_header.FieldsValue["f20"] is not top_header.FieldsValue["f20"],
            "constructed header roles shared a mutable revision list")
    mapping = ArchiveMaps(1)
    require(AddEntryMut(mapping, root.ClassValue) == 1, "part class allocation changed")
    require(AddEntryMut(mapping, root) == 2, "part object allocation changed")
    BindNodesMut(mapping, HeaderRefNodes(model_header, VERSION))
    require(FindObject(mapping, 3) is self_node and self_node.IndexValue is None,
            "the direct map changed the original self object or attached the wrong one")
    require(mapping.BaseValue == mapping.CounterValue == 4, "direct map boundary changed")
    return {"slots": [1, 2, 3], "base": 4, "next": 4}


def authored(case):
    inputs = build_inputs(case)
    root, manager, _header, _self, allocator = inputs
    config = manager.FieldsValue["f360"]
    owners = (root, manager, config, root.FieldsValue["f18"], config.FieldsValue["f18"])
    state = [dict(node.FieldsValue) for node in owners], dict(allocator.Allocations)
    model_header, top_header, directory = MakePartHeads(*inputs)
    top_bytes = WriteHeadGraph(top_header, VERSION)
    model_bytes = WriteHeadGraph(model_header, VERSION)
    manager_bytes, manager_graph = WriteMgrHeader(directory, VERSION)
    require(top_bytes == header_record(case, 0), "top header differs from independent wire")
    require(model_bytes == header_record(case, 1), "model header differs from independent wire")
    require(top_bytes != model_bytes, "the two generated header roles collapsed")
    require(manager_bytes == directory_record(case), "manager differs from independent wire")
    top = header_observation(top_bytes, case, 0)
    model = header_observation(model_bytes, case, 1)
    manager_result = replay_directory(manager_bytes, VERSION)
    require(
        manager_result["entry_indices"] == [1, 2, 3, 4]
        and manager_result["row_indices"] == [4]
        and manager_result["next_index"] == manager_graph.MapValue.CounterValue == 5,
        "directory used another archive's map",
    )
    aliases = direct_slot(root, model_header, top_header)
    require(state == ([dict(node.FieldsValue) for node in owners], allocator.Allocations),
            "head construction changed the supplied part or its allocator")
    return {TOP: top, MODEL: model, MANAGER: manager_result, "direct_map": aliases}


def check_refusal(name, edit, reason):
    root, manager, header, output, allocator = build_inputs(CASES["straight"])
    try:
        MakePartHeads(*edit(root, manager, header, output, allocator))
    except (TypeError, ValueError) as error:
        require(reason in str(error), f"{name} refused at the wrong boundary: {error}")
        return name
    raise ValueError(f"{name} unexpectedly returned a header graph")


def update_manager(root, manager, header, output, allocator, field, value):
    manager.FieldsValue[field] = value
    return root, manager, header, output, allocator


def update_config(root, manager, header, output, allocator, field, value):
    manager.FieldsValue["f360"].FieldsValue[field] = value
    return root, manager, header, output, allocator


def refusals():
    duplicate = lambda root, manager, header, output, alloc: update_manager(
        root, manager, header, output, alloc, "f368",
        native_node("moPartConfiguration_c", dict(manager.FieldsValue["f360"].FieldsValue)),
    )
    return [
        check_refusal(
            "foreign_part",
            lambda root, manager, header, output, alloc: (
                native_node("moPart_c", dict(root.FieldsValue)), manager, header, output, alloc
            ),
            "requires the same actual part",
        ),
        check_refusal("distinct_selector", duplicate, "active independent configuration"),
        check_refusal(
            "duplicate_count",
            lambda *args: update_manager(*args, "f40c", 2),
            "requires one actual independent configuration",
        ),
        check_refusal(
            "configuration_parent",
            lambda *args: update_config(*args, "f6a0", native_node("moPartConfiguration_c", {})),
            "active independent configuration",
        ),
        check_refusal(
            "foreign_configuration_owner",
            lambda *args: update_config(*args, "owner", native_node("moPart_c", {})),
            "active independent configuration",
        ),
        check_refusal(
            "excluded_configuration",
            lambda *args: update_config(*args, "fbe0", 1),
            "does not admit excluded configurations",
        ),
        check_refusal(
            "comment_sidecar",
            lambda *args: update_config(*args, "f2f0", native_node("suObList", {"items": ()})),
            "does not admit excluded configurations or comment sidecars",
        ),
        check_refusal(
            "unallocated_part",
            lambda root, manager, header, output, alloc: (
                root, manager, header, output, PersistentIds(alloc.NextValue)
            ),
            "counter must follow the actual allocated model identifier",
        ),
        check_refusal(
            "assembly_root",
            lambda root, manager, header, output, alloc: wrong_root(
                manager, header, output, alloc, "moAssembly_c"
            ),
            "requires a concrete schema one moPart_c",
        ),
        check_refusal(
            "early_save",
            lambda root, manager, header, output, alloc: (
                root, manager, header, replace(output, SavedAt=header.ModifiedAt - 1), alloc
            ),
            "native save event precedes the modeled modification time",
        ),
        check_refusal(
            "nonpart_extension",
            lambda root, manager, header, output, alloc: (
                root, manager, header, replace(output, PathName="C:\\Work\\Part.SLDASM"), alloc
            ),
            "native self path must identify a part",
        ),
    ]


def wrong_root(manager, header, output, allocator, class_name):
    alternate = native_node(class_name, {})
    manager.FieldsValue["owner"] = alternate
    return alternate, manager, header, output, allocator


def read_control(name):
    path, source_hash, top, model, manager = CONTROLS[name]
    path = ROOT / "re/solidworks/v2026/corpus" / path
    original = path.read_bytes()
    require(sha256(original).hexdigest() == source_hash, "disclosed source hash changed")
    denied = deny_external_access()
    archive = SldprtArchive.from_bytes(original, path)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "disclosed container profile changed")
    reports = {
        TOP: replay_header(TOP, archive.require(TOP), VERSION),
        MODEL: replay_header(MODEL, archive.require(MODEL), VERSION),
        MANAGER: replay_directory(archive.require(MANAGER), VERSION),
    }
    require([reports[field]["sha256"] for field in (TOP, MODEL, MANAGER)] == [top, model, manager],
            "disclosed stream hash changed")
    require(not denied, "disclosed typed replay attempted external access")
    return {"source_sha256": source_hash, "streams": reports, "external_accesses": len(denied)}


def main():
    parser = ArgumentParser(description="Observe fresh part header and directory ownership")
    parser.add_argument("case", choices=(*CASES, *CONTROLS, "refusals"))
    case = parser.parse_args().case
    if case in CONTROLS:
        report = read_control(case)
    else:
        denied = deny_external_access()
        report = {"refused": refusals()} if case == "refusals" else authored(CASES[case])
        require(not denied, "fresh header construction attempted external access")
        report["external_accesses"] = len(denied)
    print(dumps({"case": case, **report}, sort_keys=True))


if __name__ == "__main__":
    main()
