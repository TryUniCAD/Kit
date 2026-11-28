from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys


ROOT = Path(__file__).resolve().parents[4]
BASELINE = "138d0f987568dc4c52be1bd3a1b29becbc1ec939"
MANIFEST = "e2053d84764ed9b65fc4bfe62f98b08c4d33bb57f096f3a4e9265e802e9288fa"
LINEAGE = "ff4edb3b60ebc6d76714f14c56210acc7be2dd5fc9025042e5c2f6bf80bd6266"
PERSISTENCE = "85da449d283872dc47e76782268fd0c366ea4f1a190a9c8b6aad123f2619dced"
POSITIVE = {"recipe-1.0.2-F14a": "Freecad102", "recipe-1.1.4-F14a": "Freecad114"}
NEGATIVE = {"recipe-1.0.2-F14c": ("40a68d097af87a4ca192fe8d0caa227e236547cc1a5e8b95ddba1037eb8dca70", "alternate attachment or placement"),
            "recipe-0.21.2-F14a": ("2f0e5e20da3e8f6d2073a7c8dd654b0c5035ed142c2e0392a14de832cd82eb5d", "unsupported FreeCAD origin box source schema or release")}
COUNTS = {"edge": 12, "face": 6, "vertex": 8}


def pinned(path, digest):
    if not path.is_file() or path.is_symlink():
        raise ValueError("expected the exact disclosed regular input")
    value = path.read_bytes()
    if sha256(value).hexdigest() != digest:
        raise ValueError("disclosed input digest changed")
    return value


def symbolic_contrast(payload):
    from convert.adapters.freecad.BodyLineage.BoxOccurrences import ReadBoxOrder
    from convert.adapters.freecad.EditShape.Prism.PrismRaw import ReadPrismRaw
    from convert.Geometry.Opencascade import KIdentityLocation

    raw = ReadPrismRaw(payload.data, 4, True)
    shared = Counter(ref.RecordA for row in raw.Records.values() for ref in row.Children)
    parent, old, ref = next((index, row, ref) for index, row in raw.Records.items()
                            for ref in row.Children if ref.KLocation == 0 and shared[ref.RecordA] > 1)
    assert raw.Matrix(raw.Chains[1]) == KIdentityLocation
    alternate = replace(old, Children=tuple(replace(item, KLocation=1) if item is ref else item for item in old.Children))
    changed = replace(raw, Records=raw.Records | {parent: alternate})
    refused(ReadBoxOrder, changed, "alternate symbolic occurrence paths")
    return "alternate symbolic occurrence paths with an identical placement matrix"


def refused(operation, value, diagnostic):
    try:
        operation(value)
    except ValueError as error:
        if diagnostic in str(error):
            return diagnostic
        raise
    raise ValueError("the expected owner refusal did not occur")


def negative_map(document, owner):
    from convert.adapters.freecad.BodyLineage.CheckBoxMap import CheckBoxMap
    from convert.adapters.freecad.BodyLineage.ReadBoxLineage import ReadBoxLineage

    payloads = document.brep_payloads
    index, = (index for index, item in enumerate(payloads) if item.id == owner.BodyShapeId)
    original = payloads[index]
    attributes = dict(original.attributes)
    sidecar, = attributes.pop("freecad_sidecars")
    modified = replace(original, attributes=attributes)
    changed = replace(document, brep_payloads=payloads[:index] + (modified,) + payloads[index + 1:])
    rejected = refused(ReadBoxLineage, changed, "no exact retained map sidecar")
    try:
        CheckBoxMap(sidecar["data"], owner.ChildXmlId + 1, COUNTS)
    except ValueError as error:
        assert "child range disagrees" in str(error)
    else:
        raise ValueError("the source map was accepted for another actual child id")
    return {"missing_retained_sidecar": rejected, "different_child_xml_id": "child range disagrees",
            "alternate_symbolic_occurrence": symbolic_contrast(original)}


def compare_roles(owner, old):
    prior = old["source"]
    assert (owner.SourceSha256, owner.DocumentUuid, owner.BodyXmlId, owner.ChildXmlId, owner.MapSha256) == (
        prior["original_sha256"], prior["source_uuid"], prior["body_xml_id"], prior["primitive_xml_id"], prior["source_element_map_sha256"])
    original = {(row["kind"], row["role"]): row for row in old["entity_rows"]}
    observed = {(row.KindValue, row.BoundaryRole): row for row in owner.Elements}
    assert original.keys() == observed.keys() and len(observed) == len(owner.Elements) == 26
    for key, typed in observed.items():
        row = original[key]
        assert (typed.BodyOrdinal, typed.ChildOrdinal, typed.EntityId) == (
            row["source_body"]["ordinal"], row["source_primitive"]["ordinal"], row["source_body"]["neutral_entity_id"])


