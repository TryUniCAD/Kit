from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
from subprocess import PIPE, run
import sys
import tarfile
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASE = "d1087a98f09e63b227ab0084013f83ddc8c17ae8"
SOURCE_TREE = "f8e0c222f45a5529f1f4d90b18c525b8ab1f8bf4"
NATIVE = ROOT / "re/solidworks/measurements/2026/SdkNestedNeutralNative01.json"
NATIVE_SHA = "aa786c6aa4bc7bdae15662c4b4908205b7a0fda7fdb5bb1bb503594a6b0fb967"
GEOM = "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/"
SOURCES = tuple(GEOM + key + ".py" for key in (
    "ReadNoCache", "BuildPrismGeom", "PartGeometry", "ColdOutput/WithColdName", "ColdOutput/BindPrismCreate",
))
CONTROLS = (
    "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT",
    "re/solidworks/examples/.SLDPRT/example.SLDPRT",
)
SPEC = {"model_name": "CreatorNamed", "body_label": "Authored stock label",
        "width_mm": 17.8, "height_mm": 12.65, "depth_mm": 8.55, "centre_xy_mm": [3.2, -4.05],
        "edited_depth_mm": 13.1, "created_at": 1794700090,
        "self_path": r"C:\KitPrismCreator\CreatorNamed.SLDPRT"}


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return sha256(raw).hexdigest()


