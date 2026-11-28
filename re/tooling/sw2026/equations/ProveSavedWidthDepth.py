from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src")]

from ProveLocalWidthDepthRead import parameters, require
from ProveWidthDepthGeometry import measure


BASE = "d3f98794746cb3e63b9db4710e08399312daf4ee"
NATIVE = "re/solidworks/measurements/2026/SdkWidthDepthPreparationNative01.json"
NATIVE_SHA = "f40bc2433d54bcb8c3ae5165b3a3965ebae4876c71cf52293ad4a045af85b420"
FORMAT = "solidworks.sldprt"
CONFIG = "modeled default"
PARTITION = "Contents/Config-0-Partition"
BODY_PROOF = "solidworks.native_body_names"
RELATION_PROOF = "solidworks.typed_resolved_semantics"
CONTROL_MODES = {
    "cold_reference": (
        "33fd6f933c21ac8114d0c50feb0cc562a1e42a28a67fee74679c05aeef58a1f5",
        "7c193c52f92f4203e32c9e396c6c4ef1ac8924d47934454ccd1522e29be11e2b",
    ),
    "cold_plain": (
        "6f0ff8fdf5f8da7444ea804d98dfa308577038cd8e85464da03a7a62c80f9841",
        "c5d1653363741c9a0a935652ba56587930d8f58187c0fef12b9cd4208d013314",
    ),
    "saved_plain": (
        "3b6884b4d69c4c2d8c847d8b6c301efb30eff3a1987c74f7985dd75a6bb0541e",
        "16b030cd437ca011539918f05654e8ff1df3e29f6b2b052c0e651b6c6e012afe",
    ),
}
CASES = {
    "cold_reference": ("Frozen/Reference.SLDPRT", "Reference", "generated_sha256", (39.125, 17.375, 19.5625)),
    "cold_plain": ("Frozen/Plain.SLDPRT", "Plain", "generated_sha256", (39.125, 17.375, 19.5625)),
    "saved_plain": ("Inspection/PlainEdit/Edited.SLDPRT", "Plain", "saved_sha256", (47.875, 17.375, 19.5625)),
    "saved_reference": ("Inspection/ReferenceEdit/Edited.SLDPRT", "Reference", "saved_sha256", (47.875, 17.375, 23.9375)),
}


def digest(value):
    return sha256(value).hexdigest()


def native_receipt():
    raw = (ROOT / NATIVE).read_bytes()
    require(digest(raw) == NATIVE_SHA, "the previous native receipt differs")
    receipt = json.loads(raw)
    require(receipt["controls_healthy"] and receipt["distinct_native_processes"] == 6
            and receipt["oracle_identity"]["file_version"] == "34.5.2.0604",
            "native build or bracket controls differ")
    for name, expected_rows in (("Plain", 0), ("Reference", 1)):
        row = receipt["cases"][name]
        require(row["open_errors_and_warnings"] == row["fresh_reopen_errors_and_warnings"] == [0, 0]
                and len(row["real_equation_rows"]) == expected_rows, "measured native comparison differs")
    return receipt


def public_modes(raw, label):
    from convert import open_document

    full = open_document(raw, source_format=FORMAT)
    design = open_document(raw, source_format=FORMAT, include_brep=False)
    require(full.source.sha256 == design.source.sha256 == digest(raw), "source identity was lost")
    require(full.configurations == design.configurations
            and len(full.configurations) == 1 and full.configurations[0].name == CONFIG,
            "active configuration differs across read modes")
    if label == "saved_reference":
        require(full.parameters == design.parameters and full.sketches == design.sketches
                and full.feature_timeline == design.feature_timeline and len(full.feature_timeline) == 19,
                "saved equation history differs across read modes")
    related = label.endswith("reference")
    for doc in (full, design):
        parameters(
            doc, (18, 21), CASES[label][3], "derived" if related else "driving",
            ("sldprt:parameter:18:D1",) if related else (), '"D1@Sketch1" / 2' if related else None,
        )
    require(design.brep is None and not design.brep_payloads, "design-only read exposed B-rep")
    return full, design