def inspect_source(request):
    sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent.parent)]
    from convert import open_document
    from convert.adapters.freecad.BodyLineage.ReadBoxLineage import ReadBoxLineage
    from VerifyFreecadF14aIntact import no_runtime_io, normal_write_boundaries, wire

    source = Path(request["path"])
    raw = pinned(source, request["sha256"])
    document = open_document(source, strict=True, include_brep=True, include_tessellation=True)
    document.assert_valid()
    assert document.source.sha256 == request["sha256"] and document.brep is not None
    if "refusal" in request:
        with no_runtime_io():
            diagnostic = refused(ReadBoxLineage, document, request["refusal"])
        result = {"strict_open_passed": True, "source_sha256": request["sha256"], "refusal": diagnostic}
        if "same_map" in request:
            sidecar, = next(item for item in document.brep_payloads if item.id == "freecad:brep:Body:Shape").attributes["freecad_sidecars"]
            assert sidecar["source_stream"] == "Body.Shape.Map.txt" and sha256(sidecar["data"]).hexdigest() == request["same_map"]
            result["same_body_map_sha256_as_positive"] = request["same_map"]
        return result
    for encoding in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(encoding)
    before = document.to_dict()
    roundtrip = type(document).from_json(document.to_json(indent=None))
    assert roundtrip.to_dict() == before
    with no_runtime_io():
        owner = ReadBoxLineage(document)
        assert owner == ReadBoxLineage(roundtrip)
    compare_roles(owner, request["lineage"])
    controls = negative_map(document, owner)
    with TemporaryDirectory(prefix="kit-f14a-owner-refusal-") as temporary:
        boundary = normal_write_boundaries(document, source, Path(temporary) / "F14a.SLDPRT")
    assert document.to_dict() == before and pinned(source, request["sha256"]) == raw
    references = {"body_shape_id": owner.BodyShapeId, "primitive_shape_id": owner.ChildShapeId,
                  "body_id": owner.BodyId, "primitive_feature_id": owner.ProducerId}
    return {"source_sha256": owner.SourceSha256, "source_document_uuid": owner.DocumentUuid, "body_xml_id": owner.BodyXmlId,
            "primitive_xml_id": owner.ChildXmlId, "element_map_sha256": owner.MapSha256, "owner_sha256": sha256(wire(asdict(owner))).hexdigest(),
            "role_counts": Counter(row.KindValue for row in owner.Elements), "source_owners": references, "contrasts": controls,
            "typed_owner_rederived_from_existing_json": True, "strict_input_unchanged": True, "runtime_inputs_read": 0,
            "pre_staging_writer_refusals": sorted(boundary["writer_refusals"]), "missing_writer_capabilities": boundary["unsupported_capabilities"],
            "staged_files": boundary["path_output_files"], "stream_unchanged": boundary["stream_unchanged"]}


def main(manifest_path):
    inputs = json.loads(pinned(manifest_path, MANIFEST))
    receipts = ROOT / "re/solidworks/measurements/2026"
    lineage = json.loads(pinned(receipts / "SdkFreecadF14aTopologyLineage01.json", LINEAGE))
    native = json.loads(pinned(receipts / "F14aLiveReferencePersistence01.json", PERSISTENCE))
    assert inputs["heldout_inputs"] == 0 and native["downstream_live_persistence_passed"] and not native["source_reference_transfer_qualified"]
    outputs = {}
    workers = 0
    for name in (*POSITIVE, *NEGATIVE):
        row, = (entry for entry in inputs["inputs"] if entry["case"] == name)
        request = dict(row)
        if name in POSITIVE:
            identity = POSITIVE[name]
            source = lineage["cases"][identity]
            assert row["sha256"] == source["source"]["original_sha256"] == native["cases"][identity]["original_fcstd_sha256"]
            request["lineage"] = source
        else:
            wanted, request["refusal"] = NEGATIVE[name]
            assert row["sha256"] == wanted
            if name == "recipe-1.0.2-F14c":
                request["same_map"] = lineage["cases"]["Freecad102"]["source"]["source_element_map_sha256"]
        runs = []
        for _ in range(2 if name in POSITIVE else 1):
            outcome = run((sys.executable, "-I", "-B", __file__, "--worker"), input=json.dumps(request),
                          capture_output=True, text=True, check=True, timeout=90)
            assert not outcome.stderr
            runs.append(json.loads(outcome.stdout))
            workers += 1
        assert runs == [runs[0]] * len(runs)
        outputs[name] = runs[0]
    package = ROOT / "src/convert/adapters/freecad/BodyLineage"
    freecad = ROOT / "src/convert/adapters/freecad"
    prism = freecad / "EditShape/Prism"
    dependencies = [*sorted(package.glob("*.py")), freecad / "Native.py", freecad / "EditShape/PrismShape.py",
                    *(prism / name for name in ("PrismRaw.py", "PrismProof.py", "PrismFaces.py", "PrismExpected.py", "PrismTrim.py")),
                    ROOT / "src/convert/Geometry/Opencascade.py", ROOT / "src/interchange/document/Models/DocumentPayload.py",
                    ROOT / "re/tooling/sw2026/VerifyFreecadF14aIntact.py", Path(__file__).resolve()]
    return {"schema": "kit.sw2026.freecad-f14a-typed-source-owner.v1", "baseline_revision": BASELINE,
            "source_manifest_sha256": MANIFEST, "previous_lineage_sha256": LINEAGE, "previous_native_persistence_sha256": PERSISTENCE,
            "tool_dependencies_sha256": {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in dependencies},
            "cases": outputs, "independent_sdk_processes": workers, "native_processes_started": 0, "generated_outputs": 0,
            "heldout_inputs_read": 0, "source_reference_transfer_qualified": False, "public_writer_qualified": False,
            "corpus_conversions_counted": 0}


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(inspect_source(json.load(sys.stdin)), sort_keys=True))
    else:
        parser = ArgumentParser(description="Audit the actual typed FreeCAD origin box element-map owners")
        parser.add_argument("manifest", type=Path)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args()
        result = main(args.manifest)
        data = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
        with args.output.open("xb") as stream:
            stream.write(data)
        print(json.dumps({"receipt_sha256": sha256(data).hexdigest(), "independent_sdk_processes": result["independent_sdk_processes"]}))