def stable(value):
    return digest(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def checked(path, expected):
    require(not path.is_symlink(), "fixture must be an actual file")
    raw = path.read_bytes()
    require(digest(raw) == expected, f"frozen digest differs for {path.name}")
    return raw


def git(*arguments):
    return run(("git", "-C", str(ROOT), *arguments), check=True, stdout=PIPE).stdout


def process(job):
    source = Path(job["source"])
    sys.path[:0] = [str(source / "src"), str(ROOT / "re/tooling/sw2026/body")]
    from convert import open_document, write_document
    from interchange.serialization.EncodeData import ToData
    require(Path(sys.modules["convert"].__file__).is_relative_to(source / "src"), "unexpected SDK source origin")
    for name in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(name)
    if job["mode"] == "build":
        from MakeColdRequest import make_request
        from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeNamedPart import MakeNamedPart
        document, options = make_request(SPEC)
        build = lambda: {"bytes": b64encode(MakeNamedPart(document, options).BytesValue).decode("ascii")}
        files = {}
    else:
        files = {Path(path): pin for path, pin in job["files"].items()}
    checked_files = set()
    denied = []
    code = (source / "src", Path(os.__file__).resolve().parent)
    scope = {path.parent for path in files}

    def guard(event, arguments):
        if event == "open":
            name, _, flags = arguments
            if isinstance(name, (str, bytes)) and not flags & (os.O_ACCMODE | os.O_CREAT | os.O_TRUNC):
                path = Path(os.fsdecode(name))
                if path in files:
                    checked_files.add(path)
                    return
                if path.suffix in (".py", ".pyc") and any(path.is_relative_to(root) for root in code):
                    return
            denied.append(event)
            raise PermissionError("unexpected data open or write")
        if event in ("os.scandir", "os.listdir"):
            name = arguments[0]
            path = Path(os.fsdecode(name)) if isinstance(name, (str, bytes)) else None
            if path is not None and (path in scope or any(path.is_relative_to(root) for root in code)):
                return
            denied.append(event)
            raise PermissionError("unexpected discovery")
        if event.startswith(("socket.", "subprocess.", "ctypes.", "winreg.")) or event in (
            "os.exec", "os.system", "os.startfile", "os.posix_spawn", "os.fork", "os.mkdir",
            "os.rename", "os.remove", "os.rmdir", "os.link", "os.symlink",
        ):
            denied.append(event)
            raise PermissionError("external process or mutation attempted")

    sys.addaudithook(guard)
    if job["mode"] == "build":
        result = build()
        require(not checked_files, "neutral construction read input files")
    else:
        path = Path(job["target"])
        for fixture, pin in files.items():
            checked(fixture, pin)
        result = {}
        for read_mode in ("default", "history"):
            doc = open_document(path, include_brep=read_mode == "default")
            doc.assert_valid()
            require(doc.source.sha256 == files[path], "public source digest differs")
            serialized = ToData(doc)
            changes = {}
            if read_mode == "default":
                inspect(serialized, set(job["implicit_creators"]), job.get("named_creator"), changes)
            result[read_mode] = {"comparison_sha256": stable(serialized), "creators": changes,
                                 "top_level_operations": [[value.name, str(value.operation)] for value in doc.feature_timeline
                                                          if value.operation is not None],
                                 "has_brep": doc.brep is not None, "native_payloads": len(doc.brep_payloads)}
            if read_mode == "default" and job["implicit_creators"]:
                candidate = BytesIO()
                try:
                    write_document(doc, candidate, destination_format=doc.source.format_id)
                except ValueError as error:
                    require(str(error).startswith("native-only feature definitions cannot be exported:"),
                            "unexpected registry refusal")
                else:
                    raise ValueError("cold readback unexpectedly acquired a public re-export route")
                require(not candidate.getvalue(), "failed registry write emitted data")
                result[read_mode]["explicit_same_format_refusal_no_output"] = True
        for fixture, pin in files.items():
            checked(fixture, pin)
    require(not denied and not any(name in ("pythoncom", "pywintypes", "Swapp") or name.startswith("win32com")
                                  for name in sys.modules), "unexpected access attempts")
    return result


def inspect(wire, implicit, named, observed):
    source = wire["source"]
    pin = source["sha256"]
    selected = pin in implicit or pin == named
    if selected:
        body, = wire["bodies"]["$tuple"]
        brep, = wire["brep"]["bodies"]["$tuple"]
        feature, = (step for step in wire["feature_timeline"]["$tuple"] if step["id"] == body["final_feature_id"])
        require(brep["design_body_id"] == body["id"] and body["topology"]["solid_count"] == 1
                and not wire["brep_payloads"]["$tuple"], "creator lacks the actual sole neutral solid owner")
        observed[Path(source["path"]).name] = {"operation": feature["operation"]["value"],
                                               "feature": feature["name"], "body_caption": body["name"],
                                               "named_owner": pin == named,
                                               "body_name_provenance_matches_feature": body["provenance"] == feature["provenance"]}
        feature["operation"]["value"] = "<measured creator>"
        if pin in implicit:
            body["name"] = "<measured label>"
            body["provenance"] = "<measured label provenance>"
    if wire["assembly"] is not None:
        for value in wire["assembly"]["documents"]["$tuple"]:
            selected = inspect(value["document"], implicit, named, observed) or selected
    if selected:
        wire["metadata"].pop("solidworks_source_semantic_sha256", None)
    return selected


def worker(**job):
    proc = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(job),
               text=True, capture_output=True, timeout=120)
    require(proc.returncode == 0 and not proc.stderr, proc.stderr[-3800:])
    return json.loads(proc.stdout)


def measure(paths, implicit, named, roots, output, table):
    for path in paths:
        job = {"mode": "read", "files": {str(item): pin for item, pin in paths.items()}, "target": str(path),
               "implicit_creators": sorted(implicit), "named_creator": named}
        before, after = (worker(source=str(source), **job) for source in roots)
        require(before["history"] == after["history"] and
                before["default"]["comparison_sha256"] == after["default"]["comparison_sha256"],
                "public reader changed unrelated state")
        old, new = before["default"]["creators"], after["default"]["creators"]
        require(old.keys() == new.keys(), "creator coverage changed")
        for key, value in new.items():
            explicit = value["named_owner"]
            require(value["operation"] == "create" and old[key]["operation"] == "join" and
                    value["feature"] == old[key]["feature"] and
                    value["body_caption"] == ("Authored stock label" if explicit else value["feature"]) and
                    old[key]["body_caption"] == ("Authored stock label" if explicit else "Solid Bodies") and
                    value["body_name_provenance_matches_feature"] is not explicit,
                    "wrong creator, explicit atom, or implicit body-caption mapping")
        for phase in (before, after):
            for row in phase.values():
                row.pop("comparison_sha256")
        output[path.name] = {"sha256": paths[path], "before": before, "after": after}
        table["compared_documents"] += 2
        table["changed_creator_observations"] += len(new)


