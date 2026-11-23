from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from itertools import chain
import json
from pathlib import Path
from subprocess import run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent.parent), str(HERE.parent)]

from AuditKeywordModels import SOURCE, compare_generated, digest, json_bytes, pinned_documents, recovered_documents, require
from ProjectAssemblyKeywords import project_index, read_index_graph
from ProjectPartDimensions import project_dimensions
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyDisplay import MakeKeyDisplay
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Metadata.ReadKeyIndex import ReadKeyIndex
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream


def model_source():
    construction = ROOT / "src/convert/adapters/solidworks/Archive/Construction"
    paths = (*sorted((construction / "Metadata").glob("*.py")),
             construction / "Assembly/Xml/MakeAsmKeyIndex.py",
             construction / "Assembly/Xml/MakeAsmKeys.py",
             construction / "NestedAssemblies/MakeNestedKeys.py",
             construction / "SketchDimensions/MakeSketchKeys.py",
             HERE.parent / "ProjectAssemblyKeywords.py",
             HERE.parent / "ProjectPartDimensions.py")
    return digest(json_bytes({str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths}))


def compare_assembly(archive):
    model, resolved, header, manager = read_index_graph(archive)
    projected, features, references = project_index(model, resolved, header, manager)
    cabinet = next(node for node in resolved if node.ClassValue.NameValue == "moDetailCabinet_c")
    environment = model.FieldsValue["f1e0"]
    attempts = (
        ("absent_environment_alias", model, tuple(node for node in resolved if node is not environment)),
        ("duplicate_annotation_owner", model, (*resolved, cabinet)),
        ("exploded_manager_published_twice", model, (*resolved, model.FieldsValue["f1590"])),
        ("disagreeing_active_config", replace(model, FieldsValue={**model.FieldsValue, "f08": 987}), resolved),
    )
    refusals = []
    for name, changed, roots in attempts:
        try:
            _ = project_index(changed, roots, header, manager)
        except (TypeError, ValueError):
            refusals.append(name)
            continue
        raise ValueError(f"unsupported assembly graph passed: {name}")
    require(projected == archive.require(KeywordsStream),
            "binary graph did not independently reproduce the saved assembly index")
    return {"features": features, "references": references, "bytes": len(projected),
            "keyword_sha256": digest(projected), "refusals": refusals}


def compare_dimensions(archive):
    modeled, ids = project_dimensions(archive)
    expected = ReadKeyIndex(archive.require(KeywordsStream))
    saved = {row.IdValue: row.DimensionValues for row in expected.FeatureValues
             if isinstance(row, KeywordFeature) and row.DimensionValues}
    by_name = lambda table: {key: tuple(sorted(rows, key=lambda row: row.NameValue)) for key, rows in table.items()}
    require(by_name(modeled) == by_name(saved), "saved keyword rows differ from their actual parameter owners")
    require(all(value == -1 for row in ids.values() for value in row),
            "dimension outside the measured unregistered parameter path")
    order_differences = {
        identity: {"modeled": [row.NameValue for row in rows],
                   "saved": [row.NameValue for row in saved[identity]]}
        for identity, rows in modeled.items() if rows != saved[identity]
    }
    roles = Counter("degree" if row.UnitValue == "degree" else row.PrefixValue or "length"
                    for rows in modeled.values() for row in rows)
    return {"roles": dict(roles), "unregistered_parameters": sum(roles.values()),
            "order_differences": order_differences, "has_exact_dimension_order": not order_differences}


def worker():
    request = json.load(sys.stdin)
    reads = []

    def guard(event, fields):
        if event == "open":
            reads.append(str(fields[0]))
            raise RuntimeError("model-only keyword construction attempted a file read")

    sys.addaudithook(guard)
    dimensions = tuple(MakeKeyDisplay(**item) for item in request["dimensions"])
    rows = (KeywordFeature(41, "Drawn section", "ProfileFeature", "Sketch", dimensions[:3], (), None, None),
            KeywordFeature(42, "Turned body", "Revolve", "Feature", dimensions[3:], (), None, None))
    data = MakeKeywords(request["title"], request["epoch"], (KeywordConfig(0, request["config"], None),),
                        rows)
    parsed = ReadKeyIndex(data)
    require(parsed.ToBytes() == data and not reads, "authored display index failed its process boundary")
    print(json.dumps({"sha256": digest(data), "xml": data[1:].decode("utf-8"),
                      "runtime_file_reads": len(reads), "bytes": len(data)}, sort_keys=True))


