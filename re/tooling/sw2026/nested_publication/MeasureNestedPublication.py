from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
ACCESS_MODE_MASK = getattr(os, "O_ACCMODE", os.O_RDONLY | os.O_WRONLY | os.O_RDWR)
BASE = "4d7deb8495646c4e148401bb6da723ab0275d3db"
REFERENCE = ROOT / "re/solidworks/measurements/2026/SdkNestedNeutralComposition01.json"
REFERENCE_SHA = "4b950c7909de76c2691067c64af80e275c0c10b408ea35367f3ae7083929402d"
REJECTS = {
    "companion-case": ("FileExistsError", ""),
    "companion-directory": ("FileExistsError", ""),
    "root-symlink": ("FileExistsError", ""),
    "escaping-companion": ("ValueError", "nested definition destination must be a distinct sibling filename"),
    "wrong-native-name": ("ValueError", "staged final and native assembly filenames must agree"),
    "relative-native": ("ValueError", "explicit absolute windows destination"),
    "configuration": ("ValueError", "requested assembly configuration is unavailable"),
    "overwrite": ("ValueError", "assembly overwrite"),
    "unmeasured-policy": ("ApplicationUsabilityError", ""),
    "stream": ("TypeError", "filesystem bundle destination"),
    "public-closed": ("AdapterNotFoundError", "does not support the destination"),
    "stage-denied": ("PermissionError", "controlled staged companion failure"),
    "publish-denied": ("PermissionError", "controlled final companion failure"),
    "publish-race": ("FileExistsError", ""),
}


def require(condition, why):
    if not condition:
        raise ValueError(why)


def digest(data):
    return sha256(data).hexdigest()


def snapshot(directory):
    result = {}
    for entry in sorted(directory.rglob("*")):
        relative = entry.relative_to(directory).as_posix()
        if entry.is_symlink():
            result[relative] = {"symlink": str(entry.readlink())}
        elif entry.is_dir():
            result[relative] = {"directory": True}
        else:
            data = entry.read_bytes()
            result[relative] = {"bytes": len(data), "sha256": digest(data)}
    return result


class Audit:
    def __init__(self, area, target, last, names, mode):
        self.area = area
        self.target = target
        self.last = last
        self.names = frozenset(names)
        self.mode = mode
        self.active = True
        self.attempts = []
        self.published = []
        self.staged_write_attempts = []
        self.injected = False

    def inspect(self, event, args):
        if not self.active:
            return
        if event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")) or event in (
            "os.exec", "os.system", "os.startfile", "os.posix_spawn", "os.fork",
        ):
            self.attempts.append(event)
            raise PermissionError("unexpected external process or data access")
        if event == "open":
            path, mode, flags = args
            if not isinstance(path, (str, bytes)):
                self.attempts.append("descriptor open")
                raise PermissionError("unexpected descriptor open")
            location = Path(os.fsdecode(path))
            if location.is_absolute() and location.is_relative_to(self.area):
                if mode is None and location.is_dir() and location.parent == self.target.parent:
                    return
                if flags & ACCESS_MODE_MASK == os.O_WRONLY and flags & os.O_EXCL and location.name in self.names:
                    if location.parent != self.target.parent:
                        self.staged_write_attempts.append(location.name)
                        if self.mode == "stage-denied" and location.name == self.last.name:
                            raise PermissionError("controlled staged companion failure")
                    return
            self.attempts.append(("file open", location.name, mode, flags, location.is_relative_to(self.area)))
            raise PermissionError("publication attempted to read an input or write outside its destination")
        if event in ("os.scandir", "os.listdir"):
            path = args[0]
            if isinstance(path, int):
                return
            if path is None or not Path(os.fsdecode(path)).is_relative_to(self.area):
                self.attempts.append(event)
                raise PermissionError("publication inspected a directory outside its destination")
        if event not in ("os.link", "os.rename"):
            return
        destination = Path(os.fsdecode(args[1]))
        if destination.parent != self.target.parent or destination.name not in self.names:
            return
        self.published.append(destination.name)
        if self.mode == "publish-denied" and destination == self.last:
            raise PermissionError("controlled final companion failure")
        if self.mode == "publish-race" and destination == self.target and not self.injected:
            self.injected = True
            with self.last.open("xb") as output:
                output.write(b"peer owns the last nested companion")


