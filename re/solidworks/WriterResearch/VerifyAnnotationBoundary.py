from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def worker(root, request):
    require(
        type(request) is dict
        and set(request) == {"generation", "first_name", "include_top"},
        "annotation request contains unsupported or missing fields",
    )
    import ctypes
    from functools import partial
    import socket
    from uuid import UUID

    sys.path[:0] = [str(root / "src"), str(root / "re/solidworks/WriterResearch")]
    from ConfigSavedViews import KObjectList, WriteSavedViews
    from ConfigScene.Annotation import KAnnotation, KBlockManager, WriteAnnotViews
    from ConfigScene.ModelLists import PartMarker, WriteModelLists
    from ConfigScene.SketchBlock import WriteSketchBlock
    from PartArchive import PartArchiveState, PartArchiveWriter
    from convert.adapters.solidworks.Config.ModelLists import ReadModelLists
    from convert.adapters.solidworks.Config.Presentation import (
        ReadModelTagMut,
        ReadSavedAnnots,
    )
    from convert.adapters.solidworks.Container.Archive import (
        ArchiveError,
        KBigObjectTag,
    )
    from convert.adapters.solidworks.Container.Cmgr import Stamp

    "*Top".encode("utf-16-le").decode("utf-16-le")
    modules = {}
    for name, module in tuple(sys.modules.items()):
        filename = getattr(module, "__file__", None)
        if filename is not None:
            path = Path(filename).resolve()
            if path.is_relative_to(root):
                modules[path.relative_to(root).as_posix()] = sha256(
                    path.read_bytes()
                ).hexdigest()
        require(
            not name.startswith(("win32com", "pythoncom", "comtypes")),
            "native oracle module was imported",
        )

    attempts = []
    active = [False]

    def audit(event, args):
        if active[0] and (
            event
            in (
                "open",
                "import",
                "os.system",
                "os.listdir",
                "os.scandir",
                "os.startfile",
                "os.exec",
                "os.posix_spawn",
            )
            or event.startswith(("subprocess.", "socket.", "ctypes."))
        ):
            attempts.append(event)
            raise PermissionError(
                "annotation emission forbids external access: " + event
            )

    sys.addaudithook(audit)
    active[0] = True
    for event, operation in (
        ("open", lambda: open("annotation-audit-no-source", "rb")),
        (
            "subprocess.Popen",
            lambda: subprocess.run(
                [sys.executable, "-c", "raise SystemExit(91)"], check=True
            ),
        ),
        ("import", lambda: __import__("annotation_audit_no_runtime")),
        ("socket.__new__", socket.socket),
        ("ctypes.dlopen", lambda: ctypes.CDLL("annotation-audit-no-runtime")),
    ):
        count = len(attempts)
        try:
            operation()
        except PermissionError:
            require(attempts[count:] == [event], "audit calibration event differs")
        else:
            raise ValueError("external access audit did not refuse calibration")
    calibrations = tuple(attempts)
    attempts.clear()

    def raw_state(writer):
        return (
            writer.next_index,
            tuple(sorted(writer.classes.items())),
            tuple(sorted(writer.objects.items())),
            writer.build(),
        )

    def state_json(state):
        return {
            "next_index": state.NextIndex,
            "classes": state.Classes,
            "objects": state.Objects,
        }

    def prefix(relocated=False):
        state = (
            PartArchiveState(2, (), ((1, "owned-neutral-root"),)) if relocated else None
        )
        writer = PartArchiveWriter(state)
        WriteSavedViews(writer, 19000)
        WriteSketchBlock(writer, 19000, Stamp(0, 0), UUID(int=1))
        return writer.Snapshot()

    def emit(state):
        writer = PartArchiveWriter(state)
        WriteAnnotViews(
            writer, request["generation"], request["first_name"], request["include_top"]
        )
        annotation = writer.build()
        after = writer.Snapshot()
        WriteModelLists(writer, 19000, PartMarker(3, 1))
        blob = writer.build()
        cursor = state.Cursor(blob, 0)
        take = partial(ReadModelTagMut, cursor, [])
        ReadSavedAnnots(cursor, take, Scoped=True)
        require(cursor.Offset == len(annotation), "generated annotation extent")
        require(
            PartArchiveState(
                cursor.NextIndex,
                tuple(sorted(cursor.Classes.items())),
                tuple(sorted(cursor.Objects.items())),
            )
            == after,
            "generated annotation map",
        )
        ReadModelLists(cursor, take)
        require(cursor.Offset == len(blob), "generated following model-list extent")
        require(
            PartArchiveState(
                cursor.NextIndex,
                tuple(sorted(cursor.Classes.items())),
                tuple(sorted(cursor.Objects.items())),
            )
            == writer.Snapshot(),
            "generated following map",
        )
        return {
            "annotation_bytes": len(annotation),
            "annotation_sha256": sha256(annotation).hexdigest(),
            "following_bytes": len(blob) - len(annotation),
            "complete_sha256": sha256(blob).hexdigest(),
            "before": state_json(state),
            "after": state_json(after),
            "following": state_json(writer.Snapshot()),
        }

    inherited = prefix()
    ordinary = emit(inherited)
    repeated = emit(inherited)
    require(ordinary == repeated, "same owned-neutral input must be deterministic")
    relocated = emit(prefix(True))
    require(
        ordinary["annotation_bytes"] == relocated["annotation_bytes"] == 282,
        "Top-only bounded schema-1 width",
    )
    require(
        ordinary["following_bytes"] == relocated["following_bytes"] == 164,
        "following model-list width",
    )
    require(
        ordinary["after"]["next_index"] == inherited.NextIndex + 3,
        "Top list class/object allocation",
    )
    negatives = []

    def refuses(name, change, kwargs=None):
        writer = PartArchiveWriter(inherited)
        arguments = [
            request["generation"],
            request["first_name"],
            request["include_top"],
        ]
        change(writer, arguments)
        before = raw_state(writer)
        try:
            WriteAnnotViews(writer, *arguments, **(kwargs or {}))
        except (ArchiveError, TypeError) as error:
            require(
                raw_state(writer) == before,
                "refusal mutated bytes or allocator: " + name,
            )
            negatives.append(
                {"case": name, "exception": type(error).__name__, "unchanged": True}
            )
        else:
            raise ValueError("unsupported annotation request was accepted: " + name)

    for name, generation, first_name, include_top in (
        ("duplicate_top", 19000, "*Top", True),
        ("custom_name", 19000, "OwnedCustom", False),
        ("noncardinal_name", 19000, "*Isometric", False),
        ("null_name", 19000, None, False),
        ("older_generation", 18999, "*Top", False),
        ("newer_generation", 19001, "*Top", False),
        ("integer_include_top", 19000, "*Top", 1),
        ("null_include_top", 19000, "*Top", None),
    ):
        refuses(
            name,
            lambda writer, arguments, values=(
                generation,
                first_name,
                include_top,
            ): arguments.__setitem__(slice(None), values),
        )
    for owner in (KObjectList, KBlockManager):
        refuses(
            "missing_" + owner,
            lambda writer, arguments, owner=owner: writer.classes.pop(owner),
        )
    refuses(
        "preexisting_annotation",
        lambda writer, arguments: writer.classes.__setitem__(
            KAnnotation, writer.next_index - 1
        ),
    )
    refuses("zero_counter", lambda writer, arguments: writer.SetNextIndex(0))
    refuses(
        "overflow_counter",
        lambda writer, arguments: writer.SetNextIndex(KBigObjectTag - 2),
    )
    for offset in range(3):
        refuses(
            "future_object_collision_" + str(offset),
            lambda writer, arguments, offset=offset: writer.objects.__setitem__(
                writer.next_index + offset, "unrelated-owner"
            ),
        )
        refuses(
            "future_class_collision_" + str(offset),
            lambda writer, arguments, offset=offset: writer.classes.__setitem__(
                "unrelated-class", writer.next_index + offset
            ),
        )
    for field, value in (("Aliases", [7]), ("Basis", [1.0] * 9), ("Schema", 2)):
        refuses("unexposed_" + field, lambda writer, arguments: None, {field: value})
    require(not attempts, "emission attempted external access")
    active[0] = False
    return {
        "schema": "kit.sw2026.annotation-emission-boundary.v1",
        "request": request,
        "modules": {
            "count": len(modules),
            "sha256": sha256(canonical(modules)).hexdigest(),
            "writer_sha256": {
                name: digest
                for name, digest in sorted(modules.items())
                if name.startswith("re/solidworks/WriterResearch/")
            },
        },
        "audit_calibration": calibrations,
        "emission_external_events": attempts,
        "generated": ordinary,
        "relocated": relocated,
        "refusals": negatives,
        "repeat_exact": True,
        "alias_scope": "unexpected API arguments only; native graph alias admission is not exposed",
        "vendor_source_access": False,
        "models_used": False,
        "vendor_loadable": False,
        "application_usable": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Audit source-free bounded Top annotation emission in a fresh Python process"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = worker(args.root.resolve(), json.loads(sys.stdin.buffer.read()))
        sys.stdout.buffer.write(canonical(result) + b"\n")
    else:
        request = {"generation": 19000, "first_name": "*Top", "include_top": False}
        child = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(Path(__file__).resolve()),
                "--root",
                str(args.root.resolve()),
                "--worker",
            ],
            input=canonical(request),
            capture_output=True,
            timeout=60,
            check=False,
        )
        if child.returncode:
            sys.stderr.buffer.write(child.stderr)
            raise SystemExit(child.returncode)
        result = json.loads(child.stdout)
        require(result["request"] == request, "fresh child request binding")
        input_refusals = []
        for name, invalid in (
            ("nonnull_alias", {**request, "aliases": [7]}),
            ("explicit_basis", {**request, "basis": [1.0] * 9}),
            (
                "missing_include_top",
                {key: value for key, value in request.items() if key != "include_top"},
            ),
        ):
            rejected = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(Path(__file__).resolve()),
                    "--root",
                    str(args.root.resolve()),
                    "--worker",
                ],
                input=canonical(invalid),
                capture_output=True,
                timeout=60,
                check=False,
            )
            require(
                rejected.returncode == 1
                and not rejected.stdout
                and rejected.stderr.splitlines()[-1:]
                == [b"ValueError: annotation request contains unsupported or missing fields"],
                "unexpected fresh child request refusal: " + name,
            )
            input_refusals.append(
                {
                    "case": name,
                    "returncode": rejected.returncode,
                    "before_import_or_emit": True,
                }
            )
        result["input_refusals"] = input_refusals
        revision = subprocess.run(
            ["git", "-C", str(args.root.resolve()), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        result["serializer_revision"] = revision
        result["process"] = {
            "fresh_child": True,
            "returncode": child.returncode,
            "python_version": sys.version.split()[0],
        }
        result["method_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
        sys.stdout.buffer.write(canonical(result) + b"\n")
