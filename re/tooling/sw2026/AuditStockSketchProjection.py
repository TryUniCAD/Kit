from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def exact(path, digest):
    require(
        path.resolve(strict=True) == path, "source path must remain in its custody tree"
    )
    data = path.read_bytes()
    require(
        sha256(data).hexdigest() == digest, f"source digest changed for {path.name}"
    )
    return data


def disclosed(repository, source_root):
    locks = repository / "re" / "solidworks" / "v2026" / "heldout"
    blind = json.loads((locks / "OrdinaryBlindCutSourceLock.json").read_bytes())
    through = json.loads((locks / "ThroughAllSourceLock01.json").read_bytes())
    require(blind["passed"] and through["passed"], "disclosed source locks must pass")
    cases = {}
    for row in blind["cases"]:
        if row["split"] != "discovery":
            continue
        name = row["name"]
        require(
            name in ("BlindCutShallow", "BlindCutMiddle", "BlindCutDeep"),
            "unexpected blind case",
        )
        directory = (
            source_root
            / "OrdinaryBlindCutSource01"
            / "SourceLockRun02"
            / "discovery"
            / name
        )
        phase = json.loads(
            exact(directory / f"{name}.reopen.json", row["phase_record_sha256"][1])
        )
        require(
            phase["passed"] and phase["source_immutable"],
            "blind native reopen did not qualify",
        )
        cases[name] = (
            directory / f"{name}.SLDPRT",
            row["native_sha256"],
            "CurveSketch",
            phase["reopened"]["boss_profile"]["geometry"],
            phase["oracle_identity"]["file_version"],
            True,
        )
    for slot in through["slots"]:
        if slot["heldout"]:
            continue
        name = slot["slot"]
        require(name in ("D01", "D02", "D03"), "unexpected through all case")
        directory = source_root / "ThroughAllSourcePacket03"
        case = directory / "Disclosed" / name
        for state, row in slot["native_artifacts"].items():
            require(state in ("source", "edited"), "unexpected through all state")
            paths = tuple((case / "Native" / state.title()).glob("*.SLDPRT"))
            require(len(paths) == 1, "each disclosed state must own one native file")
            name_value = f"reopen-{state}"
            proof = slot["phase_records"][name_value]
            progress = directory / "Progress" / name / name_value / "Record.json"
            public = json.loads(exact(progress, proof["public_record_sha256"]))
            phase = json.loads(
                exact(case / f"{name_value}.json", public["private_record_sha256"])
            )
            require(
                phase["passed"] and phase["result"]["inputs_unchanged"],
                "through all native reopen did not qualify",
            )
            cases[f"{name}/{state}"] = (
                paths[0],
                row["sha256"],
                "StockProfile",
                phase["result"]["initial"]["profiles"]["StockProfile"]["geometry"],
                proof["native_identity"]["file_version"],
                False,
            )
    require(len(cases) == 9, "the disclosed stock corpus must have nine native states")
    return cases


