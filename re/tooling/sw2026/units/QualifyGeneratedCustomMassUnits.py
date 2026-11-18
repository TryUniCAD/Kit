from argparse import ArgumentParser
from math import isclose
from pathlib import Path
import json
import sys


sys.path.append(str(Path(__file__).resolve().parent))
from QualifyDocumentMassUnits import checked, digest, require


def snapshot(raw, mass, expected_depth):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    config = link.ConfigValue
    fields = config.RootValue.FieldsValue
    user = fields["f9b8"]
    table = {item["o"].ClassValue.NameValue: item["o"] for item in user.FieldsValue["items"]}
    density = table["moDensityUnits_c"].FieldsValue
    length = table["moLengthUserUnits_c"]
    system = table["moUnitSysUnits_c"].FieldsValue["fb0"]
    independent = density["fb8"]
    require(system == 3 and density["fc4"] == (1 if mass == "g" else 2)
            and density["fcc"] == 0 and density["fc0"] == density["fc8"] == 3,
            "custom mass or volume unit did not survive inside its document owner")
    require(independent is not length and independent.ClassValue == length.ClassValue
            and independent.FieldsValue == dict(length.FieldsValue, fb8=None, f88=0.0),
            "custom mass density no longer owns its separately derived length format")
    cfg, context = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                19000, context.MapValue, link.ResolvedValue.ContextValue)
    definition, manager = [archive.require(f"Contents/{field}") for field in ("Definition", "CMgr")]
    exact = {
        "Definition": WriteModelDef(ReadModelDef(definition, 19000).GraphValue).OutputValue == definition,
        "CMgr": WriteCmgrMut(ReadCmgrMut(manager, 19000).RootValue, 19000) == manager,
        "Config-0": cfg == archive.require(link.ConfigName),
        "ResolvedFeatures": resolved == archive.require(link.StreamName),
    }
    require(all(exact.values()), "custom mass archived model did not re-emit all four typed streams")
    model = open_document(raw, source_format="solidworks.sldprt", include_tessellation=False)
    model.assert_valid()
    feature, = [item for item in model.feature_timeline if item.name == "Boss-Extrude1"]
    depth = feature.definition.length
    require(depth.unit == "mm" and isclose(depth.value / 1000, expected_depth, abs_tol=1e-12, rel_tol=2e-7),
            "normal readback changed the real driving depth")
    shape = model.brep
    topology = [len(getattr(shape, role)) for role in ("vertices", "edges", "faces", "shells", "bodies")]
    require(topology == [8, 12, 6, 1, 1], "normal readback changed the modeled body topology")
    return {
        "file_sha256": digest(raw), "native_system_code": system, "native_mass_code": density["fc4"],
        "analysis_table_present": fields["f9c0"] is not None, "nested_density_length_verified": True,
        "normal_read_topology": topology, "normal_read_driving_depth_m": depth.value / 1000,
        "typed_stream_reemission": exact,
    }


def inspect_case(root, case, native):
    role = case["name"] + "-" + case["mass"]
    initial = native["phases"][role + "/Initial"]
    reopen = native["phases"][role + "/Reopen"]
    require(initial["passed"] and reopen["passed"] and initial["open_diagnostics"] == reopen["open_diagnostics"] == [0, 0],
            "custom mass native case has incomplete lifecycle evidence")
    initial_record = f"Inspection/{role}/Initial/Record.json"
    reopen_record = f"Inspection/{role}/Reopen/Record.json"
    checked(root, initial_record, initial["record_sha256"])
    checked(root, reopen_record, reopen["record_sha256"])
    observed_density = []
    for row in (initial["initial"], initial["edited"], reopen["initial"]):
        physical = row["geometry_m"]
        ratio = physical["mass"] / physical["volume"]
        require(isclose(ratio, 1.0, rel_tol=1e-9, abs_tol=1e-12),
                "custom display units changed the effective unassigned body density")
        observed_density.append(ratio)
    return {
        "role": role, "native_record_sha256": [initial["record_sha256"], reopen["record_sha256"]],
        "numeric_native_checks": initial["numeric_checks"] + reopen["numeric_checks"],
        "effective_density_kg_per_m3": observed_density,
        "generated": snapshot(checked(root, case["input"], case["sha256"]), case["mass"], case["dimensions_m"][2]),
        "saved_and_reopened": snapshot(
            checked(root, f"Inspection/{role}/Initial/{case['name']}.SLDPRT", initial["saved_sha256"]),
            case["mass"],
            case["edit_depth_m"],
        ),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify exact generated and saved custom mass archive ownership")
    parser.add_argument("kit", type=Path)
    parser.add_argument("packet_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-result-sha256", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.kit.resolve(strict=True) / "src"))
    root = args.packet_root.resolve(strict=True)
    packet = json.loads(checked(root, "Packet.json", args.packet_sha256))
    native = json.loads(checked(root, "Inspection/Result.json", args.native_result_sha256))
    require(native["packet_sha256"] == args.packet_sha256 and native["passed"] and native["controls_healthy"]
            and native["distinct_native_processes"] == 10 and native["heldout_inputs_read"] == 0,
            "native generated custom mass qualification is incomplete")
    report = {
        "schema": "kit.sw2026.generated-custom-mass-typed-proof.v1", "passed": True,
        "packet_sha256": args.packet_sha256, "native_result_sha256": args.native_result_sha256,
        "cases": [inspect_case(root, case, native) for case in packet["cases"]],
        "full_corpus_acceptance": False, "heldout_inputs_read": 0, "public_writer_qualified": False,
    }
    require(len(report["cases"]) == 4, "exact four custom mass candidates are required")
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "states": 8, "result_sha256": digest(args.output.read_bytes())}))