def authored_controls():
    base = {"title": "Midpoint contrast", "config": "Fresh document", "epoch": 1790000000}
    controls = (
        (3, ("41.125", "R12.625", "<MOD-DIAM>25.25", "90°")),
        (2, ("41.13", "R12.63", "<MOD-DIAM>25.25", "90°")),
    )
    results = []
    for precision, values in controls:
        dimensions = [
            {"NameValue": "D1" if units == "degree" else f"D{position}", "ParameterValue": number, "UnitValue": units,
             "DisplayPlaces": precision, "GlyphValue": glyph}
            for position, (number, units, glyph) in enumerate(
                ((.041125, "mm", None), (.012625, "mm", "radius"),
                 (.02525, "mm", "diameter"), (1.5707963267948966, "degree", None)), 1
            )
        ]
        command = (sys.executable, "-I", "-B", str(HERE), "--worker")
        result = run(command, input=json_bytes({**base, "dimensions": dimensions}),
                     check=False, capture_output=True, timeout=30)
        require(result.returncode == 0 and not result.stderr,
                result.stderr.decode(errors="replace")[-4000:])
        value = json.loads(result.stdout)
        actual = ReadKeyIndex(b"\x86" + value.pop("xml").encode("utf-8")).FeatureValues
        require(all(isinstance(row, KeywordFeature) for row in actual) and value["runtime_file_reads"] == 0,
                "independently authored display was not constructed")
        saved = tuple(dim for row in actual for dim in row.DimensionValues)
        for dim, literal in zip(saved, values, strict=True):
            numeric = f"{float(dim.NumberValue):.{dim.PlacesValue}f}"
            if dim.PrefixValue == "radius":
                numeric = "R" + numeric
            elif dim.PrefixValue == "diameter":
                numeric = "<MOD-DIAM>" + numeric
            if dim.UnitValue == "degree":
                numeric += "°"
            require(numeric == literal, "authored keyword presentation boundary differs")
        results.append({"precision": precision, "modeled_displays": values, **value})
    require(results[0]["bytes"] != results[1]["bytes"], "document precision did not change the stream length")
    return results


def main():
    if sys.argv[1:] == ["--worker"]:
        worker()
        return
    parser = ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("disclosures", type=Path)
    parser.add_argument("native_order_receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    native = args.native_order_receipt.read_bytes()
    native_result = json.loads(native)
    require(native_result["schema"] == "kit.sw2026.keyword-order-native.v1"
            and native_result["no_parameter_id_uses_display_pointer_low32"],
            "native order verification is missing")
    sources = model_source()
    counts = Counter()
    assemblies = {}
    ordering = {}
    inputs = sha256()
    for name, raw in chain(pinned_documents(SOURCE), recovered_documents()):
        archive = SldprtArchive.from_bytes(raw)
        require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
                "source is outside the measured 2026 profile")
        inputs.update(json_bytes((name, digest(raw))))
        if name.casefold().endswith(".sldasm"):
            assemblies[name] = compare_assembly(archive)
            continue
        evidence = compare_dimensions(archive)
        counts.update(evidence["roles"])
        counts.update(parts=1, exact_membership_parts=1,
                      exact_order_parts=int(evidence["has_exact_dimension_order"]),
                      unregistered_parameters=evidence["unregistered_parameters"])
        if not evidence["has_exact_dimension_order"]:
            ordering[name] = evidence["order_differences"]
    require((len(assemblies), counts["parts"], counts["unregistered_parameters"], len(ordering)) == (8, 203, 309, 7),
            "the measured keyword source cohort changed")
    controls = authored_controls()
    regression = compare_generated(args.baseline.resolve(), args.disclosures.resolve())
    require(sources == model_source(), "keyword projection code changed during the measurement")
    receipt = {"schema": "kit.sw2026.keyword-owner-projection.v1", "source_revision": SOURCE,
               "disclosed_input_identity_sha256": inputs.hexdigest(), "native_order_receipt_sha256": digest(native),
               "sources_sha256": sources, "script_sha256": digest(HERE.read_bytes()),
               "part_dimension_counts": dict(counts), "saved_dimension_order_variants": ordering,
               "assemblies": assemblies, "authored_display_controls": controls, "generated_regression": regression,
               "native_processes_started": 0, "heldout_inputs_read": 0}
    raw = json_bytes(receipt)
    with args.output.open("xb") as output:
        output.write(raw)
    print(json.dumps({"sha256": digest(raw), "assembly_streams_exact": len(assemblies),
                      "part_dimensions_independent": counts["unregistered_parameters"],
                      "part_order_variants": len(ordering),
                      "guarded_processes": len(controls) + regression["fresh_processes"]}, sort_keys=True))


if __name__ == "__main__":
    main()
