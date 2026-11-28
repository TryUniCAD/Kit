from argparse import ArgumentParser
from dataclasses import replace
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from AssemblyContentIndex import native_path
from ConfigHeaderExchangeModel import project_active_config
from D01AssemblyPropertyIntent import CORE, read_core
from ProveAssemblyContentIndex import prepare_package, registry
from ProveD01AssemblyChronology import compose_streams
from ProveD01AssemblyInfo import (
    KInfoXml, MEASUREMENTS, MODEL, MODEL_PIN, PRIOR, PRIOR_PIN, PROOF, PROOF_PIN,
    checked, fingerprint, generate, model_inputs, neutral_request, refuse, require, source_cases,
    stream_diff, system_rows, wire,
)
from ProveD01ParentDisplay import build_arguments

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.AsmInfoInput import AsmInfoInput
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.MakeAsmInfo import MakeAsmInfo
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.MakeInfoXml import MakeInfoXml
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

BASE = "f835b1395a6e0159e2e08ae45d26a3239e0151ed"
INFO = "D01AssemblyInformation01.json"
INFO_PIN = "874fc7896223235a3258c4f4bf4527850fffff71547b183adff7457198005edf"
HERE_OWNER = Path("src/convert/adapters/solidworks/Archive/Construction")


def saved_controls(root, receipts):
    controls = {}
    known = receipts[INFO]["source_controls"]
    for label, path, pin in source_cases(root, receipts[PROOF]):
        archive = SldprtArchive.from_bytes(checked(path, pin))
        model = ReadNativeLink(archive, 0).ConfigValue
        header = ReadHeaderGraph(archive.require("Header2"), 19000)
        config = project_active_config(ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue)
        actor, created, saved = read_core(archive.require(CORE))
        title, locator = native_path(header.FieldsValue["f38"], 3)
        require(ReadNodeName(model.RootValue) == title and
                model.HeaderValue.FieldsValue["f38"].FieldsValue["f60"] == header.FieldsValue["f38"].FieldsValue["f60"] == saved,
                "saved core modified time or model title differs from the paired headers")
        info = MakeInfoXml(model.RootValue, path.name, locator, ReadNodeName(config), saved,
                           AsmInfoInput(created, actor, -480, "en-US"))
        digest = fingerprint(info)
        require(info == archive.require(KInfoXml) and digest == known[label]["stream_sha256"]
                and known[label]["source_sha256"] == pin, "SDK information grammar differs: " + label)
        header_created = header.FieldsValue["f70"]
        require(model.HeaderValue.FieldsValue["f70"] == header_created, "binary headers disagree on their creation event")
        controls[label] = {"source_sha256": pin, "information_sha256": digest, "property_rows": len(system_rows(info)),
                           "core_creation_minus_header_seconds": created - header_created,
                           "core_modified_matches_both_headers": True}
    require(controls.keys() == known.keys() and len(controls) == 12, "saved information cohort changed")
    return controls


