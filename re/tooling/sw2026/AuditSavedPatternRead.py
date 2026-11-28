from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory
from traceback import walk_tb
import json
import sys
import tarfile


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
BASELINE = "319d42f3ec8bfb10c16128010605902ccd898f6d"
FORMAT = "solidworks.sldprt"
SOURCES = {
    "original": ("DirectionEnvelope.SLDPRT", "6c3027e7f6cbf67087ea96ae3543f544d406f533ad8fae127e053eba2a56c14f", 16),
    "spacing": ("DirectionEnvelopeSpacing.SLDPRT", "6eedd0f536a4f54433d9cfb1fcfcdda892be2340e14f2c232353234b772c5168", 17),
    "ordinary": ("re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT", "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6", 6),
    "legacy": ("a4e7f529a03cfd70eb3d5af493055058d5aa8789", "73f0b499c5829b5bfbdcdbb0700eee22e97c7ad6dc0a4d78c177c4d45ff5aa2c", None),
    "alternate_a": ("ColdRaisedPatternA", "60f2289933b6fa60bf601521d616c0616e6b56581eda95333e27f0d5092646a5", 21),
    "alternate_b": ("ColdRaisedPatternB", "d47491db20319c0851c2960b3f9ae0f733ffd7ecf0de5c99ab715a881e375c2b", 26),
}
NATIVE_RECEIPT = "fb0d4b55936ef81bdce01c6f1317807348b2f51b8e94cfacef036927caa03b6b"
LINK_FAILURE = "unsupported SOLIDWORKS body class moLinkedAtomIdNode_c schema 1"
STRICT_FAILURE = "saved linear pattern lacks a verified typed feature history"


def digest(value):
    return sha256(value).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def worker(source, case, previous):
    raw = sys.stdin.buffer.read()
    require(digest(raw) == SOURCES[case][1], "source bytes changed at the process boundary")
    sys.path.insert(0, str(source))
    from convert import extract_brep, open_document
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import DecodePartBase
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.Features.FeatureKinds import LinearPattern, NativeFeature

    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    guard = False
    blocked = []

    def audit(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "ctypes.dlopen"):
            blocked.append(event)
            raise RuntimeError(f"reader attempted a native launch: {event}")
        if guard and event == "open":
            blocked.append(event)
            raise RuntimeError("strict refusal attempted filesystem access")

    sys.addaudithook(audit)
    archive = SldprtArchive.from_bytes(raw)
    native, *_ = DecodePartBase(archive, None)
    version = ContainerMo(archive.streams)
    pattern = [(row.object_id, row.class_name, row.kind, row.xml_tag) for row in native.features
               if row.class_name == "moLPattern_c" or (row.xml_tag == "Feature" and row.kind == "LPattern")]
    alternate = case.startswith("alternate_")
    require(archive.format_version == 4 and IsCacheAbsent(archive) == alternate, "control envelope changed")
    saved = case in ("original", "spacing")
    link_failure = None
    link_stream = None
    if saved:
        require(version == 19000 and native.active_configuration_id == 0
                and pattern == [(52, "moLPattern_c", "LPattern", "Feature")],
                "native saved pattern identity changed")
        try:
            ReadNativeLink(archive, native.active_configuration_id, PartPattern=True)
        except ValueError as error:
            link_failure = str(error)
            require(link_failure == LINK_FAILURE
                    and any(frame.f_code.co_name == "ReadCmgrMut" for frame, _ in walk_tb(error.__traceback__)),
                    "saved linked model refused at a different owner")
            link_stream = "Contents/CMgr"
        else:
            raise ValueError("saved owner joined the complete typed codec; revisit the scoped refusal")
    elif alternate:
        require(version == 19000 and len(pattern) == 1, "measured alternate envelope lost its typed feature")
    else:
        require((version == 19000 and not pattern) if case == "ordinary"
                else (version == 14000 and len(pattern) == 5), "unrelated or legacy control changed")

    def read(geometry, strict):
        return open_document(BytesIO(raw), source_format=FORMAT, strict=strict, include_brep=geometry)

    def summary(document):
        document.assert_valid()
        return {
            "document_sha256": digest(document.to_json().encode()),
            "bodies": len(document.bodies),
            "faces": None if document.brep is None else len(document.brep.faces),
            "features": len(document.feature_timeline),
            "payload_sha256": [payload.sha256 for payload in document.brep_payloads],
        }

    reads = {}
    for geometry in (True, False):
        role = "geometry" if geometry else "design"
        if not previous and saved:
            guard = True
            try:
                read(geometry, True)
            except ValueError as error:
                require(str(error) == STRICT_FAILURE, "recognized saved history refused for another reason")
                reads["strict_" + role] = str(error)
            else:
                raise ValueError("opaque saved pattern entered strict reading")
            finally:
                guard = False
        else:
            document = read(geometry, True)
            reads["strict_" + role] = summary(document)
            if alternate:
                require(sum(isinstance(step.definition, LinearPattern) for step in document.feature_timeline) == 1,
                        "measured alternate archive lost its complete cold history")
        document = read(geometry, False)
        reads["inspect_" + role] = summary(document)
        if saved:
            actual, = [step for step in document.feature_timeline if step.id == "sldprt:feature:52"]
            require(isinstance(actual.definition, NativeFeature) and actual.operation == "linear_pattern"
                    and len(document.feature_timeline) == 31 and len(document.bodies) == 1,
                    "permissive inspection lost its real unresolved feature and inventory")
        if geometry and SOURCES[case][2] is not None:
            require(reads["inspect_geometry"]["faces"] == SOURCES[case][2], "saved geometry changed")
        if not geometry:
            require(document.brep is None and not document.brep_payloads,
                    "design-only inspection unexpectedly read the saved payload")

    extracted = []
    with TemporaryDirectory(prefix="KitSavedPatternPayloads.") as directory:
        destination = Path(directory) / "Raw"
        try:
            paths = extract_brep(BytesIO(raw), destination, source_format=FORMAT)
        except ValueError as error:
            require(alternate and "no readable Parasolid payload" in str(error) and not destination.exists(),
                    "raw extraction refused a saved payload or populated an absent output")
        else:
            extracted = [digest(path.read_bytes()) for path in paths]
            require(not alternate and extracted and extracted == reads["inspect_geometry"]["payload_sha256"],
                    "ordinary raw extraction lost the exact saved native payloads")
    require(not blocked and not any(name.startswith(("win32com", "pythoncom")) for name in sys.modules),
            "saved intake launched native software or performed a guarded disk read")
    return {"source_sha256": digest(raw), "format_version": archive.format_version, "model_version": version,
            "pattern_rows": pattern, "link_failure": link_failure, "link_stream": link_stream, "reads": reads,
            "extracted_payload_sha256": extracted, "blocked_events": len(blocked)}


