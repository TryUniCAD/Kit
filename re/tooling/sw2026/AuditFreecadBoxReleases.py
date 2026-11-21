from argparse import ArgumentParser
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from itertools import product
from math import isclose
from pathlib import Path
from subprocess import run
import json
import sys


RELEASES = ("0.21.2", "1.0.2", "1.1.4")
CASES = {f"recipe-{release}-F14{variant}" for release in RELEASES for variant in "abcd"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def hash_data(raw):
    return sha256(raw).hexdigest()


def guard(kit, request, path, rejection=None):
    worker = kit / "re/tooling/sw2026/SdkFreecadBoxProcess.py"
    process = run([sys.executable, "-I", "-B", str(worker), str(kit)], input=request,
                  capture_output=True, check=False, timeout=90)
    path.mkdir()
    (path / "Request.json").write_bytes(request)
    (path / "Process.stdout.json").write_bytes(process.stdout)
    (path / "Process.stderr.txt").write_bytes(process.stderr)
    error = process.stderr.decode(errors="replace")
    if rejection is not None:
        require(process.returncode != 0 and not process.stdout and rejection in error
                and "construction attempted runtime access" not in error, f"{path.name}: {error[-800:]}")
        return {"rejected": True, "diagnostic": error.splitlines()[-1], "request_sha256": hash_data(request)}
    require(process.returncode == 0 and not error, f"{path.name}: {error[-800:]}")
    result = json.loads(process.stdout)
    raw = b64decode(result.pop("blob"), validate=True)
    require(result["passed"] and result["runtime_input_file_reads"] == 0
            and len(raw) == result["bytes"] and hash_data(raw) == result["sha256"],
            "guarded box output changed")
    (path / "F14a.SLDPRT").write_bytes(raw)
    return result, raw


def read_box(raw, result, version):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    source = open_document(raw, source_format="solidworks.sldprt", include_tessellation=False)
    source.assert_valid()
    text = result["source_text"]
    require(source.metadata["custom_properties"] == text["file"] and source.metadata["document_summary"] == text["summary"],
            "normal SDK box read lost source text")
    require(source.configurations[0].name == "Default" and len(source.bodies) == 1
            and source.bodies[0].name == result["source_body_label"], "normal SDK box read lost its source owners")
    dimensions = {item.name: item.value.value for item in source.parameters}
    sizes = result["source_dimensions_mm"]
    require(dimensions == dict(zip(("Length", "Width", "Height"), sizes, strict=True)),
            "normal SDK box read lost the three authored lengths")
    model = source.brep
    actual = [(row.point.x, row.point.y, row.point.z) for row in model.vertices]
    expected = tuple(product(*((0.0, value) for value in sizes)))
    require(tuple(len(getattr(model, kind)) for kind in ("vertices", "edges", "faces", "shells", "bodies")) == (8, 12, 6, 1, 1)
            and all(sum(all(isclose(x, y, abs_tol=1e-9, rel_tol=1e-12) for x, y in zip(point, wanted, strict=True))
                        for point in actual) == 1 for wanted in expected), "normal SDK box read changed modeled geometry")
    storage = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(storage, 0)
    root = link.ConfigValue.RootValue
    users = {row["o"].ClassValue.NameValue: row["o"].FieldsValue for row in root.FieldsValue["f9b8"].FieldsValue["items"]}
    system, density = users["moUnitSysUnits_c"], users["moDensityUnits_c"]
    assigned = (system["fb0"], density["fc4"], density.get("fb8") is not None)
    require(assigned == ((4, 1, False) if version == "0.21.2" else (3, 2, True)),
            "FreeCAD box does not carry the correct document unit and mass owners")
    cfg, state = WriteConfigMut(root, 19000, link.ConfigValue.HeaderValue)
    resolved, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                19000, state.MapValue, link.ResolvedValue.ContextValue)
    require(cfg == storage.require(link.ConfigName) and resolved == storage.require(link.StreamName),
            "FreeCAD box did not preserve its exact complete linked streams")
    return {"dimensions_mm": dimensions, "literal_file_properties": len(text["file"]), "body_name": source.bodies[0].name,
            "archive_system_code": assigned[0], "archive_mass_code": assigned[1],
            "density_has_length_owner": assigned[2], "exact_linked_streams": 2}


