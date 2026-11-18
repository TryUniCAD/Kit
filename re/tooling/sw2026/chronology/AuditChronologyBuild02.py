import argparse
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--mode", choices=("coupled", "split"), required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    sys.path[:0] = [str(args.sdk / "src"), str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import MakeRevPart
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
    from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import FeatureTime
    from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
    from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from BuildChronology01 import compose
    from MakeRevolveRequest01 import make_request
    from interchange.document.Behavior.DocumentIo import ToJson
    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for name in ("interchange.brep.Validation.BrepValidate", "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate", "interchange.document.Validation.PlaneRevValidate", "interchange.document.Validation.DistExtValidate"):
        import_module(name)
    state = {"enabled": False, "attempts": []}

    def audit(event, arguments):
        if state["enabled"] and (event == "open" or event.startswith(("subprocess.", "socket.")) or event in ("os.system", "os.fork", "os.posix_spawn", "ctypes.dlopen")):
            state["attempts"].append(event)
            raise RuntimeError("chronology construction attempted external runtime access")

    sys.addaudithook(audit)
    state["enabled"] = True
    result = {"schema": "kit.sw2026.part-chronology-construction-process.v1", "passed": False, "mode": args.mode, "heldout_inputs_read": 0, "native_processes": 0}
    try:
        document, settings = make_request(row["spec"])
        baseline = MakeRevPart(document, settings)
        require(sha256(baseline.BytesValue).hexdigest() == row["sha256"], "previous exact generated revolve bytes changed")
        first, second = compose(document, settings, args.mode), compose(document, settings, args.mode)
        require(first["bytes"] == second["bytes"], "fresh chronological construction is not deterministic")
        require(not any("partition" in name.casefold() or "delta" in name.casefold() for name in first["streams"]), "chronology construction transmitted a geometry cache")
        require(first["headers"][0].FieldsValue["f38"] is first["headers"][1].FieldsValue["f38"], "header roles lost their actual shared self object")
        first_events = ReadLogItems(ReadLogItems(first["headers"][0].FieldsValue["f20"], "moLogs_c")[0], "moStamp_c")
        second_events = ReadLogItems(ReadLogItems(first["headers"][1].FieldsValue["f20"], "moLogs_c")[0], "moStamp_c")
        require(first_events[0] is not second_events[0], "different header roles shared a mutable stamp node")
        changed = [name for name in baseline.StreamsValue if baseline.StreamsValue[name] != first["streams"][name]]
        if args.mode == "coupled":
            require(first["bytes"] == baseline.BytesValue and not changed, "new coupled intent factory changed original default output")
        else:
            require(set(changed) == {"Header2", "Contents/Config-0-ModelHeader", "Contents/CMgrHdr2", "_MO_VERSION_19000/History"}, "independent chronology changed a nonowned stream")
        archive = SldprtArchive.from_bytes(first["bytes"])
        link = ReadNativeLink(archive, 0)
        config_bytes, config = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
        resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000, config.MapValue, link.ResolvedValue.ContextValue)
        require(config_bytes == archive.require(link.ConfigName) and resolved_bytes == archive.require(link.StreamName), "fresh part topology or references failed linked wire readback")
        clocks = []
        for stream in ("Header2", "Contents/Config-0-ModelHeader"):
            graph = ReadHeaderGraph(archive.require(stream), 19000)
            require(WriteHeadGraph(graph, 19000) == archive.require(stream), "new header graph did not round trip")
            fields = graph.FieldsValue
            logs = ReadLogItems(fields["f20"], "moLogs_c")
            times = [event.FieldsValue["f18"] for value in logs for event in ReadLogItems(value, "moStamp_c")]
            expected = [event.EventAt for value in first["book"].LogsValue for event in value.EventsValue]
            require(times == expected, "actual revision order or event clocks changed")
            users = tuple(value.TextValue for value in fields["f10"].FieldsValue["values"])
            companies = tuple(value.TextValue for value in fields["f18"].FieldsValue["values"])
            require(users == first["book"].UsersValue and companies == first["book"].CompaniesValue, "authored attribution vocabulary or unicode differs")
            for value, intention in zip(logs, first["book"].LogsValue, strict=True):
                require(value.FieldsValue["f48"] == intention.OwnerValue.FieldsValue["f08"] and value.FieldsValue["f50"].TextValue == intention.CaptionValue, "log ownership or independent caption differs")
                for stamp, event in zip(ReadLogItems(value, "moStamp_c"), intention.EventsValue, strict=True):
                    actual = stamp.FieldsValue
                    require(actual["f08"] == {"created": 0, "modified": 1}[event.OperationValue] and users[actual["f0c"]] == event.UserName and companies[actual["f10"]] == event.CompanyName and actual["f20"].TextValue == event.CommentText, "semantic event or actual attribution join differs")
            clocks.append({"stream": stream, "creation": fields["f70"], "archive": fields["f50"], "update": fields["f48"], "root_first_event": times[0], "event_count": len(times), "log_count": len(logs), "self_creation": fields["f38"].FieldsValue["shared"]["f28"], "self_save": fields["f38"].FieldsValue["f60"]})
        history = ReadHistMut(archive.require("_MO_VERSION_19000/History"), 19000).RootValue
        require(WriteHistMut(history, 19000)[0] == archive.require("_MO_VERSION_19000/History"), "new history event failed wire readback")
        history_at = history.FieldsValue["states"][0]["st"]["f08"]["f18"]
        require(history_at == first["input"].HistoryValue.CreatedAt, "version event became a header clock")
        moment = next(settings.SystemValue.CreatedAt + offset for offset in range(430) if (((settings.SystemValue.CreatedAt + offset + 11644473600) * 10_000_000) & 0xFFFFFFFF) + 9_999_999 > 0xFFFFFFFF)
        require(MakeFeatTime(FeatureInstant(moment, 0)) == FeatureTime(moment), "precise time constructor changed the existing whole second result")
        ticks = (moment + 11644473600) * 10_000_000 + 9_999_999
        precise = MakeFeatTime(FeatureInstant(moment, 9_999_999))
        require(((precise["f2a4"] & 0xFFFFFFFF) << 32) | (precise["f2a0"] & 0xFFFFFFFF) == ticks, "fractional time carry or signed words differ")
        modes = {}
        for name, options in (("history", {"include_brep": False, "include_tessellation": False}), ("default", {})):
            value = open_document(first["bytes"], source_format="solidworks.sldprt", strict=True, **options)
            before = open_document(baseline.BytesValue, source_format="solidworks.sldprt", strict=True, **options)
            value.assert_valid()
            require(value.feature_timeline == before.feature_timeline and value.sketches == before.sketches and value.parameters == before.parameters and value.bodies == before.bodies, "authored geometry history or body association changed")
            if name == "default":
                require(value.brep is not None and not value.brep.validate(frozenset(body.id for body in value.bodies)), "strict cacheless B-rep validation failed")
                require(value.brep == before.brep and not value.brep_payloads, "chronology changed geometry or manufactured native payloads")
            modes[name] = {"document_sha256": sha256(ToJson(value).encode()).hexdigest(), "bodies": len(value.bodies), "brep_bodies": len(value.brep.bodies) if value.brep else 0, "payloads": len(value.brep_payloads), "authored_geometry_unchanged": True}
        result.update(passed=True, sha256=sha256(first["bytes"]).hexdigest(), previous_sha256=row["sha256"], changed_streams=changed, streams={name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in first["streams"].items()}, clocks=clocks, history_event=history_at, modes=modes, header_lengths={name: {"before": len(baseline.StreamsValue[name]), "after": len(first["streams"][name])} for name in ("Header2", "Contents/Config-0-ModelHeader")}, computed_attribution_exact=True, fractional_word_carry_exact=True, actual_shared_self_alias=True, separate_header_stamps=True, deterministic_two_builds=True, full_original_source_preparation_admitted=False)
    finally:
        state["enabled"] = False
    result["runtime_external_attempts"] = state["attempts"]
    result["sdk_modules"] = sorted({module.__file__ for name, module in sys.modules.items() if (name == "convert" or name.startswith(("convert.", "interchange."))) and getattr(module, "__file__", None)})
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
