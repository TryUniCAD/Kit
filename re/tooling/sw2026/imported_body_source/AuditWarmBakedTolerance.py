from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
import json
from math import isclose
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from BuildBakedTolerancePart import CASES, ROOT, SDK_TREE, artifact, checked, encode, git, model_only, require, verify
from ProveBakedLocalTolerance import KIND_OWNERS, ring_signature

sys.path.insert(0, str(ROOT / "src"))
from convert.Geometry.Parasolid import BuildPartModel, KMissingParam
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream, KPartitionStream
from convert.adapters.solidworks.Core.Adapter import BrepPayloads
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import ReadLocalOwner
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalTree import ReadLocalTree
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import MakeLocalTables
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import ReadLocalWrap
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import ReadLocalState
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def inspect(blob, case, expected_feature):
    archive = SldprtArchive.from_bytes(blob)
    payloads, diagnostics = BrepPayloads(archive, ReadOptions())
    require(not diagnostics, "local payload intake produced diagnostics")
    payload, mark, prior_mark = ReadLocalState(payloads, archive.require(KPartitionStream))
    group = ReadLocalWrap(archive.require(KLocalBodyStream), payload)
    atom, feature = ReadLocalOwner(ReadNativeLink(archive, 0), group, mark)
    require(group == case["feature"] and feature == expected_feature and 0 < prior_mark < mark,
            "saved group, live feature and rollback ownership differ")
    nodes, offsets = ReadLocalNodes(payload)
    tree = ReadLocalTree(nodes)
    model = BuildPartModel(MakeLocalTables(nodes, offsets))
    require(not model.validate() and (len(model.bodies), len(model.faces), len(model.edges), len(model.vertices)) == (1, 6, 12, 8),
            "saved typed topology differs")
    rings = ring_signature(ReadMassRings(model))
    require(all(isclose(a, b, abs_tol=1e-9, rel_tol=0)
                for left, right in zip(rings, case["outward_rings"], strict=True)
                for p, q in zip(left, right, strict=True) for a, b in zip(p, q, strict=True)),
            "saved oriented rings differ from the measured source")
    references = [(node, ref) for node in nodes.values() for ref in XmtReferences(node) if ref not in nodes]
    require(references and all(node.KindValue == 80 and node.Integer("next") == ref for node, ref in references),
            "saved body contains a missing reference beyond an attribute definition successor")
    counts = {}
    for kind, label in KIND_OWNERS.items():
        values = [node.FieldsValue["tolerance"] for node in nodes.values() if node.KindValue == kind]
        counts[label] = {"exact": values.count(case["tolerance_m"]), "missing": values.count(KMissingParam),
                         "bits": dict(Counter(value.hex() for value in values))}
    return {"archive": artifact(blob), "kernel": artifact(payload), "resolved_feature_id": feature,
            "atom_id": atom.FieldsValue["f140"], "local_root": tree.BodyIndex,
            "current_mark": mark, "prior_mark": prior_mark, "ring_count": len(rings),
            "nonresident_attribute_successors": [[node.IndexValue, ref] for node, ref in references],
            "saved_tolerances": counts}


def main():
    parser = ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(git("rev-parse", "HEAD:src").decode().strip() == SDK_TREE
            and not git("diff", "HEAD", "--", "src"), "the warm audit requires the frozen SDK source tree")
    packet = args.packet.resolve(strict=True)
    job = verify(packet / "Job.json", args.job_sha256, completed=True, packed_worker=False)
    native = json.loads(checked(packet / "Native.json", args.native_sha256))
    require(native["passed"] and native["controls_healthy"] and native["job_sha256"] == args.job_sha256
            and set(native["saves"]) == set(CASES), "expected the complete disclosed native lifecycle")
    inputs = {name: checked(packet / "Saved" / (name + ".SLDPRT"), file["sha256"], file["bytes"])
              for name, file in native["saves"].items()}
    for name in ("utf-8", "utf-16-le", "latin-1"):
        lookup(name)
    with model_only() as accesses:
        rows = {name: inspect(inputs[name], job["cases"][name], native["phases"][name]["rebuilt"]["feature_id"])
                for name in CASES}
    report = {"schema": "kit.sw2026.baked-local-saved-tolerance-audit.v2", "job_sha256": args.job_sha256,
              "native_receipt_sha256": args.native_sha256, "native_build": native["oracle_build"],
              "native_lifecycles_healthy": native["passed"], "guarded_external_accesses": len(accesses),
              "heldout_credit": 0, "whole_source_conversions": 0, "cases": rows}
    with args.output.open("xb") as f:
        f.write(encode(report))


if __name__ == "__main__":
    main()