def audit(workspace):
    require(git("rev-parse", f"{BASE}:src").decode().strip() == SOURCE_TREE, "incorrect baseline tree")
    require(git("rev-parse", "HEAD:src").decode().strip() == SOURCE_TREE
            or git("merge-base", "HEAD", BASE).decode().strip() == BASE, "unrelated reader base")
    changed = set(git("diff", "--name-only", BASE, "--", "src").decode().splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard", "--", "src").decode().splitlines())
    require(changed == set(SOURCES), "revised source paths differ from the audited scope")
    runtime = {path: digest((ROOT / path).read_bytes()) for path in SOURCES}
    initial = json.loads(checked(NATIVE, NATIVE_SHA))
    result = {"schema": "kit.sw2026.cold-prism-creator.v1", "baseline": BASE, "baseline_source_tree": SOURCE_TREE,
              "revised_sources_sha256": runtime, "tool_sha256": digest(HERE.read_bytes()),
              "native_prior_receipt_sha256": NATIVE_SHA, "bundles": {}, "controls": {},
              "compared_documents": 0, "changed_creator_observations": 0}
    with TemporaryDirectory(prefix="KitColdCreator") as folder:
        area = Path(folder).resolve()
        baseline = area / "baseline"
        baseline.mkdir()
        archive = area / "src.tar"
        with archive.open("xb") as output:
            run(("git", "-C", str(ROOT), "archive", BASE, "src"), stdout=output, check=True)
        with tarfile.open(archive) as tracked:
            tracked.extractall(baseline, filter="data")
        sources = (baseline, ROOT)
        for case in initial["cases"]:
            folder = workspace / case["case"]
            fixture = json.loads(checked(folder / "Fixture.json", case["fixture_sha256"]))
            authored = json.loads(checked(folder / "NeutralRequest.json", fixture["request_sha256"]))
            actual = {row["id"]: row for row in authored["definitions"]}

            def leaves_for(owner):
                row = actual[owner]
                if row["kind"] == "part":
                    return {fixture["files"][owner]["file"]}
                return set().union(*(leaves_for(item["target"]) for item in row["occurrences"]))

            frozen = folder / "FrozenGenerated"
            paths = {frozen / value["file"]: value["sha256"] for value in fixture["files"].values()}
            require(not frozen.is_symlink() and frozen.resolve() == frozen and
                    all(path.parent == frozen for path in paths) and set(frozen.iterdir()) == set(paths),
                    "unexpected file or mirror in frozen bundle")
            leaves = {pin for path, pin in paths.items() if path.suffix == ".SLDPRT"}
            rows = {}
            measure(paths, leaves, None, sources, rows, result)
            for identity, file in fixture["files"].items():
                require(set(rows[file["file"]]["after"]["default"]["creators"]) == leaves_for(identity),
                        "readback missed an actual authored leaf")
            result["bundles"][case["case"]] = rows

        for control in CONTROLS:
            path = ROOT / control
            pin = digest(git("show", f"{BASE}:{control}"))
            measure({path: pin}, set(), None, sources, result["controls"], result)
        generated = [b64decode(worker(source=str(source), mode="build")["bytes"], validate=True) for source in sources]
        require(generated[0] == generated[1], "related reader change changed named writer bytes")
        named = area / "CreatorNamed.SLDPRT"
        named.write_bytes(generated[0])
        measure({named: digest(generated[0])}, set(), digest(generated[0]), sources, result["controls"], result)
    require(runtime == {path: digest((ROOT / path).read_bytes()) for path in SOURCES}, "revised sources changed during the run")
    result.update({"fresh_sdk_processes": result["compared_documents"] + 2, "named_writer_byte_equal": True,
                   "audit_denials": 0, "native_processes_started": 0, "private_inputs_opened": 0,
                   "public_admission_changed": False})
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(process(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        require(args.workspace is not None and args.output is not None, "workspace and receipt paths are required")
        receipt = (json.dumps(audit(args.workspace.resolve()), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as output:
            output.write(receipt)
        print(digest(receipt))
