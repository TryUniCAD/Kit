from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from subprocess import run
import sys


def audit(root, lock_row, mode):
    from AuditStockSketchProjection import exact, require
    from AuditThroughAllDisclosed import roundtrip
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from convert.adapters.solidworks.Core.TypedResolved.RequireNative import (
        RequireNative,
    )

    name = lock_row["name"]
    require(
        name in ("RevolveFull", "RevolvePartialForward", "RevolvePartialReverse"),
        "only the disclosed revolve source cohort is admitted",
    )
    directory = root / name
    path = directory / f"{name}.SLDPRT"
    native = json.loads(
        exact(directory / f"{name}.reopen.json", lock_row["phase_record_sha256"][1])
    )
    require(
        native["passed"]
        and native["source_immutable"]
        and native["oracle_identity"]["file_version"] == "34.5.2.0604",
        "revolve native source observation did not qualify",
    )
    source = exact(path, lock_row["native_sha256"])
    archive = (
        SldprtArchive.open(path) if mode == "path" else SldprtArchive.from_bytes(source)
    )
    link = ReadNativeLink(archive, 0)
    for graph in (link.ConfigValue, link.ResolvedValue):
        report = graph.ReportValue
        require(
            report["completed"]
            and not report["missing_schemas"]
            and not report["provisional_schemas"],
            "linked revolve graph is incomplete",
        )
    (feature,) = [
        row
        for row in link.ResolvedValue.RootsValue
        if row and row.ClassValue.NameValue == "moRevolution_c"
    ]
    fields = feature.FieldsValue
    end = RequireNative(fields["f8d8"], "moRevEndSpec_c")
    (row,) = NativeRows(
        RequireNative(end.FieldsValue["f18"], "moDisplayAngularDim_c").FieldsValue[
            "f850"
        ]
    )
    handle = RequireNative(row["o"], "moFeatureDimHandle_c")
    dimension = RequireNative(handle.FieldsValue["ff0"], "AngleDim_c")
    angle = RequireNative(
        dimension.FieldsValue["f28"], "moAngleParameter_c"
    ).FieldsValue["f58"]
    line = RequireNative(fields["f830"], "moLineRef_w")
    selection = RequireNative(line.FieldsValue["f58"], "moCompSketchEntHandle_c")
    axis = RequireNative(selection.FieldsValue["f0f8"], "sgLineHandle")
    actual = native["reopened"]
    require(
        isclose(angle, actual["angle_radians"], rel_tol=0.0, abs_tol=1e-12)
        and fields["f824"] == int(actual["reverse"]),
        "actual angle or direction differs from the reopen oracle",
    )
    _ = exact(path, lock_row["native_sha256"])
    return {
        "source_sha256": lock_row["native_sha256"],
        "angle_rad": angle,
        "reversed": bool(fields["f824"]),
        "angle_dimension_id": dimension.FieldsValue["f50"],
        "axis_line_slot": axis.FieldsValue["idx"],
        "axis_permanent_id": selection.FieldsValue["f100"],
        "resolved_map_base": link.ResolvedValue.MapBase,
        "resolved_map_counter": link.ResolvedValue.MapValue.CounterValue,
        "streams": roundtrip(archive, link),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("discovery", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker", nargs=2)
    args = parser.parse_args()
    repository, root = args.repository.resolve(strict=True), args.discovery.resolve(
        strict=True
    )
    sys.path[:0] = [str(repository / "src"), str(Path(__file__).resolve().parent)]
    from AuditStockSketchProjection import require, source_fingerprint

    raw = (
        repository / "re/solidworks/v2026/heldout/OrdinaryRevolveSourceLock.json"
    ).read_bytes()
    lock = json.loads(raw)
    require(
        lock["passed"] and root.name == "discovery",
        "the source cohort must be disclosed and locked",
    )
    cases = {row["name"]: row for row in lock["cases"] if row["split"] == "discovery"}
    require(len(cases) == 3, "expected three disclosed revolve sources")
    if args.worker:
        name, mode = args.worker
        require(mode in ("path", "bytes"), "unsupported archive input mode")
        print(json.dumps(audit(root, cases[name], mode), sort_keys=True))
        return
    fingerprint = source_fingerprint(repository)
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs = {
            (name, mode): executor.submit(
                run,
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(Path(__file__).resolve()),
                    str(repository),
                    str(root),
                    str(args.output),
                    "--worker",
                    name,
                    mode,
                ],
                text=True,
                capture_output=True,
                timeout=60,
            )
            for name in cases
            for mode in ("path", "bytes")
        }
        results = {}
        for spec, job in jobs.items():
            outcome = job.result()
            require(outcome.returncode == 0, outcome.stderr)
            results[spec] = json.loads(outcome.stdout)
    for name in cases:
        require(
            results[name, "path"] == results[name, "bytes"],
            "path and byte revolve owners differ",
        )
    require(
        fingerprint == source_fingerprint(repository),
        "sdk source changed during the audit",
    )
    report = {
        "schema": "kit.sw2026.sdk-ordinary-revolve-linked.v1",
        "passed": True,
        "source_lock_sha256": sha256(raw).hexdigest(),
        "source_fingerprint": fingerprint,
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": {name: results[name, "path"] for name in cases},
        "linked_stream_comparisons": sum(
            len(result["streams"]) for result in results.values()
        ),
        "sdk_processes": len(results),
        "heldout_inputs_read": 0,
        "native_launches": 0,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