def read_case(case, mode):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Lines.BindLineLoop import (
        BindLineLoop,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSketch import (
        LineSketch,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from AuditThroughAllDisclosed import roundtrip

    path, digest, caption, native, build, use_public = case
    require(
        build == "34.5.2.0604", "stock source did not come from the pinned oracle build"
    )
    payload = exact(path, digest)
    archive = (
        SldprtArchive.open(path)
        if mode == "path"
        else SldprtArchive.from_bytes(payload)
    )
    link = ReadNativeLink(archive, 0)
    if use_public:
        document = open_document(
            path if mode == "path" else payload,
            source_format="solidworks.sldprt",
            include_brep=False,
            include_tessellation=False,
        )
        require(not document.validate(), "the public document did not validate")
        (projection,) = (
            sketch for sketch in document.sketches if sketch.name == caption
        )
    else:
        model = NativePartModel(archive, None)
        (sketch,) = (sketch for sketch in model.sketches if sketch.name == caption)
        bound = BindLineLoop(sketch, IndexFeatures(link)[sketch.object_id], link)
        require(bound is not None, "the linked stock profile did not qualify")
        projection = LineSketch(bound, set())
    require(
        projection.attributes["typed_line_loop"] is True
        and not projection.parameter_ids,
        "the stock must have typed geometry and no driving length",
    )
    active = {
        point["array_index"]: point["native_creation_id"]
        for point in projection.attributes["native_point_rows"]
    }
    retired = [
        row["array_index"] for row in projection.attributes["native_retired_point_rows"]
    ]
    require(
        set(active).isdisjoint(retired) and len(active) == len(native) == 4,
        "expected four live vertices disjoint from retired slots",
    )
    require(
        len(projection.entities) == 4
        and len(projection.closed_profile_entity_ids) == 1,
        "the stock did not expose one four-edge contour",
    )
    by_slot = {row["id"][0]: row for row in native}
    axes = {
        relation.references[0].entity_id: relation.kind
        for relation in projection.constraints
    }
    require(
        len(projection.constraints) == len(axes) == 4,
        "each live line must own one actual unary axis",
    )
    lines = []
    for entity in projection.entities:
        slot = entity.attributes["typed_archive_owner"]["row_index"]
        row = by_slot[slot]
        require(
            not row["construction"] and row["kind"] == "line",
            "native stock included non-line or construction geometry",
        )
        require(
            entity.attributes["native_line_creation_id"] == row["id"][1],
            "archive line creation identity disagrees with the oracle",
        )
        point_ids = [row["point_bindings"][where]["id"] for where in ("start", "end")]
        indices = tuple(entity.attributes["native_point_indices"])
        require(
            [[index, active[index]] for index in indices] == point_ids,
            "stock endpoint bindings differ from the native point identities",
        )
        for where in ("start", "end"):
            point = getattr(entity.geometry, where)
            require(
                all(
                    isclose(value, metres * 1000.0, rel_tol=0.0, abs_tol=1e-10)
                    for value, metres in zip(
                        (point.x, point.y), row[where], strict=True
                    )
                ),
                "stock endpoint geometry differs from the oracle",
            )
        axis = "horizontal" if row["start"][1] == row["end"][1] else "vertical"
        require(
            axes[entity.id] == axis,
            "stock constraint disagrees with the oracle line axis",
        )
        lines.append({"slot": slot, "point_ids": point_ids, "axis": axis})
    _ = exact(path, digest)
    return {
        "oracle_file_version": build,
        "source_sha256": digest,
        "path": "public-sdk" if use_public else "shared-linked-sketch",
        "lines": lines,
        "retired_point_slots": retired,
        "retired_line_slots": [
            row["array_index"]
            for row in projection.attributes["native_retired_line_rows"]
        ],
        "streams": roundtrip(archive, link),
    }


def source_fingerprint(repository):
    sources = sorted((repository / "src").rglob("*.py"))
    index = [
        (path.relative_to(repository).as_posix(), sha256(path.read_bytes()).hexdigest())
        for path in sources
    ]
    return {
        "python_source_files": len(index),
        "manifest_sha256": sha256(json.dumps(index).encode()).hexdigest(),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker", nargs=2)
    args = parser.parse_args()
    repository, source_root = args.repository.resolve(
        strict=True
    ), args.source_root.resolve(strict=True)
    cases = disclosed(repository, source_root)
    if args.worker:
        name, mode = args.worker
        require(mode in ("path", "bytes"), "unknown stock input mode")
        sys.path.insert(0, str(repository / "src"))
        sys.path.insert(1, str(Path(__file__).resolve().parent))
        print(json.dumps(read_case(cases[name], mode), sort_keys=True))
        return
    fingerprint = source_fingerprint(repository)
    report = {"schema": "kit.sw2026.disclosed-stock-sketch-read.v1", "cases": {}}
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = {
            (name, mode): executor.submit(
                subprocess.run,
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(Path(__file__).resolve()),
                    str(repository),
                    str(source_root),
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
        for name in cases:
            outcomes = [jobs[name, mode].result() for mode in ("path", "bytes")]
            for outcome in outcomes:
                require(outcome.returncode == 0, outcome.stderr)
            by_path, by_bytes = (json.loads(outcome.stdout) for outcome in outcomes)
            require(by_path == by_bytes, "path and byte stock projection diverged")
            report["cases"][name] = {**by_path, "path_and_bytes_match": True}
    require(
        fingerprint == source_fingerprint(repository),
        "sdk source changed during the measurements",
    )
    report.update(
        sdk_processes=len(jobs),
        linked_stream_comparisons=sum(
            len(result["streams"]) * 2 for result in report["cases"].values()
        ),
        heldout_inputs_read=0,
        native_processes_started=0,
        writer_outputs=0,
        passed=True,
        tool_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        stream_audit_sha256=sha256(
            Path(__file__).with_name("AuditThroughAllDisclosed.py").read_bytes()
        ).hexdigest(),
        source_fingerprint=fingerprint,
    )
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
