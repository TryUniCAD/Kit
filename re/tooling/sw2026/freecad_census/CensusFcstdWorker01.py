import argparse
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import time


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def simple(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(k): simple(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [simple(v) for v in value]
    return str(value)


def scrub(value, paths):
    text = str(value)
    for path in sorted(paths, key=len, reverse=True):
        text = text.replace(path, "<source>")
    text = re.sub(r"(?:/Users/|[A-Za-z]:\\\\|\\\\Mac\\)[^\s\"']+", "<path>", text)
    return text


def counts(document):
    return {
        "features": len(document.feature_timeline),
        "parameters": len(document.parameters),
        "sketches": len(document.sketches),
        "sketch_entities": sum(len(v.entities) for v in document.sketches),
        "sketch_constraints": sum(len(v.constraints) for v in document.sketches),
        "support_planes": len(document.support_planes),
        "selections": len(document.selections),
        "bodies": len(document.bodies),
        "configurations": len(document.configurations),
        "materials": len(document.materials),
        "meshes": len(document.meshes),
        "brep_payloads": len(document.brep_payloads),
        "has_brep": document.brep is not None,
        "has_assembly": document.assembly is not None,
        "has_drawing": document.DrawingValue is not None,
    }


def readwrite(request):
    base = Path(request["attempt_root"])
    code = base / "CodeRoot"
    sys.path.insert(0, str(code / "src"))
    from convert import open_document, write_document
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
        ProjectBlind,
    )
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import (
        ProjectCircle,
    )
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import (
        ReadLineLoop,
    )
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import (
        PlanCircle,
    )
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import (
        CheckAsmShape,
    )

    source = Path(request["source_path"])
    paths = request["declared_source_paths"]
    allowed = {
        os.path.normcase(resolve(value))
        for value in paths
        for resolve in (os.path.abspath, os.path.realpath)
    }
    directory = base / "Cases" / request["case_id"]
    directory.mkdir(parents=True, exist_ok=False)
    activity = {
        "stage": "read",
        "file_reads": [],
        "writer_source_reads": [],
        "process_calls": 0,
        "forbidden_external_reads": 0,
        "cad_imports": [],
    }

    def audit(event, args):
        if (
            event == "import"
            and args
            and str(args[0]).split(".")[0]
            in {"FreeCAD", "Part", "pythoncom", "win32com"}
        ):
            activity["cad_imports"].append(str(args[0]))
            raise RuntimeError("CAD runtime imports are outside this census")
        if event == "subprocess.Popen":
            activity["process_calls"] += 1
            raise RuntimeError("nested processes are outside the SDK operation")
        if (
            event != "open"
            or not args
            or not isinstance(args[0], (str, bytes, os.PathLike))
        ):
            return
        raw = os.fsdecode(args[0])
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        reading = (isinstance(mode, str) and ("r" in mode or "+" in mode)) or (
            mode is None and flags & os.O_ACCMODE == os.O_RDONLY
        )
        if not reading:
            return
        absolute = os.path.normcase(os.path.abspath(raw))
        suffix = Path(raw).suffix.casefold()
        if suffix in {".fcstd", ".sldprt", ".sldasm", ".slddrw", ".f3d", ".f3z"}:
            activity["file_reads"].append(
                {
                    "stage": activity["stage"],
                    "sha256_of_path": sha256(absolute.encode()).hexdigest(),
                }
            )
            if absolute not in allowed and not Path(absolute).is_relative_to(directory):
                activity["forbidden_external_reads"] += 1
                raise RuntimeError(
                    "unlisted external CAD dependency requires separate disclosure"
                )
            if activity["stage"] == "write" and absolute in allowed:
                activity["writer_source_reads"].append(
                    sha256(absolute.encode()).hexdigest()
                )
                raise RuntimeError(
                    "the native writer tried to reread a source CAD file"
                )

    sys.addaudithook(audit)
    result = {
        "case_id": request["case_id"],
        "input_sha256": request["source_sha256"],
        "object_types": request["object_types"],
        "source_path_unchanged": False,
        "strict_read_passed": False,
        "public_write_returned": False,
        "writer_output_count": 0,
        "native_acceptance": False,
        "no_document_mutation_or_metadata_stripping": True,
    }
    started = time.monotonic()
    try:
        if digest(source) != request["source_sha256"]:
            raise ValueError("the exact disclosed source digest changed")
        document = open_document(
            source, strict=True, include_brep=True, include_tessellation=True
        )
        result["strict_read_passed"] = True
        result["counts"] = counts(document)
        result["feature_kinds"] = dict(
            Counter(str(value.kind) for value in document.feature_timeline)
        )
        result["definition_types"] = dict(
            Counter(
                type(value.definition).__name__ for value in document.feature_timeline
            )
        )
        result["parameter_kinds"] = dict(
            Counter(str(value.value.kind) for value in document.parameters)
        )
        result["metadata_keys"] = list(document.metadata)
        result["source_attribute_keys"] = list(document.source.attributes)
        result["diagnostic_codes"] = [str(value.code) for value in document.diagnostics]
        result["validation_errors"] = [
            scrub(value, paths) for value in document.validate()
        ]
        result["capabilities"] = sorted(str(value) for value in document.capabilities)
        result["provenance_owner_counts"] = {
            key: sum(value.provenance is not None for value in values)
            for key, values in (
                ("features", document.feature_timeline),
                ("parameters", document.parameters),
                ("sketches", document.sketches),
                ("planes", document.support_planes),
                ("bodies", document.bodies),
            )
        }
        neutral = document.to_json(indent=2) + "\n"
        (directory / "Neutral.json").write_text(neutral)
        result["neutral_sha256"] = digest(directory / "Neutral.json")
        result["pure_admission_diagnostics"] = {}
        functions = {
            "public_line_plan": lambda: PlanPartWrite(document),
            "public_circle_plan": lambda: PlanCircle(document),
            "unchanged_line_owner_grammar": lambda: ProjectBlind(
                document, ReadLineLoop
            ),
            "unchanged_circle_owner_grammar": lambda: ProjectCircle(document),
        }
        if document.assembly is not None:
            functions["public_assembly_shape"] = lambda: CheckAsmShape(document)
        for label, function in functions.items():
            try:
                plan = function()
                result["pure_admission_diagnostics"][label] = {
                    "passed": True,
                    "plan_type": type(plan).__name__,
                }
            except Exception as error:
                result["pure_admission_diagnostics"][label] = {
                    "passed": False,
                    "exception": type(error).__name__,
                    "message": scrub(error, paths),
                }
        name = document.metadata.get("name")
        name_source = "unchanged document metadata name"
        if document.assembly is not None:
            root = document.assembly.root_definition_id
            name = next(
                (
                    value.name
                    for value in document.assembly.definitions
                    if value.id == root
                ),
                None,
            )
            name_source = "actual assembly root definition name"
        if not isinstance(name, str) or not name:
            name = source.stem
            name_source = "original source path basename, no neutral name inserted"
        if (
            Path(name).name != name
            or PureWindowsPath(name).name != name
            or name in {".", ".."}
        ):
            raise ValueError(
                "authored destination name cannot safely identify one output basename"
            )
        suffix = (
            ".SLDDRW"
            if document.DrawingValue is not None
            else ".SLDASM" if document.assembly is not None else ".SLDPRT"
        )
        format_id = (
            "solidworks.slddrw"
            if suffix == ".SLDDRW"
            else "solidworks.sldasm" if suffix == ".SLDASM" else "solidworks.sldprt"
        )
        destination = directory / "Output" / (name + suffix)
        destination.parent.mkdir()
        options = {
            "require_self_contained": True,
            "require_native_transfers": True,
            "allow_non_native": False,
        }
        if suffix == ".SLDASM":
            guest = (
                PureWindowsPath(request["guest_attempt_root"])
                / "Cases"
                / request["case_id"]
                / "Output"
                / destination.name
            )
            options["native_destination"] = str(guest)
        recipe = {
            "schema": "kit.sw2026.public-fcstd-census-case-recipe.v1",
            "case_id": request["case_id"],
            "source_path": str(source),
            "source_sha256": request["source_sha256"],
            "source_format": None,
            "strict": True,
            "include_brep": True,
            "include_tessellation": True,
            "neutral_sha256": result["neutral_sha256"],
            "destination": str(destination),
            "destination_format": format_id,
            "destination_name_source": name_source,
            "allow_carrier": False,
            "overwrite": False,
            "validate": True,
            "write_values": options,
            "native_acceptance": False,
        }
        publish(directory / "Recipe.json", recipe)
        result["recipe_sha256"] = digest(directory / "Recipe.json")
        result["destination_format"] = format_id
        result["destination_name_source"] = name_source
        activity["stage"] = "write"
        try:
            output = write_document(
                document,
                destination,
                destination_format=format_id,
                allow_carrier=False,
                overwrite=False,
                validate=True,
                values=options,
            )
            result["public_write_returned"] = True
            result["public_writer_result"] = {
                "adapter": output.adapter,
                "bytes_written": output.bytes_written,
                "dropped": sorted(str(value) for value in output.dropped),
                "requirements": list(output.requirements),
                "metadata": simple(output.metadata),
                "application_usable_claim": output.application_usable,
                "vendor_loadable_claim": output.vendor_loadable,
                "transfers": simple([asdict(value) for value in output.transfers]),
            }
        except Exception as error:
            result["public_refusal"] = {
                "exception": type(error).__name__,
                "message": scrub(error, paths),
            }
        finally:
            activity["stage"] = "postwrite"
        after = document.to_json(indent=2) + "\n"
        result["neutral_unchanged_after_write"] = (
            sha256(after.encode()).hexdigest() == sha256(neutral.encode()).hexdigest()
        )
        artifacts = [value for value in destination.parent.iterdir() if value.is_file()]
        result["writer_output_count"] = len(artifacts)
        result["outputs"] = [
            {
                "relative": value.relative_to(directory).as_posix(),
                "bytes": value.stat().st_size,
                "sha256": digest(value),
            }
            for value in artifacts
        ]
        if result["public_write_returned"]:
            publish(
                directory / "ReadbackRequest.json",
                {
                    "sdk_root": str(code),
                    "source_neutral": str(directory / "Neutral.json"),
                    "source_neutral_sha256": result["neutral_sha256"],
                    "target": str(destination),
                    "target_sha256": digest(destination),
                    "case_id": request["case_id"],
                    "output": str(directory / "Readback.json"),
                },
            )
    except Exception as error:
        result["case_error"] = {
            "exception": type(error).__name__,
            "message": scrub(error, paths),
        }
    finally:
        activity["stage"] = "final"
        try:
            result["source_path_unchanged"] = digest(source) == request["source_sha256"]
        except Exception:
            result["source_path_unchanged"] = False
    result["runtime_activity"] = activity
    result["elapsed_seconds"] = time.monotonic() - started
    publish(directory / "Result.json", result)
    return {
        "case_id": request["case_id"],
        "strict_read": result["strict_read_passed"],
        "public_write": result["public_write_returned"],
        "writer_outputs": result["writer_output_count"],
        "source_unchanged": result["source_path_unchanged"],
    }


def readback(request):
    sys.path.insert(0, str(Path(request["sdk_root"]) / "src"))
    from convert import open_document
    from interchange import CadDocument

    target = Path(request["target"])
    result = {
        "case_id": request["case_id"],
        "normal_strict_readback_passed": False,
        "native_acceptance": False,
    }
    try:
        if (
            digest(target) != request["target_sha256"]
            or digest(Path(request["source_neutral"]))
            != request["source_neutral_sha256"]
        ):
            raise ValueError("the generated target or exact source neutral changed")
        source = CadDocument.from_json(Path(request["source_neutral"]).read_text())
        actual = open_document(
            target, strict=True, include_brep=True, include_tessellation=True
        )
        result["normal_strict_readback_passed"] = True
        result["counts"] = counts(actual)
        result["source_counts"] = counts(source)
        result["diagnostic_codes"] = [value.code for value in actual.diagnostics]
        result["validation_errors"] = [str(value) for value in actual.validate()]
        result["all_source_feature_names_present"] = set(
            value.name for value in source.feature_timeline
        ) <= set(value.name for value in actual.feature_timeline)
        result["parameter_count_not_lower"] = len(actual.parameters) >= len(
            source.parameters
        )
        result["body_count_equal"] = len(actual.bodies) == len(source.bodies)
        result["lossless_semantic_equivalence_proven"] = False
        path = Path(request["output"]).with_name("ReadbackNeutral.json")
        path.write_text(actual.to_json(indent=2) + "\n")
        result["readback_neutral_sha256"] = digest(path)
    except Exception as error:
        result["error"] = {
            "exception": type(error).__name__,
            "message": str(error).replace(str(target), "<output>"),
        }
    publish(Path(request["output"]), result)
    return {
        "case_id": request["case_id"],
        "normal_strict_readback_passed": result["normal_strict_readback_passed"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("case", "readback"))
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_bytes())
    result = readwrite(request) if args.mode == "case" else readback(request)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
