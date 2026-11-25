from importlib import import_module
import math
import os
from pathlib import Path, PureWindowsPath
import platform
import shutil
import sys
import tempfile
from time import perf_counter_ns
import zlib

from ApplicationWorkers.ApplicationProtocol import exclusive_rename, sync_directory
from Corpus import git
from EncoderRoundTrip.Artifacts import (
    NATIVE_LIMIT,
    absolute,
    canonical_json,
    digest,
    exists,
    require_directory,
    write_artifact,
)
from EncoderRoundTrip.Source import decode_document
from NativeAcceptance.Records import ReadBytes


APPLICATIONS = {
    "solidworks": ("solidworks.sldprt", ".SLDPRT", "EncoderRoundTrip.Solidworks"),
    "fusion": ("fusion.f3d", ".f3d", "EncoderRoundTrip.Fusion"),
}
ROLES = ("reconstruction", "edited")
WRITTEN_AT = 1767225600
LOCATOR_ROOT = PureWindowsPath(r"C:\KitEncoderRoundTrip")
SDK_INPUT_SUFFIXES = {".py", ".json", ".xz"}
SHARED_INPUTS = (
    "re/automation/ApplicationWorkers/ApplicationProtocol.py",
    "re/automation/Corpus.py",
    "re/automation/NativeAcceptance/Records.py",
    "re/automation/NativeAcceptance/WindowsSnapshot.py",
)
IDENTITY_FIELDS = (
    "schema",
    "application",
    "sdk_revision",
    "sdk_sources_sha256",
    "runtime",
    "source_sha256",
    "neutral_sha256",
    "candidate_sha256",
    "edit",
    "written_at",
    "native_locators",
)


def _edit_depth(edit):
    if not isinstance(edit, dict) or set(edit) != {"dimension", "value_mm"}:
        raise ValueError("edit requires exactly dimension and value_mm")
    value = edit["value_mm"]
    try:
        numeric = float(value) if type(value) in (int, float) else math.nan
    except OverflowError as error:
        raise ValueError("extrusion depth exceeds the millimetre domain") from error
    if (
        edit["dimension"] != "depth"
        or not math.isfinite(numeric)
        or numeric <= 0
    ):
        raise ValueError("edit must set a finite positive extrusion depth in millimetres")
    return {"dimension": "depth", "value_mm": numeric}


def _error(error, status, stage, started):
    return {
        "status": status,
        "stage": stage,
        "error_type": type(error).__name__,
        "reason": str(error)[:2048],
        "elapsed_ns": perf_counter_ns() - started,
    }


def _read_source(source, format_id, suffix, directory):
    started = perf_counter_ns()
    stage = "read_native"
    evidence = {}
    try:
        if source.suffix.casefold() != suffix.casefold():
            raise ValueError(f"source must be a {suffix} native file")
        content = ReadBytes(source, NATIVE_LIMIT)
        evidence = {"name": source.name, "sha256": digest(content), "bytes": len(content)}
        stage = "decode_native"
        document, neutral, comparison_only_archive = decode_document(content, format_id)
        stage = "persist_neutral"
        artifact = write_artifact(directory, "document.json", neutral)
        return document, {
            **evidence,
            "status": "decoded",
            "neutral": artifact,
            "comparison_only_archive_in_memory": comparison_only_archive,
            "elapsed_ns": perf_counter_ns() - started,
        }
    except ValueError as error:
        return None, {**evidence, **_error(error, "rejected", stage, started)}
    except OSError as error:
        if stage == "persist_neutral":
            raise
        return None, {**evidence, **_error(error, "failed", stage, started)}
    except Exception as error:
        return None, {**evidence, **_error(error, "failed", stage, started)}


def _candidate(document, edit, locator, module_name, directory, reconstruction_sha256=None):
    started = perf_counter_ns()
    stage = "load_generator"
    try:
        try:
            generator = import_module(module_name).generate_candidate
        except ModuleNotFoundError as error:
            if error.name != module_name:
                raise
            raise ValueError(f"candidate generator unavailable: {module_name}") from error
        stage = "generate_candidate"
        payload = generator(document, edit, native_locator=str(locator), written_at=WRITTEN_AT)
        stage = "validate_candidate"
        if type(payload) is not bytes or not 1 <= len(payload) <= NATIVE_LIMIT:
            raise TypeError("candidate generator must return one nonempty native byte payload of at most 256 MiB")
        payload_sha256 = digest(payload)
        if payload_sha256 == reconstruction_sha256:
            raise ValueError("edited candidate equals the reconstruction bytes")
    except ValueError as error:
        status = "unsupported" if stage != "validate_candidate" else "failed"
        return _error(error, status, stage, started)
    except Exception as error:
        return _error(error, "failed", stage, started)
    artifact = write_artifact(directory, locator.name, payload)
    return {
        "status": "awaiting_native",
        "artifact": artifact,
        "elapsed_ns": perf_counter_ns() - started,
    }