def alternate_model(arguments, settings):
    child, recipe, *mates = arguments
    output = SelfFileInput(r"C:\KitInfo\R&D – μ assembly.SLDASM", recipe.OutputValue.SavedAt)
    edited = replace(recipe, OutputValue=output, NameValue=PureWindowsPath(output.PathName).stem,
                     ModelName="Independent chassis", ConfigName="Workshop state",
                     DocumentUnits=UnitInput("in", "degree", "ips", 5))
    actor = "Independent evidence & review"
    local = replace(settings, SaveActor=actor, OffsetMinutes=780)
    blank = MakeCylAsm(child, edited, *mates)
    latest = MakeCylAsm(child, replace(edited, InformationValue=local), *mates)
    plain, emitted = (SldprtArchive.from_bytes(row.BytesValue) for row in (blank, latest))
    require(stream_diff(plain, emitted) == {KInfoXml}
            and latest.ChildValue is blank.ChildValue is child
            and emitted.require(KInfoXml) == latest.StreamsValue[KInfoXml],
            "authored information altered another linked model owner")
    values = dict(system_rows(emitted.require(KInfoXml)))
    wanted = {"SW-File Name": "R&D – μ assembly", "SW-BOM Part Number": "Independent chassis",
              "SW-Folder Name": "C:\\KitInfo\\", "SW-Configuration Name": "Workshop state",
              "SW_UnitSystem": "3", "SW_UnitsLinear": "3", "SW_UnitsDualLinear": "0",
              "SW_UnitsLinearDecimalPlaces": "5", "SW-Last Saved By": actor}
    require(all(values[key] == value for key, value in wanted.items()),
            "authored information path, model title, configuration, units or clock lost ownership")
    return {"default_parent_sha256": fingerprint(blank.BytesValue), "parent_sha256": fingerprint(latest.BytesValue),
            "information_sha256": fingerprint(emitted.require(KInfoXml)),
            "local_save_date": values["SW-Short Date"], "field_values": wanted,
            "prior_parent_streams_unchanged": len(plain.streams), "property_rows": len(values)}


def refusals(state, headers, recipe, settings, arguments):
    output = recipe.OutputValue
    same_top = ArchiveNode(headers[1].ClassValue, dict(headers[1].FieldsValue))
    file = headers[1].FieldsValue["f38"]
    same_top.FieldsValue["f38"] = ArchiveNode(file.ClassValue, dict(file.FieldsValue))
    detached = replace(state, CurrentConfig=ArchiveNode(state.CurrentConfig.ClassValue, dict(state.CurrentConfig.FieldsValue)))
    child, _, *mates = arguments
    custom = replace(recipe, InformationValue=settings, DocumentUnits=UnitInput("mm", "degree", "custom", 5, "kg"))
    return {
        "detached_header": refuse(lambda: MakeAsmInfo(state, (headers[0], same_top), output, settings), "paired self file"),
        "detached_configuration": refuse(lambda: MakeAsmInfo(detached, headers, output, settings), "sole active configuration"),
        "foreign_locator": refuse(lambda: MakeAsmInfo(state, headers, replace(output, PathName=r"C:\KitInfo\Other.SLDASM"), settings),
                                  "paired self file"),
        "wrong_save_event": refuse(lambda: MakeAsmInfo(state, headers, replace(output, SavedAt=output.SavedAt + 1), settings),
                                   "paired self file"),
        "future_core_creation": refuse(lambda: MakeAsmInfo(state, headers, output, replace(settings, CreatedAt=output.SavedAt + 1)),
                                        "follow its actual core creation"),
        "foreign_locale": refuse(lambda: replace(settings, LocaleName="en-GB"), "explicit U.S. English local clock"),
        "invalid_offset": refuse(lambda: replace(settings, OffsetMinutes=True), "explicit U.S. English local clock"),
        "independent_mass_length": refuse(lambda: MakeCylAsm(child, custom, *mates), "ordinary inherited mass length"),
    }


