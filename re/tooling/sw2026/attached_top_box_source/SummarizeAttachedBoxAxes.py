from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path


JOB = "1652371d1505a8b4683573039e38dfa636aa2025165d8cce6f55e4318ef6e44e"
FILES = {
    "Result.json": "0ac0c750cd671a2f4c5dcc7e3459d79a51199c3c0cd7220ba8cc2dd6a953ac38",
    "Before.json": "aa38662c8d435ad38109ab00cd95cc2abd884fd2c70f75a1da3292436d73b50c",
    "Author.json": "33f6f6fafa3c36036fdeef164950b0dbc907850ec3cbf587b404bc481b9a5280",
    "Reopen.json": "261386282c257d777c81f712f28667b13972a87c2d5458a16c0104378c524ae3",
    "After.json": "51fd35f1acf169bd9bc6e2528a7d89cbb2066cfebe9cb0ca5f39415b1b0f32d8",
    "Original.SLDPRT": "58ae249a1317122ee95a4b2e78398c6c51cd2a9d4d628121e2a17353bde47d40",
    "Length.SLDPRT": "c49b88db7720bf7ffc0a8f947e9283156035f8d10b9b9dad1c1c04a6e2688c69",
    "Width.SLDPRT": "5f8f83a5deb6fe3608d9ab2620a659d28ac47a8accc1e2537d35761dccf891a6",
    "Height.SLDPRT": "c7b4cd94cb4c06a86607a61393c95c57fc3d3f6a57d59c282ea9b018d9d5ae63",
}
DRIVERS = ("Length@AdditiveBox Profile", "Width@AdditiveBox Profile", "Height@AdditiveBox")
MODES = ("before", "generated", "reopen", "after")
STATES = ("Original", "Length", "Width", "Height")
AXIS_PARENTS = (
    ("X-axis", ("Top Plane", "Front Plane")),
    ("Y-axis", ("Front Plane", "Right Plane")),
    ("Z-axis", ("Right Plane", "Top Plane")),
)


def checked(path, expected):
    data = path.read_bytes()
    assert not path.is_symlink() and sha256(data).hexdigest() == expected, path.name
    return data


def verify_state(observed, sizes):
    length, width, height = sizes
    assert tuple(observed["drivers_m"].values()) == tuple(sizes)
    solid = observed["solid"]
    assert (solid["body_count"], solid["name"], solid["topology"]) == (1, "Body", [8, 12, 6])
    quantities = (solid["mass"]["volume"], solid["mass"]["area"], *solid["mass"]["com"])
    expected = (length * width * height, 2 * (length * width + length * height + width * height),
                length / 2, -height / 2, width / 2)
    assert all(isclose(actual, target, rel_tol=5e-7) for actual, target in zip(quantities, expected, strict=True))
    assert tuple(observed["axes"]) == tuple(name for name, _ in AXIS_PARENTS)
    for index, (name, parents) in enumerate(AXIS_PARENTS):
        row = observed["axes"][name]
        assert row["selectable"] and set(row["parents"]) == set(parents)
        assert row["unit"] == [float(axis == index) for axis in range(3)]
        assert all(point[axis] == 0.0 for point in row["endpoints_m"] for axis in range(3) if axis != index)
    return {"drivers_m": observed["drivers_m"], "body_count": solid["body_count"],
            "body_topology": solid["topology"], "mass_properties": solid["mass"],
            "axes": observed["axes"], "tree": observed["tree"]}