def saved_body(full, design, raw):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyKernel import ReadBodyKernel
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import ReadMgrAtom

    archive = SldprtArchive.from_bytes(raw)
    partition = archive.require(PARTITION)
    payloads, nodes, marks = ReadBodyKernel(partition, PARTITION)
    proof = full.metadata[BODY_PROOF]
    relation = NativePartModel(archive, CONFIG).WidthDepth
    atom = ReadMgrAtom(relation.LinkValue)
    require(atom.IndexValue == 58 and atom.FieldsValue["f180"] == atom.FieldsValue["f1b0"] == 1422,
            "physical atom slot or paired body stamps differ")
    require((len(nodes), marks, proof["body_transmit_index"], proof["atom_manager_id"],
             proof["body_match_tag"], proof["last_modifying_feature_id"])
            == (177, (8, 2), 2, 101, 1422, 21), "actual cache owner or history marks changed")
    require(len(full.brep_payloads) == 3 and full.brep.bodies[0].design_body_id == full.bodies[0].id,
            "public geometry did not bind to its actual history body")
    require(tuple(p.sha256 for p in full.brep_payloads if p.source_stream == PARTITION)
            == tuple(p.sha256 for p in payloads), "public B-rep payloads differ from active storage")
    require(design.metadata[BODY_PROOF] == {**proof, "complete_brep_binding": False}
            and full.bodies[0].attributes["solidworks.native_body"] == proof
            and design.bodies[0].attributes["solidworks.native_body"] == design.metadata[BODY_PROOF],
            "design-only body proof lost selected ownership")
    for doc in (full, design):
        (body,) = doc.bodies
        require(body.name == "Boss-Extrude1" and body.final_feature_id == "sldprt:feature:21"
                and body.attributes["native_object_id"] == 21
                and body.provenance.native_id == f"{PARTITION}:body:2",
                "actual body name or producer differs")
        require([(span.stream, span.offset, span.length) for span in body.provenance.spans]
                == [("Contents/Config-0", 3096, 100), (PARTITION, 0, len(partition))],
                "physical producer spans differ")
    require(not design.bodies[0].attributes["parasolid_payload_ids"]
            and "parasolid_active_payload_id" not in design.bodies[0].attributes,
            "design-only read retained dangling payload links")
    reversed_faces = sum(not face.same_sense for face in full.brep.faces)
    require(reversed_faces == 5, "the observed saved plane senses changed")
    return {"nodes": len(nodes), "marks": marks, "bytes": len(partition),
            "native_atom_slot": atom.IndexValue, "native_atom_span": [3096, 3196],
            "reversed_plane_carriers": reversed_faces, "stream_sha256": digest(partition),
            "active_transmit_sha256": payloads[0].sha256, "proof": dict(proof)}


def geometry_evidence(full, design):
    metrics = measure(full, CASES["saved_reference"][3])
    for body in (full.bodies[0], design.bodies[0]):
        topology = body.topology
        require(topology.valid and (topology.solid_count, topology.shell_count, topology.face_count,
                                   topology.edge_count, topology.vertex_count) == (1, 1, 6, 12, 8)
                and topology.volume == metrics["volume_mm3"]
                and topology.surface_area == metrics["area_mm2"]
                and body.attributes["solidworks.body_centroid_mm"] == metrics["centre_mm"],
                "body counts or measures differ from the complete physical solid")
    require(full.bodies[0].topology == design.bodies[0].topology, "topology differs by mode")
    return metrics


def saved_history(full):
    proof = full.metadata[RELATION_PROOF]["local_width_depth_equation"]
    require(proof["relation"]["object_index"] == 62
            and tuple(proof[key]["live_handle"]["object_index"] for key in ("dependency", "target"))
            == (128, 313), "live relation storage or handle owner differs")
    require((full.metadata["solidworks.typed_configuration_graph"]["map_counter"],
             full.metadata[RELATION_PROOF]["map_counter"]) == (198, 338), "linked map counters differ")
    return proof


def digest_modes(full, design):
    return tuple(digest(doc.ToJson(IndentSize=None).encode("utf-8")) for doc in (full, design))


def positive(label, raw):
    full, design = public_modes(raw, label)
    result = {"sha256": digest(raw), "neutral_json_mode_sha256": digest_modes(full, design),
              "dimensions_mm": CASES[label][3],
              "history_rows_by_mode": (len(full.feature_timeline), len(design.feature_timeline)),
              "native_payloads_by_mode": (len(full.brep_payloads), len(design.brep_payloads))}
    if label in CONTROL_MODES:
        require(result["neutral_json_mode_sha256"] == CONTROL_MODES[label], "ordinary control projection changed")
        return result
    result["active_body"] = saved_body(full, design, raw)
    result["physical_geometry"] = geometry_evidence(full, design)
    result["typed_relation"] = saved_history(full)
    return result


def mismatched_cache(reference, plain):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat

    reference_archive, plain_archive = map(SldprtArchive.from_bytes, (reference, plain))
    streams = {**reference_archive.streams, PARTITION: plain_archive.require(PARTITION)}
    require(reference_archive.require(PARTITION) != streams[PARTITION],
            "the independent saved control has an identical cache")
    contrast = BuildSldprt(streams, FormatVersion=reference_archive.format_version)
    require(SldprtArchive.from_bytes(contrast).streams == streams, "isolated cache contrast changed other streams")
    refusals = []
    for include in (True, False):
        try:
            open_document(contrast, source_format=FORMAT, include_brep=include)
        except SldprtFormat as error:
            require(str(error).endswith("saved width-depth boundary differs from its live dimensions"),
                    "wrong strict cache refusal")
            refusals.append(str(error))
        else:
            raise ValueError("strict SDK accepted the independent mismatched result")
        partial = open_document(contrast, source_format=FORMAT, include_brep=include, strict=False)
        require(partial.brep is None and BODY_PROOF not in partial.metadata
                and any(diag.code == "sldprt.width_depth_body_unresolved" for diag in partial.diagnostics),
                "permissive read exposed an unbound result")
    return {"partition_sha256": digest(streams[PARTITION]), "strict_refusal_by_mode": refusals,
            "permissive_omits_unbound_body_geometry": True}