def worker(payload, prior_config, prior_model):
    require(set(payload) == {"neutral", "header_event", "model_clock"}, "unexpected information worker input")
    request, documents, models, properties, _ = prepare_package(payload["neutral"])
    reg = registry()
    parent, original_child, prior, accesses = generate(payload, prior_config)
    require(prior["parent_sha256"] == prior_model, "previous complete 34-stream parent changed")
    ordinary, bundle = compose_streams(request["models"], request["chronology"], documents, models, reg)
    arguments = build_arguments(request["models"]["after"], documents[1], models[1])
    recipe = arguments[1]
    settings = AsmInfoInput(properties.created_at, properties.save_actor, -480, "en-US")
    headers = bundle.HeaderValue, bundle.TopHeader
    state = bundle.StateValue
    with_info = EmitAsmStreams(state, bundle.ChildValue, replace(recipe, InformationValue=settings),
                               headers, bundle.OccurrenceValues, bundle.MateValues).StreamsValue
    info = with_info.pop(KInfoXml)
    require(all(ordinary[name] == value for name, value in with_info.items())
            and set(ordinary) - with_info.keys() == {"ThirdPtyStore/VisualStates"}
            and bundle.ChildValue.BytesValue == original_child,
            "adding information through the shared emitter changed earlier parent streams or the child")
    require(info == MakeAsmInfo(state, headers, recipe.OutputValue, settings),
            "the actual assembly emitter used a different information owner")
    before = SldprtArchive.from_bytes(parent)
    require(KInfoXml not in before.streams and len(before.streams) == 34
            and all(before.require(name) == value for name, value in ordinary.items()),
            "the earlier complete container disagrees with the shared emitter's other streams")
    current = BuildSldprt(before.streams | {KInfoXml: info}, FormatVersion=4)
    after = SldprtArchive.from_bytes(current)
    require(stream_diff(before, after) == {KInfoXml} and len(after.streams) == 35,
            "the earlier D01 transport order or stream inventory changed")
    alt = alternate_model(arguments, settings)
    rejected = refusals(state, headers, recipe, settings, arguments)
    values = dict(system_rows(info))
    require(alt["local_save_date"] != values["SW-Short Date"] and not accesses,
            "same-locator controls did not vary authored local date or attempted external reads")
    return {"baseline_sha256": prior_model, "child_sha256": fingerprint(original_child),
            "parent_sha256": fingerprint(current), "information_sha256": fingerprint(info),
            "property_rows": len(values), "parent_streams": len(after.streams),
            "prior_parent_streams_unchanged": len(before.streams), "alternate": alt,
            "owner_refusals": rejected, "runtime_external_accesses": len(accesses)}


def main():
    parser = ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--disclosures", type=Path)
    action.add_argument("--worker", nargs=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin), *args.worker)))
        return
    require(args.output is not None, "supply an unused output path")
    pins = {PRIOR: PRIOR_PIN, PROOF: PROOF_PIN, MODEL: MODEL_PIN, INFO: INFO_PIN}
    receipts = {name: json.loads(checked(MEASUREMENTS / name, pin)) for name, pin in pins.items()}
    controls = saved_controls(args.disclosures, receipts)
    request = wire(model_inputs(neutral_request(args.disclosures, receipts[PROOF]), receipts[PRIOR]))
    original = receipts[MODEL]["generated"]
    command = (sys.executable, "-I", "-B", str(HERE), "--worker",
               original["prior_parent_sha256"], original["parent_sha256"])
    first, second = (subprocess.run(command, input=request, capture_output=True, timeout=120) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent model workers differ")
    result = json.loads(first.stdout)
    previous = receipts[INFO]["generated"]
    expected = previous["profiles"]["working_destination"]
    require(result["child_sha256"] == previous["child_sha256"] and
            all(result[key] == expected[key] for key in ("parent_sha256", "information_sha256", "property_rows")),
            "SDK information composition changed the earlier D01 parent, child or info bytes")
    repository = HERE.parents[5]
    module = repository / HERE_OWNER
    owners = (module / "Assembly/AssemblyInput.py", module / "Assembly/Metadata/MakeAsmCommon.py",
              module / "Assembly/Metadata/MakeAsmAux.py", module / "NestedAssemblies/EmitNestedAsm.py",
              *sorted((module / "Assembly/Metadata/Information").glob("*.py")), HERE)
    result = {"schema": "kit.sw2026.sdk-assembly-information.v1", "base": BASE,
              "pinned_receipts": pins, "source_controls": controls, "generated": result,
              "guarded_generated_workers": 2, "native_processes_started": 0, "heldout_inputs_read": 0,
              "whole_source_admitted": False, "worker_request_sha256": fingerprint(request),
              "source_sha256": {str(path.relative_to(repository)): fingerprint(path.read_bytes()) for path in owners}}
    with args.output.open("xb") as target:
        target.write(wire(result))


if __name__ == "__main__":
    main()
