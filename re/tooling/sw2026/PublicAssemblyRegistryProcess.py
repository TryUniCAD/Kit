from __future__ import annotations

from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]).resolve(strict=True)
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "re/tooling/sw2026")]

from convert import open_document, write_document
from convert.api.ApiContext import GetRegistry
from interchange.document.Behavior import DocumentIo
from interchange.document.Models.DocumentProvenance import HasProvenance
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData
from MakeAssemblyBoundaryCase import make_case, make_perpendicular_case


def require(value, message):
    if not value:
        raise ValueError(message)


def state(path):
    result = {}
    for file in path.iterdir():
        if file.is_symlink():
            result[file.name] = {"symlink": os.readlink(file)}
        elif file.is_file():
            result[file.name] = {"sha256": sha256(file.read_bytes()).hexdigest(), "bytes": file.stat().st_size}
        elif file.is_dir():
            result[file.name] = {"directory": True}
    return result


def reader_info():
    adapter = GetRegistry().reader("solidworks.sldasm")
    info = adapter.info
    return {"class": type(adapter).__module__ + "." + type(adapter).__name__, "id": info.format_id,
            "extensions": list(info.extensions), "aliases": list(info.aliases),
            "capabilities": sorted(str(row) for row in info.capabilities)}


def run(mode, count, output, incoming):
    output.mkdir(parents=True, exist_ok=False)
    if incoming is not None:
        document = FromData(incoming["document"])
    elif mode.startswith("perpendicular"):
        document = make_perpendicular_case(invalid=mode == "perpendicular-invalid")
    else:
        document = make_case(count)
    document.assert_valid()
    epoch = 1794001000 if incoming is None else incoming["saved_at"]
    module = import_module("convert.adapters.solidworks.Core.AssemblyWriting.EmitAsmMut")
    module.ReadTime = lambda: epoch
    target = output / (document.metadata["name"] + ".SLDASM")
    child = output / (document.assembly.documents[0].document.metadata["name"] + ".SLDPRT")
    native = ("C:\\KitPublicRegistryProof\\" + target.name) if incoming is None else incoming["native_parent"]
    options = {"native_destination": native, "require_native_transfers": True}
    format_id, overwrite, stream = None, False, None
    if mode in ("explicit", "perpendicular-explicit"):
        format_id = "solidworks.sldasm"
    elif mode == "child-collision":
        child.write_bytes(b"preexisting owned test data")
    elif mode == "case-collision":
        child.with_name(child.name.lower()).write_bytes(b"preexisting case variant")
    elif mode == "directory-collision":
        child.mkdir()
    elif mode == "dangling-child":
        child.symlink_to(output / "missing-unrelated-target")
    elif mode == "root-collision":
        target.write_bytes(b"preexisting parent test data")
    elif mode == "overwrite-rejected":
        target.write_bytes(b"preexisting parent test data")
        child.write_bytes(b"preexisting child test data")
        overwrite = True
    elif mode == "overwrite-empty":
        overwrite = True
    elif mode == "stream-rejected":
        stream = BytesIO(b"unchanged caller stream")
        format_id = "solidworks.sldasm"
    elif mode == "missing-mapping":
        del options["native_destination"]
    elif mode == "wrong-mapping":
        options["native_destination"] = r"C:\KitPublicRegistryProof\DifferentAssembly.SLDASM"
    elif mode == "relative-mapping":
        options["native_destination"] = target.name
    elif mode == "wrong-format":
        format_id = "solidworks.sldprt"
    elif mode == "unqualified-option":
        options["recorded_fallback"] = True
    elif mode == "unsupported-mate":
        graph = document.assembly
        document = replace(document, assembly=replace(graph, mates=(replace(graph.mates[0], kind="perpendicular"), *graph.mates[1:])))
    elif mode == "named-child":
        graph = document.assembly
        actual = graph.documents[0]
        parameters = actual.document.parameters
        renamed = replace(actual.document, parameters=(replace(parameters[0], name="FrameWidth"), *parameters[1:]))
        document = replace(document, assembly=replace(graph, documents=(replace(actual, document=renamed),)))
    elif mode == "unqualified-child":
        graph = document.assembly
        actual = graph.documents[0]
        extra = replace(actual.document, metadata={**actual.document.metadata, "unprojected": "text"})
        document = replace(document, assembly=replace(graph, documents=(replace(actual, document=extra),)))
    elif mode not in ("fresh", "commit-failure", "race-protection", "direct", "perpendicular", "perpendicular-invalid"):
        raise ValueError("unknown public assembly process scenario")
    if mode == "direct":
        require(os.name == "nt", "direct Windows native-path qualification needs a genuine Windows filesystem process")
        del options["native_destination"]
    before = state(output)
    audit = {"active": False, "runtime_input_reads": [], "publication_fault_injected": False, "race_created": False}
    access_mode_mask = getattr(os, "O_ACCMODE", os.O_WRONLY | os.O_RDWR)
    def observe(event, arguments):
        if not audit["active"]:
            return
        if event == "open":
            path, mode_value, flags = arguments
            if isinstance(path, (str, bytes, os.PathLike)) and Path(os.fsdecode(path)).is_dir():
                return
            if isinstance(mode_value, str) and "r" in mode_value or isinstance(flags, int) and flags & access_mode_mask != os.O_WRONLY:
                audit["runtime_input_reads"].append(str(path))
                raise PermissionError("native writer attempted a runtime input file read")
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork"):
            raise PermissionError("native writer attempted a process or CAD runtime")
        if event in ("os.rename", "os.link") and Path(arguments[1]) == target:
            if mode == "commit-failure" and not audit["publication_fault_injected"]:
                audit["publication_fault_injected"] = True
            elif mode == "race-protection" and not audit["race_created"]:
                child.write_bytes(b"concurrent owner test data")
                audit["race_created"] = True
        if event in ("os.rename", "os.link") and Path(arguments[1]) == child and mode == "commit-failure" and audit["publication_fault_injected"]:
            audit["publication_fault_injected"] = "raised"
            raise PermissionError("controlled second publication failure")
    sys.addaudithook(observe)
    codecs = tuple(lookup(name) for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1"))
    error, result = None, None
    audit["active"] = True
    try:
        result = write_document(document, target if stream is None else stream, destination_format=format_id,
                                overwrite=overwrite, allow_carrier=False, values=options)
    except Exception as caught:
        error = {"type": type(caught).__name__, "message": str(caught)}
    finally:
        audit["active"] = False
    after = state(output)
    require(not audit["runtime_input_reads"], "the SDK writer opened a runtime input file: " + repr(audit["runtime_input_reads"]) + "; " + repr(error))
    require(not any(name.startswith(".") for name in after), "the public transaction leaked staging output")
    if mode in ("fresh", "explicit", "direct", "perpendicular", "perpendicular-explicit") or mode == "missing-mapping" and os.name == "nt":
        require(error is None and result is not None and set(after) == {target.name, child.name}, "the normal public SDK bundle was not produced")
        require(result.application_usable and result.vendor_loadable and len(result.transferred_capabilities) == 9
                and not result.dropped and not result.carrier_capabilities
                and result.metadata["component_file_count"] == 1 and result.path == target.resolve(), "normal result metadata or native transfer scope differs")
        expected_profile = ("2026_ordinary_owned_perpendicular_assembly" if any(mate.kind == "perpendicular" for mate in document.assembly.mates)
                            else "2026_ordinary_owned_planar_assembly")
        require(result.metadata["native_qualification"] == expected_profile, "the native result attests a different mate profile")
        if incoming is not None:
            require({name: row["sha256"] for name, row in after.items()} == incoming["expected_sha256"], "normal output differs from the measured native input")
    elif mode == "race-protection":
        require(audit["race_created"] and error and error["type"] == "FileExistsError"
                and set(after) == {child.name} and child.read_bytes() == b"concurrent owner test data",
                "publication did not preserve the concurrently created companion")
    else:
        require(error is not None and before == after, "a rejected or failed public write changed existing data or left a partial pair")
        if mode == "commit-failure":
            require(audit["publication_fault_injected"] == "raised", "the second publication did not execute its failure injection")
    if stream is not None:
        require(stream.getvalue() == b"unchanged caller stream", "stream rejection changed caller bytes")
    info = GetRegistry().writer("solidworks.sldasm").info
    require(info.format_id == "solidworks.sldprt" and info.extensions == (".sldprt", ".sldasm") and info.aliases == ("solidworks.sldasm",)
            and info.part_extensions == (".sldprt",) and info.assembly_extensions == (".sldasm",), "normal writer metadata changed format ownership")
    require(not GetRegistry().writer("solidworks.sldprt").supports(document, output / "anything.SLDDRW"), "drawing writing was enabled")
    return {"passed": True, "mode": mode, "worker_pid": os.getpid(), "occurrences": count, "before": before, "after": after,
            "error": error, "runtime_input_file_reads": 0, "native_processes_started": 0, "writer_native_flags": result is not None and result.vendor_loadable,
            "native_qualification_is_prior_measured_profile": True, "whole_bundle_matches_native_input": incoming is not None,
            "concurrent_companion_preserved": mode == "race-protection", "reader": reader_info()}


if __name__ == "__main__":
    incoming = None if len(sys.argv) < 6 else json.loads(Path(sys.argv[5]).read_bytes())
    print(json.dumps(run(sys.argv[2], int(sys.argv[3]), Path(sys.argv[4]).resolve(), incoming), sort_keys=True))