def observe(root, source, case, raw, previous=False):
    command = [sys.executable, "-I", "-B", str(HERE), "--worker", case, "--sdk-root", str(source)]
    if previous:
        command.append("--previous")
    result = run(command, cwd=root, input=raw, capture_output=True, check=False, timeout=45)
    require(result.returncode == 0, result.stderr.decode())
    return json.loads(result.stdout)


def measure(root, disclosed, compression):
    report = {}
    with TemporaryDirectory(prefix="KitSavedPatternBaseline.") as directory:
        archived = check_output(["git", "archive", BASELINE, "src"], cwd=root)
        with tarfile.open(fileobj=BytesIO(archived), mode="r:") as trees:
            trees.extractall(directory, filter="data")
        for case, (name, pin, _) in SOURCES.items():
            if case == "legacy":
                raw = check_output(["git", "cat-file", "blob", name], cwd=root)
            else:
                if case.startswith("alternate_"):
                    path = compression / name / (name + ".SLDPRT")
                else:
                    path = (root if case == "ordinary" else disclosed) / name
                require(path.is_file() and not path.is_symlink(), "exact disclosed source is missing")
                raw = path.read_bytes()
            require(digest(raw) == pin, "fixture differs from the pinned disclosed or tracked file")
            before = observe(root, Path(directory) / "src", case, raw, previous=True)
            after = observe(root, root / "src", case, raw)
            if case in ("original", "spacing"):
                before_reads = before["reads"]
                after_reads = after["reads"]
                for role in ("geometry", "design"):
                    require(before_reads["strict_" + role] == before_reads["inspect_" + role],
                            "previous strict lane did more than return the opaque inspection")
                    require(after_reads["inspect_" + role] == before_reads["inspect_" + role],
                            "permissive saved inspection changed")
                require({**before, "reads": after_reads} == after, "raw or typed saved owner witness changed")
            else:
                require(before == after, "unrelated or legacy public reader changed")
            report[case] = after
    return {
        "schema": "kit.sw2026.saved-pattern-read-boundary.v1",
        "baseline_commit": BASELINE,
        "read_process_count": len(report) * 2,
        "native_processes_started": 0,
        "sealed_inputs_read": 0,
        "previous_native_receipt_sha256": NATIVE_RECEIPT,
        "worker_sha256": digest(HERE.read_bytes()),
        "production_sha256": {
            name: digest((root / "src/convert/adapters/solidworks/Core" / name).read_bytes())
            for name in ("Adapter.py", *("TypedResolved/Patterns/Cold/" + name for name in
                         ("ApplyColdPat.py", "HasColdPat.py", "ColdPatError.py", "TryColdPat.py")))
        },
        "cases": report,
    }


def main():
    parser = ArgumentParser(description="Compare exact disclosed saved-pattern public reads with the prior SDK")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--compression", type=Path)
    parser.add_argument("--worker", choices=tuple(SOURCES))
    parser.add_argument("--sdk-root", type=Path)
    parser.add_argument("--previous", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = worker(args.sdk_root, args.worker, args.previous)
    else:
        require(args.disclosed is not None and args.compression is not None,
                "disclosed saved source and measured compression directories are required")
        result = measure(args.root.resolve(), args.disclosed.resolve(), args.compression.resolve())
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
