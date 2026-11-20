import argparse
import codecs
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring


def require(value, message):
    if not value:
        raise ValueError(message)


def walk(value, seen=None):
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    if hasattr(value, "FieldsValue") and hasattr(value, "ClassValue"):
        yield value
        yield from walk(value.FieldsValue, seen)
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk(child, seen)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from walk(child, seen)


def text(value):
    if type(value) is str:
        return value
    result = value.TextValue
    require(type(result) is str, "metadata text must retain its typed encoding")
    return result


def text_proof(value):
    value = text(value)
    return {"characters": len(value), "empty": not value, "utf8_sha256": sha256(value.encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    data = Path(row["path"]).read_bytes()
    require(sha256(data).hexdigest() == row["sha256"], "disclosed native source custody differs")
    sys.path.insert(0, str(args.sdk / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
    from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
    from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import RevisionBook
    from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import RevisionEvent
    from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import RevisionLog
    from convert.adapters.solidworks.Archive.Construction.Chronology.MakeRevBook import MakeRevBook
    from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
    from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
    for encoding in ("ascii", "utf-8", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for name in ("interchange.document.Models.DocumentProvenance", "interchange.document.Behavior.DocumentIo"):
        import_module(name)
    state = {"enabled": False, "attempts": []}

    def audit(event, arguments):
        if state["enabled"] and (event == "open" or event.startswith(("subprocess.", "socket.")) or event in ("os.system", "os.fork", "os.posix_spawn", "ctypes.dlopen")):
            state["attempts"].append(event)
            raise RuntimeError("chronology read or construction attempted external runtime access")

    sys.addaudithook(audit)
    output = {"schema": "kit.sw2026.disclosed-part-chronology-read.v1", "case": row["name"], "source_sha256": row["sha256"], "passed": False, "heldout_inputs_read": 0, "native_processes": 0}
    state["enabled"] = True
    try:
        archive = SldprtArchive.from_bytes(data)
        link = ReadNativeLink(archive, 0)
        model = link.ConfigValue.RootValue
        config_bytes, config_graph = WriteConfigMut(model, 19000, link.ConfigValue.HeaderValue)
        resolved_bytes, resolved_graph = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000, config_graph.MapValue, link.ResolvedValue.ContextValue)
        require(config_bytes == archive.require(link.ConfigName) and resolved_bytes == archive.require(link.StreamName), "chronology source critical linked streams do not reemit exactly")
        for graph in (config_graph, resolved_graph):
            require(graph.ReportValue["completed"] and not graph.ReportValue["missing_schemas"] and not graph.ReportValue["provisional_schemas"], "chronology source crossed an unqualified native schema")
        nodes = list(walk((model, link.ResolvedValue.RootsValue)))
        owners = {}
        for value in (model, *[value for value in nodes if "f2a0" in value.FieldsValue and "f2b0" in value.FieldsValue]):
            identifier = value.FieldsValue.get("f08")
            if type(identifier) is int and identifier >= 0:
                require(identifier not in owners or owners[identifier] is value, "actual source chronology has ambiguous feature identity")
                owners[identifier] = value
        headers = []
        for stream in ("Contents/Config-0-ModelHeader", "Header2"):
            header = ReadHeaderGraph(archive.require(stream), 19000)
            fields = header.FieldsValue
            users = tuple(text(value) for value in fields["f10"].FieldsValue["values"])
            companies = tuple(text(value) for value in fields["f18"].FieldsValue["values"])
            intentions, rows = [], []
            for log in ReadLogItems(fields["f20"], "moLogs_c"):
                log_fields = log.FieldsValue
                identifier = log_fields["f48"]
                require(identifier in owners, "actual revision log has no modeled feature identity")
                events, event_rows = [], []
                for event in ReadLogItems(log, "moStamp_c"):
                    event_fields = event.FieldsValue
                    operation = {0: "created", 1: "modified"}.get(event_fields["f08"])
                    require(operation is not None, "source revision operation remains outside constructor scope")
                    events.append(RevisionEvent(operation, users[event_fields["f0c"]], companies[event_fields["f10"]], event_fields["f18"], text(event_fields["f20"])))
                    event_rows.append({"operation": operation, "epoch": event_fields["f18"], "user_index": event_fields["f0c"], "company_index": event_fields["f10"], "comment": text(event_fields["f20"])})
                intentions.append(RevisionLog(owners[identifier], text(log_fields["f50"]), tuple(events)))
                rows.append({"owner_id": identifier, "owner_class": owners[identifier].ClassValue.NameValue, "caption": text(log_fields["f50"]), "events": event_rows})
            graph = MakeRevBook(RevisionBook(users, companies, tuple(intentions)))
            fields.update(f10=graph.UsersValue, f18=graph.CompaniesValue, f20=graph.LogsValue)
            generated = WriteHeadGraph(header, 19000)
            require(generated == archive.require(stream), "semantic revision reconstruction changed native header bytes")
            self_fields = fields["f38"].FieldsValue
            shared = self_fields["shared"]
            headers.append({"stream": stream, "bytes": len(generated), "sha256": sha256(generated).hexdigest(), "semantic_log_reconstruction_byte_identity": True, "new_log_nodes": True, "clock_owners": {key: fields[key] for key in ("f70", "f50", "f48")}, "counter_owners": {key: fields[key] for key in ("f08", "f40", "f44")}, "unrepresented_header_state": {key: fields[key] for key in ("f7c", "f80")}, "attribution": {"users": [text_proof(value) for value in users], "companies": [text_proof(value) for value in companies]}, "logs": rows, "self": {"name": text(shared["h10"].FieldsValue["value"]), "path": text_proof(shared["h18"].FieldsValue["value"]), "creation_epoch": shared["f28"], "save_epoch": self_fields["f60"], "cached_save_epoch": self_fields["f70"], "persisted_state": self_fields["f58"], "configuration_name": text(self_fields["refcfg"]["f08"]), "configuration_id": self_fields["refcfg"]["f10"]}})
        history = ReadHistMut(archive.require("_MO_VERSION_19000/History"), 19000).RootValue
        biography = ReadHistMut(archive.require("_MO_VERSION_19000/Biography"), 19000).RootValue
        metadata = {}
        for name, value in (("History", history), ("Biography", biography)):
            encoded = WriteHistMut(value, 19000)[0]
            require(encoded == archive.require("_MO_VERSION_19000/" + name), "typed metadata wire identity differs")
            metadata[name] = {"bytes": len(encoded), "sha256": sha256(encoded).hexdigest(), "byte_identity": True}
        states = []
        for entry in history.FieldsValue["states"]:
            fields = entry["st"]
            stamp = fields["f08"]
            codes = [value["st"]["f08"] for value in fields["f38"].FieldsValue["states"]]
            states.append({"event_epoch": stamp["f18"], "revision_status": stamp["f08"], "user_index": stamp["f0c"], "company_index": stamp["f10"], "file_version": fields["f30"], "date_codes": codes, "low_date_codes": [value & 0xFFFFFF for value in codes], "high_flags": [value & 0xFF000000 for value in codes]})
        features = []
        for identifier, feature in sorted(owners.items()):
            fields = feature.FieldsValue
            if "f2a0" not in fields:
                continue
            ticks = ((fields["f2a4"] & 0xFFFFFFFF) << 32) | (fields["f2a0"] & 0xFFFFFFFF)
            if ticks:
                seconds, fraction = divmod(ticks - 11644473600 * 10_000_000, 10_000_000)
                rebuilt = MakeFeatTime(FeatureInstant(seconds, fraction))
                require(rebuilt == {key: fields[key] for key in ("f2a0", "f2a4")}, "precise feature moment did not preserve original native time words")
                time_fact = {"filetime_seconds": seconds, "filetime_fraction_ticks": fraction, "reconstructed_word_identity": True, "zero_constructor_state": False}
            else:
                time_fact = {"filetime_seconds": None, "filetime_fraction_ticks": None, "reconstructed_word_identity": None, "zero_constructor_state": True}
            features.append({"id": identifier, "class": feature.ClassValue.NameValue, "name": fields["f18"].FieldsValue["f08"] if fields["f18"] is not None else None, **time_fact, "create_version": fields["f2b0"], "create_date_code": fields["f2b4"], "last_update_version": fields["f2b8"], "last_update_date_code": fields["f2bc"], "update_counter": fields["f29c"], "create_parasolid_behavior": fields["f2ac"], "create_service_pack": fields["f300"], "create_subservice_pack": fields["f301"]})
        records = []
        for record in biography.FieldsValue["records"]:
            fields = record["r"]
            records.append({"file_version": fields["f08"], "date_code": fields["f0c"], "language": fields["f38"], "start_filetime": {key: fields["f40"][key] for key in ("f08", "f0c")}, "end_filetime": {key: fields["fe8"][key] for key in ("f08", "f0c")}, "storage_name_start": text_proof(fields["f40"]["s5"]), "storage_name_end": text_proof(fields["fe8"]["s5"])})
        references = []
        logs_by_id = {value["owner_id"]: value for value in headers[0]["logs"]}
        for value in nodes:
            fields = value.FieldsValue
            if value.ClassValue.NameValue != "moCompSketchEntHandle_c":
                continue
            target = fields["ff0"]; identifier = target["f00"]
            log = logs_by_id.get(identifier)
            expected = log["events"][0]["epoch"] if log and log["events"] else 2592000
            references.append({"class": value.ClassValue.NameValue, "target_id": identifier, "actual_creation_event": target["f08"], "expected_first_log_event": expected, "matches_first_event": target["f08"] == expected})
        core = fromstring(archive.require("docProps/core.xml"))
        core_clocks = {child.tag: child.text for child in core if child.tag in ("{http://purl.org/dc/terms/}created", "{http://purl.org/dc/terms/}modified")}
        manager = ReadMgrHeader(archive.require("Contents/CMgrHdr2"), 19000).RootValue
        require(WriteMgrHeader(manager, 19000)[0] == archive.require("Contents/CMgrHdr2"), "manager save owner does not round trip")
        for header in headers:
            header["computed_latest_tail_event"] = max((log["events"][-1]["epoch"] for log in header["logs"] if log["events"]), default=None)
            require(header["clock_owners"]["f70"] == header["self"]["creation_epoch"], "source self creation and actual header identity disagree")
        output.update(passed=True, critical_linked_byte_identity=True, manager_header_byte_identity=True, headers=headers, metadata=metadata, feature_instants=features, history={"states": states, "independent_root_fields": {key: history.FieldsValue[key] for key in ("f28", "f2c", "f30", "f38", "f3c", "f40")}}, biography={"records": records, "new_telemetry_generated": False}, manager_save_epoch=manager.FieldsValue["f60"], model_name=model.FieldsValue["f18"].FieldsValue["f08"], physical_source_basename=Path(row["path"]).name, source_core_xml_clocks=core_clocks, selected_sketch_creation_joins=references, complete_original_preparation_admitted=False)
    finally:
        state["enabled"] = False
    output["runtime_external_attempts"] = state["attempts"]
    output["sdk_modules"] = sorted({module.__file__ for name, module in sys.modules.items() if (name == "convert" or name.startswith(("convert.", "interchange."))) and getattr(module, "__file__", None)})
    print(json.dumps(output, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
