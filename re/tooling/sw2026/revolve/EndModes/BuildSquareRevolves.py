from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import json

from BuildOrdinaryEndRevolves import ROOT, build_one, digest, encode
from ProjectSquareSource import square_source
from convert import open_document


def project(raw, case):
    pair, proof = square_source(raw, case)
    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    sketch, = document.sketches
    equal, = (rule for rule in sketch.constraints if rule.kind == "equal")
    entity_ids = {entity.id for entity in sketch.entities if not entity.construction}
    assert len(sketch.constraints) == 5 and len({ref.entity_id for ref in equal.references}) == 2
    assert all(ref.entity_id in entity_ids and not ref.point for ref in equal.references)
    assert equal.driving and equal.provenance is not None and equal.attributes["native_code"] == 14
    return pair, proof


def prepare_cases(spec, source_lock, sources):
    assert spec["split"] == source_lock["split"] and source_lock["passed"]
    locked = {row["name"]: row for row in source_lock["sources"]}
    assert source_lock["writer_output_count"] == 0 and source_lock["idle_after"]
    assert set(locked) == {case["name"] for case in spec["cases"]}
    cases = []
    for case in spec["cases"]:
        name = case["name"]
        source = (sources / name / (name + ".SLDPRT")).read_bytes()
        assert digest(source) == locked[name]["native_sha256"]
        pair, proof = project(source, case)
        cases.append((case | {"equal_edges": pair}, proof))
    return cases


def build_cases(cases, guest, epoch):
    requests = [{"case": case, "destination": str(guest / (case["name"] + ".SLDPRT")), "epoch": epoch}
                for case, _ in cases]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(build_one, requests))
    measured = []
    for (case, source_proof), (raw, proof) in zip(cases, results, strict=True):
        pair, generated = project(raw, case)
        assert pair == case["equal_edges"] and source_proof["words"] == generated["words"]
        assert generated["line_reference_counts"] == source_proof["line_reference_counts"] == [2, 2]
        result = {
            "source_sha256": source_proof["source_sha256"],
            "candidate_sha256": proof["archive_sha256"],
            "path_and_stream_equal": proof["path_and_stream_equal"],
            "runtime_external_access_attempts": proof["runtime_external_access_attempts"],
            "candidate_streams": proof["streams"],
            "native_relation_code": 14,
            "same_ordered_contour_operands": True,
            "strict_source_and_candidate_read": True,
        }
        measured.append((case["name"], raw, result))
    return measured


def main(spec_path, lock_path, lock_pin, output, guest, epoch):
    assert spec_path.is_absolute() and lock_path.is_absolute()
    assert output.is_absolute() and not output.is_relative_to(ROOT) and guest.is_absolute()
    lock_raw = lock_path.read_bytes()
    assert digest(lock_raw) == lock_pin
    source_lock = json.loads(lock_raw)
    spec_raw = spec_path.read_bytes()
    assert digest(spec_raw) == source_lock["spec_sha256"]
    spec = json.loads(spec_raw)
    assert spec["split"] == "discovery"
    cases = prepare_cases(spec, source_lock, lock_path.parent)
    measured = build_cases(cases, guest, epoch)
    git = lambda *args: check_output(("git", *args), cwd=ROOT, text=True).strip()
    receipt = {"schema": "kit.sw2026.square-revolve-generation.v1", "split": spec["split"],
               "source_lock_sha256": lock_pin, "spec_sha256": digest(spec_raw),
               "writer_revision": git("rev-parse", "HEAD"), "writer_source_tree": git("rev-parse", "HEAD:src"),
               "epoch": epoch, "model_worker_external_read_attempts": 0,
               "cases": {name: proof for name, _, proof in measured}}
    output.mkdir(parents=True)
    for name, raw, _ in measured:
        (output / (name + ".SLDPRT")).write_bytes(raw)
    result = encode(receipt)
    (output / "BuildReceipt.json").write_bytes(result)
    print(json.dumps({"built": len(measured), "receipt_sha256": digest(result),
                      "model_worker_external_read_attempts": 0}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--lock-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest", type=PureWindowsPath, required=True)
    parser.add_argument("--epoch", type=int, default=1760000000)
    args = parser.parse_args()
    main(args.spec, args.lock, args.lock_sha256, args.output, args.guest, args.epoch)