def mismatched_creator(reference):
    from convert import open_document
    from convert.Geometry.Parasolid import DecodeBrepModel
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadSavedEq import ReadSavedEq

    full = open_document(reference, source_format=FORMAT)
    payload = next(p for p in full.brep_payloads if p.source_stream == PARTITION and p.kind == "partition")
    document = replace(full, brep=DecodeBrepModel(payload.data))
    archive = SldprtArchive.from_bytes(reference)
    model = NativePartModel(archive, CONFIG)
    relation = model.WidthDepth
    require(relation is not None and relation.WidthFeature != relation.DepthFeature,
            "actual distinct sketch and boss owners were lost")
    crossed = replace(model, WidthDepth=replace(relation, DepthFeature=relation.WidthFeature))
    refusals = []
    for include in (True, False):
        try:
            ReadSavedEq(document, archive, crossed, ReadOptions(include_brep=include))
        except SldprtFormat as error:
            require(str(error).endswith("saved width-depth equation targets a different body creator"),
                    "wrong crossed owner refusal")
            refusals.append(str(error))
        else:
            raise ValueError("typed read accepted the actual sketch as body creator")
    return {"actual_owner": relation.DepthFeature, "crossed_owner": relation.WidthFeature,
            "strict_refusal_by_mode": refusals}


def separate_worker(case, payload, cutoff):
    args = [sys.executable, "-I", "-B", str(HERE), "--worker", case, "--cutoff", str(cutoff)]
    process = subprocess.run(args, input=payload, capture_output=True, timeout=60, check=False)
    require(process.returncode == 0, process.stderr.decode(errors="replace"))
    result = json.loads(process.stdout)
    require(result["worker_cad_file_opens"] == 0, "worker attempted to reopen source CAD")
    return result


def compare_native(metrics, measured):
    native = measured["edited_mass_properties_si"]
    pairs = [(metrics["volume_mm3"], native["volume"] * 1e9),
             (metrics["area_mm2"], native["area"] * 1e6),
             *zip(metrics["centre_mm"], (value * 1000 for value in native["com"]), strict=True)]
    require(all(format(actual, ".6g") == format(expected, ".6g") for actual, expected in pairs),
            "saved body does not match independent native volume, area and centroid")
    return len(pairs)


def run(packet_root):
    receipt = native_receipt()
    inputs = {}
    for label, (relative, lane, field, _) in CASES.items():
        pinned = receipt["cases"][lane][field]
        inputs[label] = (packet_root / relative).read_bytes()
        require(digest(inputs[label]) == pinned, f"disclosed source identity differs: {label}")
    rows = {label: separate_worker(label, raw, 0) for label, raw in inputs.items()}
    reference, plain = inputs["saved_reference"], inputs["saved_plain"]
    contrast = separate_worker("contrast", reference + plain, len(reference))
    comparisons = compare_native(rows["saved_reference"]["physical_geometry"], receipt["cases"]["Reference"])
    for label, (relative, _, _, _) in CASES.items():
        require((packet_root / relative).read_bytes() == inputs[label], "an immutable disclosed file changed")
    return {"schema": "kit.sw2026.saved-width-depth-body.v1", "baseline_revision": BASE,
            "previous_native_receipt_sha256": NATIVE_SHA, "native_build": "34.5.2.0604",
            "prior_distinct_native_processes": 6, "prior_controls_healthy": True,
            "native_measure_comparisons": comparisons, "new_native_launches": 0, "heldout_input_reads": 0,
            "cases": rows, "contrasts": contrast}


def main():
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--worker", choices=(*CASES, "contrast"))
    parser.add_argument("--cutoff", type=int, default=0)
    args = parser.parse_args()
    if args.worker:
        raw = sys.stdin.buffer.read()
        source_opens = []

        def protect_source(event, values):
            if event == "open" and isinstance(values[0], (str, bytes)):
                name = str(values[0], "utf-8", "replace") if isinstance(values[0], bytes) else values[0]
                if name.lower().endswith((".sldprt", ".sldasm", ".fcstd", ".x_b")):
                    source_opens.append(name)
                    raise ValueError("the offline worker requires CAD bytes through stdin")
        sys.addaudithook(protect_source)
        result = ({"foreign_cached_boundary": mismatched_cache(raw[:args.cutoff], raw[args.cutoff:]),
                   "crossed_creator": mismatched_creator(raw[:args.cutoff])}
                  if args.worker == "contrast" else positive(args.worker, raw))
        result["worker_cad_file_opens"] = len(source_opens)
    else:
        require(args.packet is not None, "the disclosed packet root is required")
        result = run(args.packet)
    print(json.dumps(result, sort_keys=True, indent=2, default=dict, allow_nan=False))


if __name__ == "__main__":
    main()