def configure(mode, area, target, names, native):
    options = {
        "allow_carrier": mode != "unmeasured-policy",
        "require_native_transfers": True,
        "native_destination": native,
    }
    stream = None
    companions = sorted(set(names) - {target.name}, key=str.casefold)
    last = target.parent / companions[-1]
    folder = target.parent
    if mode in ("companion-case", "companion-directory", "root-symlink"):
        folder.mkdir(parents=True)
    if mode == "companion-case":
        companion = next(name for name in companions if name.endswith(".SLDASM"))
        (folder / companion.swapcase()).write_bytes(b"unrelated existing same windows name")
    elif mode == "companion-directory":
        path = folder / companions[-1]
        path.mkdir()
        (path / "content.txt").write_bytes(b"unrelated existing directory")
    elif mode == "root-symlink":
        target.symlink_to(area / "other" / target.name)
    elif mode == "wrong-native-name":
        options["native_destination"] = str(PureWindowsPath(native).with_name("Different.SLDASM"))
    elif mode == "relative-native":
        options["native_destination"] = target.name
    elif mode == "stream":
        stream = BytesIO(b"existing stream")
    return options, last, stream


def worker(job):
    sys.path[:0] = (str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"))
    from AuditNestedNeutralComposition import authored_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.AssemblyWriting.Nested.WriteNestedAsm import WriteNestedAsm
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from interchange.document.Models.DocumentProvenance import HasProvenance

    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-be", "utf-16-le"):
        lookup(encoding)
    mode = job["mode"]
    area = Path(job["area"]).resolve()
    doc, native = authored_document(job["request"])
    if mode == "escaping-companion":
        graph = doc.assembly
        child = next(row for row in graph.definitions if row.id != graph.root_definition_id and str(row.kind) == "assembly")
        definitions = tuple(replace(row, name='Nested\\Escape') if row is child else row for row in graph.definitions)
        doc = replace(doc, assembly=replace(graph, definitions=definitions))
    doc.assert_valid()
    require(not HasProvenance(doc), "expected independently authored neutral input")
    registry = GetRegistry()
    registry_writers = [(adapter.info.FormatId, type(adapter).__name__) for adapter in registry.writers()
                        if adapter.info.FormatId.startswith("solidworks.")]
    require(registry_writers == [("solidworks.sldprt", "SldprtWriter")], "nested adapter escaped private registry")
    target = area / "new" / "output" / PureWindowsPath(native["path_name"]).name
    names = tuple(job["expected"])
    options, last, stream = configure(mode, area, target, names, native["path_name"])
    settings = WriteOptions(
        overwrite=mode == "overwrite",
        configuration="No such configuration" if mode == "configuration" else doc.configurations[0].id,
        values=options,
    )
    before = snapshot(area)
    audit = Audit(area, target, last, names, mode)
    sys.addaudithook(audit.inspect)
    error = None
    result = None
    try:
        if mode == "public-closed":
            result = registry.write(doc, target, format_id="solidworks.sldasm", options=settings)
        else:
            result = WriteNestedAsm(doc, target if stream is None else stream, settings, WrittenAt=native["saved_at"])
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        audit.active = False
    require(not audit.attempts, f"publication attempted forbidden runtime access: {audit.attempts}")
    require(not any(name in ("pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "publication imported a vendor runtime")
    after = snapshot(area)
    require(not any(".kit-" in part for file in after for part in Path(file).parts), "publication left staged files")
    if mode == "fresh":
        require(error is None and result is not None, f"fresh nested publication failed: {error}")
        files = {Path(path).name: value for path, value in after.items() if "sha256" in value}
        require(files == job["expected"], "published bundle differs from pure preparation evidence")
        metadata = dict(result.metadata)
        require(
            result.path == target and result.bytes_written == files[target.name]["bytes"]
            and result.vendor_loadable is False and result.application_usable is False
            and not result.dropped and not result.requirements
            and result.native_capabilities == GetDocumentCaps(doc)
            and metadata["component_file_count"] == len(files) - 1
            and set(metadata["component_file_names"]) == set(files) - {target.name}
            and metadata["bundle_bytes_written"] == sum(value["bytes"] for value in files.values())
            and metadata["bundle_bytes_written"] == metadata["component_bytes_written"] + result.bytes_written,
            "published bundle result misstates its ownership or qualification",
        )
        return {"files": files, "metadata": metadata, "vendor_loadable": False, "application_usable": False,
                "native_transfers": sorted(value.value for value in result.native_capabilities),
                "runtime_input_file_reads": 0, "staged_write_attempts": audit.staged_write_attempts,
                "publication_attempts": audit.published}
    expected_type, expected_error = REJECTS[mode]
    require(result is None and error is not None and error["type"] == expected_type and expected_error in error["message"],
            f"unexpected failure for {mode}: {error}")
    if mode == "publish-race":
        final_peer = {name: row for name, row in after.items() if "sha256" in row}
        require(audit.injected and len(audit.published) == len(names)
                and tuple(final_peer) == (last.relative_to(area).as_posix(),)
                and last.read_bytes() == b"peer owns the last nested companion",
                "late peer was replaced or earlier successful publications survived rollback")
    else:
        require(after == before, "failed publication changed caller files or left new output")
    if mode == "publish-denied":
        require(len(audit.published) == len(names), "final companion failure did not traverse all prior publications")
    if mode == "stage-denied":
        require(bool(audit.staged_write_attempts) and not audit.published, "staging failure reached final publication")
    if mode in ("companion-case", "companion-directory", "root-symlink", "escaping-companion", "configuration", "overwrite", "public-closed"):
        require(not audit.staged_write_attempts and not audit.published, "early refusal reached bundle byte output")
    if stream is not None:
        require(stream.getvalue() == b"existing stream", "stream refusal changed caller content")
    return {"error": error["type"], "diagnostic": expected_error, "existing_entries_preserved": True,
            "runtime_input_file_reads": 0, "staged_write_attempts": audit.staged_write_attempts,
            "publication_attempts": audit.published, "peer_preserved": audit.injected}


def run_worker(job):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(job),
                 capture_output=True, text=True, timeout=90, check=False)
    require(result.returncode == 0, f"{job['mode']}: {result.stderr[-4000:]}")
    return json.loads(result.stdout)


def prove(workspace):
    sys.path[:0] = (str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"))
    from AuditNestedNeutralComposition import CASES, checked

    raw = REFERENCE.read_bytes()
    require(digest(raw) == REFERENCE_SHA, "expected the frozen neutral composition receipt")
    earlier = json.loads(raw)["cases"]
    positives = {}
    refusals = {}
    with TemporaryDirectory(prefix="KitNestedPublication") as scratch:
        area = Path(scratch).resolve()
        for name, checksum in CASES.items():
            capsule = workspace / name
            fixture = json.loads(checked(capsule / "Fixture.json", checksum))
            request = json.loads(checked(capsule / "NeutralRequest.json", fixture["request_sha256"]))
            expected = {file: {key: row[key] for key in ("bytes", "sha256")}
                        for file, row in earlier[name]["outputs"].items()}
            tasks = ("fresh", *REJECTS) if len(expected) == 4 else ("fresh",)
            for mode in tasks:
                owned = area / f"{name}-{mode}"
                owned.mkdir()
                result = run_worker({"mode": mode, "area": str(owned), "request": request, "expected": expected})
                if mode == "fresh":
                    positives[name] = {"neutral_request_sha256": fixture["request_sha256"], **result}
                else:
                    refusals[mode] = result
    publication = ROOT / "src/convert/adapters/solidworks/Core/AssemblyWriting"
    paths = [*publication.glob("Nested/*.py"), *(publication / name for name in
             ("CheckFreshAsm.py", "CheckFreshFiles.py", "WriteAsmBundle.py", "WriteAsmFiles.py"))]
    return {"schema": "kit.sw2026.staged-nested-publication.v1", "base": BASE,
            "direct_preparation_receipt_sha256": REFERENCE_SHA,
            "source_sha256": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(paths)},
            "proof_sha256": digest(HERE.read_bytes()), "fresh_workers": len(positives) + len(refusals),
            "disclosed": positives, "refusals": refusals,
            "native_launches": 0, "heldout_inputs_read": 0, "normal_public_route_enabled": False}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    report = worker(json.load(sys.stdin)) if args.worker else prove(args.workspace)
    print(json.dumps(report, sort_keys=True, indent=2))
