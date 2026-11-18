from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose, pi
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root / "src"), str(Path(__file__).parent)]

from AuditThroughAllDisclosed import graph, roundtrip
from convert import open_document
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.Selection import SelectPathElem

parser = ArgumentParser(description="Verify ordinary reads of generated selected-body cuts and reject physically malformed links")
parser.add_argument("--scope-root", type=Path, required=True)
parser.add_argument("--native-root", type=Path, required=True)
parser.add_argument("--saved-root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

scope = args.scope_root.resolve(strict=True)
native = args.native_root.resolve(strict=True)
source_proof = scope / "Process02/Result.json"
source_raw = source_proof.read_bytes()
assert sha256(source_raw).hexdigest() == "4156c18cb2c93ee9a8a2f4212cb8cc6ed5c32ae416186b6c2d14d02e2535cd53"
source = json.loads(source_raw)
assert source["passed"]
native_result = (native / "Inspection/Result.json").read_bytes()
assert sha256(native_result).hexdigest() == "f95b0c5e647d2312d483da7a0e95c4444d551705127ddea1978e9c6c405ceeeb"
trial = json.loads((native / "Trial02.json").read_bytes())
native_input = native / trial["generated_file"]


def check_selection(document, cut, evidence):
    stock_id = f'sldprt:feature:{evidence["producer_feature_id"]}'
    (selection,) = tuple(row for row in document.selections if row.id == cut.id + ":stock-body")
    assert stock_id in cut.input_feature_ids and selection.id in cut.selection_ids
    assert selection.path == (SelectPathElem("feature", stock_id, "body"),)
    return [[row.entity_kind, row.entity_id, row.subelement] for row in selection.path]

def inspect(path, axis, mode, depth, expected_volume):
    raw = path.read_bytes()
    archived, linked, _, _ = graph(raw)
    identical = roundtrip(archived, linked)
    results = []
    for input_value in (path, raw):
        doc = open_document(input_value, source_format="solidworks.sldprt")
        assert not doc.validate() and doc.brep is not None and not doc.brep_payloads
        (body,) = doc.bodies
        (cut,) = tuple(row for row in doc.feature_timeline if row.operation == "cut")
        definition = cut.definition
        assert type(definition) is ExtrudeFeature and definition.length is None
        assert definition.end_condition == ExtrudeEnd.KThroughAll and body.final_feature_id == cut.id
        assert definition.reversed == (mode != "reverse")
        assert definition.second_end_condition == (ExtrudeEnd.KThroughAll if mode == "both" else None)
        evidence = doc.metadata["solidworks.typed_resolved_semantics"]["cut_body_dependency"]
        assert evidence["binding"] == "cold_selected_stock_atom" and evidence["feature_scope_code"] == 1
        stock_path = check_selection(doc, cut, evidence)
        value = body.topology.volume
        assert value is not None and isclose(value, expected_volume, rel_tol=1e-10, abs_tol=1e-10)
        rims = sorted(getattr(curve.center, axis) for curve in doc.brep.curves if isinstance(curve, CircleCurve))
        expected_rims = {
            "forward": (0.0, depth / 2),
            "reverse": (-depth / 2, 0.0),
            "both": (-depth / 2, depth / 2),
        }[mode]
        assert all(isclose(value, target, rel_tol=0.0, abs_tol=1e-10) for value, target in zip(rims, expected_rims, strict=True))
        results.append({
            "native_body_scope": evidence["feature_scope_code"],
            "stock_atom": evidence["consumed_atom_id"],
            "portable_stock_path": stock_path,
            "volume_mm3": value,
            "rim_stations_mm": rims,
        })
    assert results[0] == results[1]
    return dict(results[0], sha256=sha256(raw).hexdigest(), exact_streams=len(identical), path_and_bytes_equal=True)

positives = []
for name in ("G01", "G02", "G03"):
    design = json.loads((scope / "Inputs" / (name + ".json")).read_bytes())
    width, height, depth = (value * 1000 for value in design["stock_size_m"])
    mode = design["direction"]
    radius = design["radius_m"] * 1000
    expected = width * height * depth - pi * radius * radius * depth / (1 if mode == "both" else 2)
    file = scope / "Process02/Generated" / (design["name"] + ".SLDPRT")
    positives.append(dict(inspect(file, design["axis"], mode, depth, expected), case=name))
    if name == "G01":
        assert native_input.read_bytes() == file.read_bytes()

saved = []
for directory, name, expected_sha in (
    ("GeneratedThroughAll02", "ThroughAllD01CutForward", "ced6b5c0e3ab5593c40ee776f50c68972c63b2599e49598be01d4786bffaa63d"),
    ("GeneratedThroughAllReverse01", "ThroughAllD02CutReverse", "e342763ba76cd09fc21a4f777127d0ff442b3c4b637acefecf1a974fbaf52431"),
    ("GeneratedThroughAllBoth01", "ThroughAllD03CutBoth", "cc4ec3d3d0d337186a83338eada5d16c73d041aec73962beb3ce0be852c19712"),
):
    path = args.saved_root / directory / "Control" / (name + ".SLDPRT")
    raw = path.read_bytes()
    assert sha256(raw).hexdigest() == expected_sha
    rows = []
    for input_value in (path, raw):
        doc = open_document(input_value, source_format="solidworks.sldprt", include_brep=False, include_tessellation=False)
        assert not doc.validate()
        evidence = doc.metadata["solidworks.typed_resolved_semantics"]["cut_body_dependency"]
        assert evidence["binding"] == "saved_configuration_atom_alias" and evidence["feature_scope_code"] == 1
        (cut,) = tuple(row for row in doc.feature_timeline if row.operation == "cut")
        assert cut.id == f'sldprt:feature:{evidence["consumer_feature_id"]}'
        stock_path = check_selection(doc, cut, evidence)
        rows.append({
            "cut_owner": cut.id,
            "portable_stock_path": stock_path,
            "stock_atom": evidence["consumed_atom_id"],
            "result_atom": evidence["result_atom_id"],
        })
    assert rows[0] == rows[1]
    saved.append(dict(rows[0], name=name, sha256=expected_sha, path_and_bytes_equal=True))


def malformed(payload, fault):
    archive, link, _, features = graph(payload)
    cut = features["ThroughFeature"]
    fields = cut.FieldsValue
    wrapper = fields["f548"]["items"][0]["o"].FieldsValue
    if fault == "wrong-selected-atom":
        wrapper["f18"] += 1
    elif fault == "wrong-base-feature":
        wrapper["f108"] = cut.FieldsValue["f08"]
    elif fault == "different-lineage":
        wrapper["f110"][0]["v"] += 1
    elif fault == "invented-topology-owner":
        wrapper["f100"] = 1
    elif fault == "scope-flag-disagrees":
        fields["f544"] = 0
    elif fault == "wrapper-missing":
        fields.update(has_f548=0, f548=None)
    elif fault == "precomputed-cut-output":
        boss = features["StockBoss"]
        fields.update(has_f528=1, f528=boss.FieldsValue["f528"])
    else:
        raise ValueError(fault)
    streams = dict(archive.streams)
    streams[link.StreamName], _ = WriteResolMut(
        link.ResolvedValue.RootsValue,
        link.ResolvedValue.ExtraFields,
        19000,
        link.ConfigValue.MapValue,
        link.ResolvedValue.ContextValue,
    )
    return BuildSldprt(streams, FormatVersion=4)

bad = []
for fault in (
    "wrong-selected-atom",
    "wrong-base-feature",
    "different-lineage",
    "invented-topology-owner",
    "scope-flag-disagrees",
    "wrapper-missing",
    "precomputed-cut-output",
):
    payload = malformed(native_input.read_bytes(), fault)
    try:
        open_document(payload, source_format="solidworks.sldprt")
    except ValueError as error:
        bad.append({"case": fault, "sha256": sha256(payload).hexdigest(), "error": str(error)})
    else:
        raise ValueError("malformed selected stock entered the reconstructed geometry route: " + fault)

report = {
    "schema": "kit.sw2026.cold-selected-stock-reader.v1",
    "passed": True,
    "data_source_sha256": sha256(source_raw).hexdigest(),
    "disclosed_native_result_sha256": sha256(native_result).hexdigest(),
    "path_and_bytes_reads": 2 * (len(positives) + len(saved)),
    "cold_geometry_reads": 2 * len(positives),
    "saved_semantic_reads": 2 * len(saved),
    "exact_critical_streams": sum(row["exact_streams"] for row in positives),
    "cold_generated_cases": positives,
    "saved_disclosed_cases": saved,
    "rejected_faults": bad,
    "heldout_payloads_read": 0,
}
with args.output.open("x") as output:
    json.dump(report, output, sort_keys=True, indent=2, allow_nan=False)
    output.write("\n")
print(json.dumps({
    "passed": True,
    "strict_positive_reads": report["path_and_bytes_reads"],
    "rejection_cases": len(bad),
    "result_sha256": sha256(args.output.read_bytes()).hexdigest(),
}))