def deliberate_refusals(kit, request, out):
    bad_units = deepcopy(request)
    node = next(row for row in bad_units["document"]["metadata"]["freecad"]["document_properties"]["children"]
                if row["attributes"]["name"] == "UnitSystem")
    node["children"][0]["attributes"]["value"] = "1"
    bad_material = deepcopy(request)
    feature = bad_material["document"]["feature_timeline"]["$tuple"][0]
    feature["definition"]["object_data"]["properties"]["ShapeMaterial"]["children"][0]["attributes"]["uuid"] = (
        "00000000-0000-0000-0000-000000000000"
    )
    offset_origin = deepcopy(request)
    point = next(row for row in offset_origin["document"]["metadata"]["freecad"]["objects"] if row["name"] == "Origin001")
    point["properties"]["Placement"]["children"][0]["attributes"]["Px"] = "1.0"
    live_hasher = deepcopy(request)
    live_hasher["document"]["metadata"]["freecad"]["string_hasher"]["entries"] = ["symbolic identifier"]
    cases = (
        ("unsupported-units", bad_units, "unqualified document unit"),
        ("unknown-material", bad_material, "unqualified material assignment"),
        ("nonorigin-point", offset_origin, "requires explicit support placement"),
        ("populated-string-map", live_hasher, "populated string map"),
    )
    return {name: guard(kit, json.dumps(doc, sort_keys=True, allow_nan=False).encode(), out / name, reason)
            for name, doc, reason in cases}


def main():
    parser = ArgumentParser(description="Build and verify exact disclosed FreeCAD schema-four origin box variants")
    parser.add_argument("kit", type=Path)
    parser.add_argument("observation", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--observation-sha256", required=True)
    args = parser.parse_args()
    raw = args.observation.read_bytes()
    require(hash_data(raw) == args.observation_sha256, "FreeCAD box source observation changed")
    observed = json.loads(raw)
    cases = observed["rows"]
    require(len(cases) == len(CASES) and {row["case"] for row in cases} == CASES
            and not observed["original_corpus_membership_verified"], "FreeCAD box source scope differs")
    kit = args.kit.resolve(strict=True)
    sys.path.insert(0, str(kit / "src"))
    args.output.mkdir(exist_ok=False)
    root = args.observation.parent
    result = {"schema": "kit.sw2026.freecad-box-release-construction.v1", "passed": False,
              "source_observation_sha256": args.observation_sha256, "builds": {}, "negative": {},
              "native_acceptance": False, "original_corpus_conversions": 0, "heldout_inputs_read": 0}
    for row in cases:
        name = row["case"]
        request = (root / "Neutral" / (name + ".json")).read_bytes()
        require(hash_data(request) == row["strict_request_sha256"], "FreeCAD box neutral request differs")
        data = json.loads(request)
        require(data["document"]["source"]["sha256"] == row["sha256"], "FreeCAD box neutral source identity differs")
        if not name.endswith("F14a"):
            reason = ("uses another attachment engine" if name.endswith("F14c") else "includes another authored model domain")
            result["negative"][name] = guard(kit, request, args.output / name, reason)
            continue
        built, generated = guard(kit, request, args.output / name)
        version = name.split("-")[1]
        proof = read_box(generated, built, version)
        trimmed = deepcopy(data)
        trimmed["document"]["brep"] = None
        trimmed["document"]["brep_payloads"] = {"$tuple": []}
        cold, cache_free = guard(kit, json.dumps(trimmed, ensure_ascii=False, sort_keys=True, allow_nan=False).encode(),
                                 args.output / (name + "-no-source-cache"))
        require(cache_free == generated and not cold["geometry"]["source_cache_compared"], "FreeCAD source cache changed output")
        result["builds"][name] = {"generated": built, "normal_sdk_readback": proof, "without_source_cache_sha256": cold["sha256"]}
        if version == "1.1.4":
            result["negative"].update(deliberate_refusals(kit, data, args.output))
    result["guarded_workers"] = 2 * len(result["builds"]) + len(result["negative"])
    result["passed"] = len(result["builds"]) == 3 and len(result["negative"]) == 13
    target = args.output / "Result.json"
    target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "workers": result["guarded_workers"], "sha256": hash_data(target.read_bytes())}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