def summarize(packet, evidence):
    job = loads(checked(packet / "Job.json", JOB))
    candidate = checked(packet / "F14c.SLDPRT", job["candidate_sha256"])
    build = loads(checked(packet / "Build.json", job["build_sha256"]))
    raw = {name: checked(evidence / name, sha) for name, sha in FILES.items()}
    result = loads(raw["Result.json"])
    assert result["passed"] and result["controls_healthy"] and result["candidate_unchanged"]
    assert result["job_sha256"] == JOB and result["candidate_sha256"] == job["candidate_sha256"]
    assert result["oracle_sha256"] == job["oracle_sha256"] and result["oracle_build"] == job["oracle_version"]
    phases = result["phases"]
    assert tuple(phases) == MODES and result["distinct_processes"] == 4
    for mode, filename in (("before", "Before.json"), ("after", "After.json")):
        control = loads(raw[filename])
        assert control["opened"] and control["rebuilt"] and control["sha256"] == job["control_sha256"]
        assert control["open_errors"] == control["open_warnings"] == control["whats_wrong"] == 0
        assert control["bodies"] > 0 and control["mass"]["volume"] > 0
        assert not control["dialogs"] and not control["controller_diagnostics"]
        assert phases[mode]["record_sha256"] == FILES[filename] and phases[mode]["passed"]
    identities = [phases[mode]["oracle_identity"] for mode in MODES]
    assert all(v["sha256"] == job["oracle_sha256"] and v["file_version"] == job["oracle_version"]
               and v["pe_machine"].casefold() == "0x8664" for v in identities)
    assert all(left["process_creation_filetime"] < right["process_creation_filetime"]
               for left, right in zip(identities, identities[1:]))
    reports = {}
    for mode, file in (("generated", "Author.json"), ("reopen", "Reopen.json")):
        wrapper = loads(raw[file])
        phase = phases[mode]
        assert wrapper["passed"] and not wrapper["first_failure"]
        assert wrapper["result"] | {"record_sha256": FILES[file]} == phase
        assert len(wrapper["checks"]) == phase["numeric_checks"] and all(row["passed"] for row in wrapper["checks"])
        reports[mode] = {}
        for index, state in enumerate(STATES):
            dims = list(job["original_m"])
            if index:
                dims[index - 1] = job["edit_m"][index - 1]
            observed = phase["observations"][state]
            assert tuple(observed["drivers_m"]) == DRIVERS
            if mode == "reopen":
                assert observed["open_errors"] == observed["open_warnings"] == 0
            assert phase["files"][state] == {"bytes": len(raw[state + ".SLDPRT"]), "sha256": FILES[state + ".SLDPRT"]}
            reports[mode][state] = verify_state(observed, dims)
    assert phases["generated"]["generated_open_status"] == [0, 0]
    assert all(reports["generated"][state]["tree"] == reports["reopen"][state]["tree"] for state in STATES)
    return {
        "schema": "kit.sw2026.attached-box-axes-native-receipt.v1",
        "passed": True,
        "native_process_count": 4,
        "controls_healthy": True,
        "oracle_build": job["oracle_version"],
        "oracle_sha256": job["oracle_sha256"],
        "guest_python": [result["python_version"], result["python_machine"]],
        "job_sha256": JOB,
        "observer_revision": job["observer_revision"],
        "build_sha256": job["build_sha256"],
        "candidate": {"bytes": len(candidate), "sha256": job["candidate_sha256"],
                      "native_path": job["native_path"], "immutable": True},
        "source_sha256": job["source_sha256"],
        "creation_epoch": build["creation_epoch"],
        "runtime_input_file_reads": build["runtime_input_file_reads"],
        "native_numeric_checks": {mode: phases[mode]["numeric_checks"] for mode in reports},
        "processes": {mode: dict(process_id=identity["process_id"],
                                 process_creation_filetime=identity["process_creation_filetime"])
                      for mode, identity in zip(MODES, identities, strict=True)},
        "raw_evidence_sha256": FILES,
        "observations": reports,
        "new_heldout_credits": 0,
        "corpus_conversion_credits": 0,
    }


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--packet", type=Path, required=True)
    cli.add_argument("--evidence", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    report = summarize(args.packet, args.evidence)
    with args.output.open("x", encoding="utf-8") as file:
        file.write(dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