def _checkout_identity(root, module_name):
    module_path = root / "re" / "automation" / (module_name.replace(".", "/") + ".py")
    files = {
        path for path in (root / "src").rglob("*") if path.suffix in SDK_INPUT_SUFFIXES
    }
    files.update(root / name for name in SHARED_INPUTS)
    files.update(Path(__file__).parent / name for name in ("Artifacts.py", "Command.py", "Pipeline.py", "Receipts.py", "Source.py"))
    if module_path.is_file():
        files.add(module_path)
    if module_name == "EncoderRoundTrip.Solidworks":
        preparation = root / "re" / "tooling" / "sw2026" / "PreparePlainPartEvidence.py"
        if preparation.is_file():
            files.add(preparation)
    if not (root / "src" / "convert" / "__init__.py").is_file():
        raise ValueError("round trip requires the trusted checkout's SDK sources")
    source_digests = {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in files}
    return {
        "sdk_revision": git(root, "rev-parse", "HEAD").decode("ascii").strip(),
        "sdk_sources_sha256": digest(canonical_json(source_digests)),
    }


def _runtime_identity(application):
    runtime = {
        "python": sys.version,
        "implementation": sys.implementation.name,
        "platform": sys.platform,
        "machine": platform.machine(),
        "zlib_build": zlib.ZLIB_VERSION,
        "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
    }
    if application == "fusion":
        try:
            from compression.zstd import zstd_version
        except ImportError:
            zstd_version = None
        runtime["stdlib_zstd"] = zstd_version
    return runtime


def _identity(checkout, application, source, candidates, edit, locators):
    return {
        "schema": 1,
        "application": application,
        **checkout,
        "runtime": _runtime_identity(application),
        "source_sha256": source.get("sha256"),
        "neutral_sha256": source.get("neutral", {}).get("sha256"),
        "candidate_sha256": {
            role: candidates[role].get("artifact", {}).get("sha256") for role in ROLES
        },
        "edit": edit,
        "written_at": WRITTEN_AT,
        "native_locators": {role: str(locators[role]) for role in ROLES},
    }


def _locators(output, suffix, native_locator_directory):
    if native_locator_directory is None:
        parent = PureWindowsPath(output) if os.name == "nt" else LOCATOR_ROOT
    else:
        parent = PureWindowsPath(native_locator_directory)
    if not parent.is_absolute() or ".." in parent.parts:
        raise ValueError("native locator directory must be an absolute Windows path without parent traversal")
    return {role: parent / (role + suffix) for role in ROLES}


def run_round_trip(root, source, output, application, edit, *, native_locator_directory=None):
    if application not in APPLICATIONS:
        raise ValueError("unknown round-trip application")
    edit = _edit_depth(edit)
    started = perf_counter_ns()
    root, source, output = absolute(root), absolute(source), absolute(output)
    if exists(output):
        raise FileExistsError(f"round-trip output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    require_directory(output.parent)
    format_id, suffix, module_name = APPLICATIONS[application]
    locators = _locators(output, suffix, native_locator_directory)
    checkout = _checkout_identity(root, module_name)
    directory = absolute(tempfile.mkdtemp(prefix=".encoder-round-trip-", dir=output.parent))
    try:
        document, source_result = _read_source(source, format_id, suffix, directory)
        if document is None:
            candidates = {
                role: {"status": "blocked", "reason": "source was not decoded", "elapsed_ns": 0}
                for role in ROLES
            }
        else:
            reconstruction = _candidate(
                document, None, locators["reconstruction"], module_name, directory
            )
            edited = _candidate(
                document, edit, locators["edited"], module_name, directory,
                reconstruction.get("artifact", {}).get("sha256"),
            )
            candidates = {"reconstruction": reconstruction, "edited": edited}
        if checkout != _checkout_identity(root, module_name):
            raise ValueError("SDK or pipeline sources changed during the round trip, retry against a stable checkout")
        identity = _identity(checkout, application, source_result, candidates, edit, locators)
        complete_candidates = all(candidates[role]["status"] == "awaiting_native" for role in ROLES)
        result = {
            **identity,
            "run_fingerprint": digest(canonical_json(identity)),
            "status": "awaiting_native" if complete_candidates else "incomplete",
            "source": source_result,
            **candidates,
            "models_used": False,
            "vendor_loadable": False,
            "application_usable": False,
            "elapsed_ns": perf_counter_ns() - started,
        }
        write_artifact(directory, "manifest.json", canonical_json(result))
        sync_directory(directory)
        exclusive_rename(directory, output)
        sync_directory(output.parent)
        return result
    finally:
        if exists(directory):
            shutil.rmtree(directory)
