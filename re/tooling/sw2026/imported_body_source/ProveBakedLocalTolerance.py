from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from math import isfinite
from pathlib import Path
import sys

from AuditBakedFcstdSources import boundary_summary, physical_owner
from BuildBakedLabelPair import checked, computed_box, construction_guard, require


OWNERS_SHA256 = "76471602145cacdac72876f471b00d74cf41397df85ed946e5a719d62afaeb1e"
MEASUREMENTS = "re/solidworks/measurements/2026"
FIXTURES = ("Baked01.FCStd", "Baked02.FCStd", "ParametricControl.FCStd")
KIND_OWNERS = {14: "faces", 16: "edges", 18: "vertices"}


def ring_signature(rings):
    result = []
    for ring in rings:
        positions = tuple((point.x, point.y, point.z) for point in ring)
        start = positions.index(min(positions))
        result.append(positions[start:] + positions[:start])
    return sorted(result)


def import_scope(document, evidence):
    (feature,) = document.feature_timeline
    (body,) = document.bodies
    (configuration,) = document.configurations
    require(feature.kind.value == "imported" and feature.definition.type_id == "Part::Feature"
            and evidence["standalone_baked"], "source is not an independently baked feature")
    require(body.final_feature_id == feature.id and not feature.input_feature_ids and configuration.active,
            "source feature does not own its sole final body")
    require(document.brep is not None and document.validate() == (),
            "source does not have a complete typed boundary")
    physical = boundary_summary(document.brep, body.id)
    source_shape = next(payload for payload in document.brep_payloads if payload.role.value == "brep")
    require(sha256(source_shape.data).hexdigest() == evidence["shape_sha256"],
            "neutral boundary does not bind the source Shape")
    return physical, configuration.name


def transmit_pair(document, evidence):
    from convert.Geometry.Parasolid import KMissingParam
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import MakeLocalPrism
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import KMillimetersPerMeter
    from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalXmt import EncodeLocalXmt
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes

    source, configuration = import_scope(document, evidence)
    tolerance_sets = tuple(source["tolerances_mm"].values())
    require(all(len(row) == 1 for row in tolerance_sets), "varied local tolerances are outside the measured scope")
    source_values = {row[0] for row in tolerance_sets}
    require(len(source_values) == 1, "nonuniform face, edge and vertex tolerances")
    (tolerance,) = source_values
    require(isfinite(tolerance) and tolerance > 0, "missing positive local tolerance")
    meters = tolerance / KMillimetersPerMeter
    with construction_guard():
        candidate = computed_box(source["bounds_mm"], configuration)
        nodes = MakeLocalPrism(candidate.brep)
        require(ring_signature(ReadMassRings(document.brep)) == ring_signature(ReadMassRings(candidate.brep)),
                "normalized rings do not preserve source orientation and incidences")
        bound = []
        for node in nodes:
            if node.KindValue in KIND_OWNERS:
                require(node.FieldsValue["tolerance"] == KMissingParam,
                        "generated box already carries an assigned tolerance")
                fields = dict(node.FieldsValue, tolerance=meters)
                bound.append(replace(node, FieldsValue=fields))
            else:
                bound.append(node)
        base = EncodeLocalXmt(nodes)
        value = EncodeLocalXmt(tuple(bound))
        actual, _ = ReadLocalNodes(value)
        original, _ = ReadLocalNodes(base)
        counts = Counter()
        for index, saved in actual.items():
            previous = original[index]
            row = KIND_OWNERS.get(saved.KindValue)
            if row is None:
                require(saved == previous, "local tolerance changed a non-tolerance record")
                continue
            require(saved.FieldsValue["tolerance"] == meters
                    and dict(saved.FieldsValue, tolerance=KMissingParam) == previous.FieldsValue,
                    "local tolerance changed a separate field")
            counts[row] += 1
        require(dict(counts) == {"faces": 6, "edges": 12, "vertices": 8},
                "unrepresented topology tolerance owner")
        require(value != base and EncodeLocalXmt(tuple(actual.values())) == value,
                "typed tolerance transmit cannot be reproduced")
    return {"source_shape_sha256": evidence["shape_sha256"], "source_tolerance_mm": tolerance,
            "encoded_tolerance_m": meters, "owners": dict(counts), "oriented_faces": 6,
            "untoleranced_transmit_sha256": sha256(base).hexdigest(),
            "tolerance_transmit_sha256": sha256(value).hexdigest(), "tolerance_transmit_bytes": len(value),
            "other_node_fields_identical": True, "typed_replay_exact": True}


def measure(root, sources):
    sys.path.insert(0, str(root / "src"))
    from convert import open_document

    owner_path = root / MEASUREMENTS / "DisclosedBakedFcstdOwners01.json"
    owner_raw = checked(owner_path, OWNERS_SHA256)
    evidence = json.loads(owner_raw)["cases"]
    rows = {}
    for name in FIXTURES:
        expected = evidence[name]["source_lock"]
        path = sources / name
        owner = physical_owner(path, expected)
        require(json.loads(json.dumps(owner)) == evidence[name]["physical_owners"],
                "source's physical ownership differs")
        raw = checked(path, expected["file_sha256"])
        document = open_document(BytesIO(raw), source_format="freecad.fcstd", strict=True)
        if expected["standalone_baked"]:
            rows[name] = transmit_pair(document, expected)
        else:
            try:
                import_scope(document, expected)
            except ValueError as issue:
                require(str(issue) == "source is not an independently baked feature",
                        "parametric control refused at the wrong boundary")
            else:
                raise ValueError("parametric control entered the baked body projection")
    require(len(rows) == 2, "expected two independently authored baked sources")
    return {"schema": "kit.sw2026.disclosed-baked-local-tolerance.v1",
            "source_owner_audit_sha256": sha256(owner_raw).hexdigest(),
            "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "sources": rows, "guarded_runtime_accesses": 0,
            "live_parametric_control_refused": True, "native_processes": 0,
            "part_outputs": 0, "whole_source_qualified": False}


def main():
    parser = ArgumentParser()
    parser.add_argument("sources", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    report = measure(root, args.sources.resolve(strict=True))
    data = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as output:
        output.write(data)
    print(sha256(data).hexdigest())


if __name__ == "__main__":
    main()
