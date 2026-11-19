import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import platform
from shutil import copyfile
import sys
import zlib

OMISSIONS = {
    "Repacked": (),
    "OmitDisplayLists": ("Contents/DisplayLists",),
    "OmitViewBucketLists": ("Contents/VBLists",),
    "OmitDisplayStamp": ("_DL_VERSION_19000/DLUpdateStamp",),
    "OmitAllThree": (
        "Contents/DisplayLists",
        "Contents/VBLists",
        "_DL_VERSION_19000/DLUpdateStamp",
    ),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def copy_checked(source, destination, expected):
    require(
        source.is_file() and not source.is_symlink() and digest(source) == expected,
        "a declared disclosed source changed: " + source.name,
    )
    require(not destination.exists(), "the private destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    copyfile(source, destination)
    require(digest(destination) == expected, "the frozen source copy differs")


def prepare(args):
    source = args.source_packet.resolve(strict=True)
    sdk = args.sdk_root.resolve(strict=True)
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    source_guest = PureWindowsPath(args.source_guest_root)
    require(
        not output.exists()
        and not output.is_relative_to(sdk)
        and not output.is_relative_to(source)
        and guest.is_absolute()
        and source_guest.is_absolute()
        and guest.name == output.name,
        "choose an unused isolated packet with explicit absolute guest mappings",
    )
    prior_job = json.loads((source / "Job.json").read_bytes())
    prior_result = json.loads((source / "Inspection/Result.json").read_bytes())
    require(
        digest(source / "Job.json")
        == prior_result["job_sha256"]
        == "f44c830d5926001c66812e921ed36d57050ae34366854d99f474e4d639047574"
        and prior_result["complete"] is True
        and prior_result["healthy_controls"] is True
        and prior_result["distinct_processes"] == 8,
        "the existing disclosed native note/render result changed",
    )
    source_file = source / "Source/Disclosed01.SLDDRW"
    control = source / "Control.SLDDRW"
    intent = source / "Source/Intent.json"
    require(
        digest(source_file)
        == "ba31c08e6e1a915509bd8d7db8962577fe0e4bcfccf6468ce4fa92ad5b4800ad"
        and digest(control)
        == "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
        and digest(intent)
        == "7e6175c03ca5c76ad6a30e981c161d4a46f6b0366d6b39ae7de0e3d5dc52324b",
        "the exact disclosed note source, declared intent or pristine changed",
    )
    sys.path.insert(0, str(sdk / "src"))
    from convert.adapters.solidworks.Container.Container import (
        EmitSldprt,
        SldprtArchive,
        TemplateFields,
    )

    native = source_file.read_bytes()
    archive = SldprtArchive.from_bytes(native)
    require(
        archive.format_version == 4, "the disclosed drawing container version differs"
    )
    signatures, type_ids = TemplateFields(native, archive)
    streams = archive.streams
    require(
        set(key for keys in OMISSIONS.values() for key in keys) <= streams.keys(),
        "a requested viewport cache stream is absent",
    )
    output.mkdir(parents=True)
    for source_path, target in (
        (source_file, "Inputs/Source/Disclosed01.SLDDRW"),
        (control, "Inputs/Pristine/Control.SLDDRW"),
        (intent, "Intent.json"),
        (source / "GridApi01.json", "GridApi01.json"),
        (source / "Job.json", "Evidence/DisplayFlagsJob.json"),
        (source / "Inspection/Result.json", "Evidence/DisplayFlagsResult.json"),
        (source / "SheetFitDiagnostic02/Result.json", "Evidence/SheetFitResult.json"),
    ):
        copy_checked(source_path, output / target, digest(source_path))
    variants = {}
    source_order = [record.name for record in archive.records]
    for name, omitted in OMISSIONS.items():
        retained = {key: value for key, value in streams.items() if key not in omitted}
        encoded = EmitSldprt(
            list(retained.items()),
            archive.file_id,
            archive.format_version,
            signatures,
            type_ids,
        )
        decoded = SldprtArchive.from_bytes(encoded)
        require(
            decoded.file_id == archive.file_id
            and decoded.format_version == archive.format_version
            and decoded.streams == retained
            and [record.name for record in decoded.records]
            == [name for name in source_order if name not in omitted],
            "repacking changed a retained stream or directory order",
        )
        relative = "Inputs/" + name + "/Disclosed01.SLDDRW"
        target = output / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(encoded)
        variants[name] = {
            "file": relative,
            "sha256": digest(target),
            "bytes": len(encoded),
            "omitted": list(omitted),
            "retained_stream_count": len(retained),
            "retained_logical_streams_exact": True,
            "only_changes_are_declared_omissions": True,
            "diagnostic_source_copy": True,
            "writer_output": False,
        }
    for name, expected in prior_job["tools"].items():
        copy_checked(source / "Tools" / name, output / "Tools" / name, expected)
    viewport = source / "Tools/InspectNoteViewport02.py"
    copy_checked(
        viewport,
        output / "Tools" / viewport.name,
        "0abf5d3b3072b6b1d881dd51e646217848d246726e9f5281130e26320de6edeb",
    )
    for name in ("InspectNoteViewportCache01.py", Path(__file__).name):
        own = Path(__file__).resolve().parent / name
        copy_checked(own, output / "Tools" / name, digest(own))
    closure = {}
    for module in tuple(sys.modules.values()):
        raw = getattr(module, "__file__", None)
        if raw is None:
            continue
        path = Path(raw).resolve()
        if path.is_file() and path.is_relative_to(sdk / "src"):
            closure[path.relative_to(sdk).as_posix()] = digest(path)
    require(closure, "the actual shared container source closure is missing")
    publish(
        output / "Preparation.json",
        {
            "schema": "kit.sw2026.note-viewport-cache-preparation.v1",
            "reused_algorithm": "PrepareDrawingCache: TemplateFields plus EmitSldprt with untouched retained logical streams",
            "python": platform.python_version(),
            "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
            "source_sha256": sha256(native).hexdigest(),
            "source_stream_count": len(streams),
            "file_id": archive.file_id,
            "format_version": archive.format_version,
            "original_record_order": source_order,
            "logical_streams": {
                key: {"bytes": len(value), "sha256": sha256(value).hexdigest()}
                for key, value in streams.items()
            },
            "sdk_source_sha256": closure,
            "variants": variants,
            "seven_role_reduction_included": False,
            "writer_output_count": 0,
            "native_acceptance": False,
        },
    )
    for relative, expected in closure.items():
        require(
            digest(sdk / relative) == expected,
            "the container source changed during staging",
        )
    require(
        source_file.read_bytes() == native,
        "the original note source changed during staging",
    )
    job = {
        "schema": "kit.sw2026.disclosed-note-viewport-cache.v1",
        "oracle_sha256": prior_job["oracle_sha256"],
        "source_sha256": digest(source_file),
        "control_sha256": digest(control),
        "intent_sha256": digest(intent),
        "variants": variants,
        "roles": [
            "ControlBefore",
            "SourceBefore",
            *OMISSIONS,
            "SourceAfter",
            "ControlAfter",
        ],
        "original_sources": {
            "source": {
                "host": str(source_file),
                "guest": str(source_guest / "Source/Disclosed01.SLDDRW"),
                "sha256": digest(source_file),
            },
            "control": {
                "host": str(control),
                "guest": str(source_guest / "Control.SLDDRW"),
                "sha256": digest(control),
            },
            "intent": {
                "host": str(intent),
                "guest": str(source_guest / "Source/Intent.json"),
                "sha256": digest(intent),
            },
        },
        "guest_runtime": {
            "executable": args.guest_python,
            "version": "3.12.7",
            "pointer_bits": 64,
        },
        "writer_output_count": 0,
        "heldout_inputs_read": 0,
        "document_saves": 0,
        "parameter_edits": 0,
        "preference_writes": 0,
        "native_acceptance": False,
        "files_sha256": {
            path.relative_to(output).as_posix(): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    publish(output / "Trial.json", job)
    trial_sha = digest(output / "Trial.json")
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        args.guest_python,
        "-B",
        str(guest / "Tools/InspectNoteViewportCache01.py"),
    ]
    tail = [str(guest / "Trial.json"), "--trial-sha256", trial_sha]
    recipe = {
        "schema": "kit.sw2026.note-viewport-cache-recipe.v1",
        "packet_sha256": trial_sha,
        "scope": "read-only diagnostic native copies, separate three caches and combined omission, no design edit/save or writer output",
        "host_verify_argv": [
            "uv",
            "run",
            "--no-project",
            "--offline",
            "--isolated",
            "--python",
            "3.11",
            "python",
            "-B",
            str(output / "Tools/InspectNoteViewportCache01.py"),
            "verify",
            str(output / "Trial.json"),
            "--trial-sha256",
            trial_sha,
        ],
        "guest_verify_argv": [*prefix, "verify", *tail],
        "commands": [
            {
                "role": role,
                "argv": [*prefix, "phase", *tail, "--phase", role],
                "always_run_after_other_failure": role
                in ("SourceAfter", "ControlAfter"),
            }
            for role in job["roles"]
        ],
        "summary_argv": [*prefix, "summary", *tail],
        "native_processes_planned": len(job["roles"]),
        "bitmap_stages": [
            "before semantic inspection and rebuild",
            "after unchanged rebuild",
            "after ViewZoomToSheet",
        ],
        "bitmap_contract": "full 960x720 BMP SHA-256 equality, actual pose/preferences and full note/sheet/tree equality against same-batch source; both source/pristine before-after must match",
        "summary_exit_zero": "diagnostic complete and both brackets healthy; inspect all_diagnostic_copies_match separately",
        "document_saves": 0,
        "writer_output_count": 0,
        "native_acceptance": False,
    }
    publish(output / "Recipe.json", recipe)
    return {
        "packet": str(output),
        "trial_sha256": trial_sha,
        "recipe_sha256": digest(output / "Recipe.json"),
        "frozen_files": len(job["files_sha256"]),
        "native_processes_started": 0,
        "variants": variants,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-packet", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--source-guest-root", required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--guest-python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
