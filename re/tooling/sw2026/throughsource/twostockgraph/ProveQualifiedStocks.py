from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveStockRegistration import (
    FORMAT, FROZEN, LEGACY, ROOT, legacy_worker, load_runtime, policy_result, require,
)


PROFILES = ("disclosed", "independent")
NATIVE_CAPS = (
    "body_structure", "configurations", "editable_sketches", "parameters",
    "parametric_history", "selections", "support_planes",
)
DIAGNOSTIC = "depthless extrusion reconstruction is unqualified"
GUARD_SCOPE = "src/convert/adapters/"
SOURCES = (
    "base/DepthlessWriter.py",
    "registry/NativeEnds.py",
    "registry/NativeWrite.py",
    "registry/RegistryWriteApi.py",
    "solidworks/Core/Preparation/IsStockChain.py",
    "solidworks/Core/Preparation/PlanNativePart.py",
    "solidworks/Core/Preparation/PrepareNative.py",
    "solidworks/Core/Writing/EmitNativeMut.py",
    "solidworks/Core/Writing/IsPartTarget.py",
    "solidworks/Core/Writing/SldprtWriter.py",
    "solidworks/Core/Writing/SldWriteInfo.py",
    "solidworks/Core/Writing/StockEndWriter.py",
)


def check_disclosed(pinned, historical_hash):
    evidence_path = ROOT / "re/solidworks/measurements/2026/SdkTwoStockPreparation01.json"
    raw = evidence_path.read_bytes()
    require(sha256(raw).hexdigest() == "0b792fb7b3a0d8c16e742cb90198093a4962361ff96645af1eed2aacacaafe63",
            "wrong disclosed preparation evidence")
    recorded = json.loads(raw)["results"]["disclosed"]
    require(pinned["streams"] == recorded["streams"] and recorded["sha256"] == historical_hash,
            "disclosed model changed an exact measured logical stream")
    exact = pinned["sha256"] == historical_hash and pinned["bytes"] == recorded["bytes"]
    require(exact or "zlib-ng" in ZLIB_RUNTIME_VERSION,
            "disclosed model no longer reproduces the frozen native-tested archive")
    return exact


def publication(folder, profile):
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import PrepareStockPart
    from convert.api.ApiContext import GetRegistry
    from ProveSdkStockWriter import (
        authored, check_independent, fingerprint, HISTORICAL_HASH, read_generated, STAMP,
    )
    from RequirePartReceipt import measure_refusals
    from VerifySdkCircleEndRegistration import OutputGuard

    document = authored(profile)
    filename = document.metadata["name"] + ".SLDPRT"
    normal = folder / "registered" / filename
    direct = folder / "direct" / filename
    locator = rf"C:\KitSdkCandidates\{filename}"
    policy = {"require_native_transfers": True}
    options = WriteOptions(values={**policy, "final_destination": str(normal)})
    adapter = GetRegistry().GetWriter(FORMAT)
    audit = OutputGuard(folder, filename)
    sys.addaudithook(audit.audit)
    with audit.active("memory"):
        unmodified = BytesIO()
        prepared = PrepareStockPart(document, unmodified, STAMP, options)
        witness = PrepareStockPart(document, BytesIO(), STAMP, WriteOptions(
            values={"final_destination": locator},
        ))
        config, = document.configurations
        require(
            adapter.supports(document, normal)
            and adapter.supports(document, unmodified)
            and adapter.ProveThroughEnd(document, normal) == document.feature_timeline[-1].id,
            "the registered part writer did not authenticate the actual cut",
        )
        candidates = (
            PrepareNative(document, normal, STAMP, WriteOptions(configuration=config.id, values=policy)),
            PrepareNative(document, direct, STAMP, replace(options, configuration=config.name)),
            *(PrepareNative(document, unmodified, STAMP, replace(options, configuration=identifier))
              for identifier in (config.id, config.name)),
        )
        raw = prepared.BytesValue
        archived = SldprtArchive.from_bytes(raw)
        restored = read_generated(raw, document)
        require(
            all(candidate.BytesValue == raw for candidate in candidates)
            and archived.streams == prepared.StreamsValue and len(archived.streams) == 10
            and not normal.parent.exists() and not direct.parent.exists()
            and not unmodified.getvalue() and unmodified.tell() == 0,
            "ordinary pure preparation changed the archive or touched the caller targets",
        )
    if os.name != "nt":
        require(raw == witness.BytesValue, "standalone host path changed the frozen locator")
    pinned = fingerprint(witness.StreamsValue, witness.BytesValue)
    exact_disclosed = None
    if profile == "disclosed":
        exact_disclosed = check_disclosed(pinned, HISTORICAL_HASH)
    else:
        check_independent(restored["bodies"])
    capabilities = sorted(value.value for value in GetDocumentCaps(document))
    require(capabilities == list(NATIVE_CAPS), "the neutral cut lost its selected-scope capabilities")
    normal.parent.mkdir()
    with audit.active("path"):
        require(normal.write_bytes(raw) == len(raw), "short internal research artifact")
    missing_receipt = measure_refusals(document, normal, str(normal), adapter, audit)
    return {
        "artifact": fingerprint(archived.streams, raw), "frozen_locator_artifact": pinned,
        "intended_capabilities": capabilities, "qualified_routes": 0, "prepared_routes": 4,
        "historical_native_digest_matches": exact_disclosed, "strict_readback": restored,
        "missing_receipt_refusals": missing_receipt, "guarded_output_events": dict(audit.events),
        "runtime_input_file_reads": len(audit.denied),
    }


def rejected_models(document):
    from interchange.Features.FeatureExtrude import ExtrudeEnd
    from interchange.Features.FeatureKinds import NativeFeature
    from interchange.Features.ScopedExtrude import ScopedExtrude
    from ProveSdkStockWriter import damage

    cut = document.feature_timeline[-1]
    prefix = document.feature_timeline[:-1]
    native = replace(cut, definition=NativeFeature(FORMAT, "unresolved_scope"))
    alternate = replace(cut.definition, end_condition=ExtrudeEnd.KUpToFirst)
    scoped = ScopedExtrude(cut.definition, "all_applicable", (), ())
    return (
        ("crossed-pick", damage(document, "foreign-body-pick"), DIAGNOSTIC),
        ("unmodeled-intent", damage(document, "source-metadata"), DIAGNOSTIC),
        ("other-depthless-end", replace(document, feature_timeline=(
            *prefix, replace(cut, definition=alternate),
        )), DIAGNOSTIC),
        ("wrapped-through-end", replace(document, feature_timeline=(
            *prefix, replace(cut, definition=scoped),
        )), DIAGNOSTIC),
        ("opaque-native", replace(document, feature_timeline=(*prefix, native)),
         "native-only feature definitions cannot be exported"),
    )


def denial(folder):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from ProveSdkStockWriter import PART, STAMP, authored
    from RequirePartReceipt import must_need_receipt
    from VerifySdkCircleEndRegistration import OutputGuard, refuses

    document = authored("disclosed")
    filename = PART + ".SLDPRT"
    existing = folder / "existing" / filename
    existing.parent.mkdir()
    sentinel = b"unaltered prior destination"
    existing.write_bytes(sentinel)
    final = rf"C:\KitSdkCandidates\{filename}"
    policy = {"require_native_transfers": True}
    options = WriteOptions(values={**policy, "final_destination": final}, overwrite=True)
    stream = BytesIO(sentinel)
    adapter = GetRegistry().GetWriter(FORMAT)
    audit = OutputGuard(folder, filename)
    sys.addaudithook(audit.audit)
    with audit.active("memory"):
        blocked = {}
        for reason, source, expected in rejected_models(document):
            via_registry = refuses(lambda: write_document(
                source, stream, destination_format=FORMAT, overwrite=True,
                allow_carrier=False, values=options.values,
            ), (ValueError,))
            via_direct = refuses(lambda: adapter.write(source, stream, options), (ValueError,))
            require(via_direct == via_registry and expected in via_direct,
                    "ordinary guard failed to retain the refusal: " + reason)
            blocked[reason] = via_direct
        for name in ("OtherName.SLDPRT", PART + ".SLDASM"):
            target = folder / "never-staged" / name
            reason = refuses(lambda: write_document(
                document, target, destination_format=FORMAT, allow_carrier=False,
            ), (ValueError,))
            require(DIAGNOSTIC in reason, "an unrelated destination acquired proof")
            blocked[name] = reason
        reason = refuses(lambda: write_document(
            document, stream, destination_format="interchange.json",
            allow_carrier=False, overwrite=True,
        ), (ValueError,))
        require(DIAGNOSTIC in reason, "the JSON writer acquired SOLIDWORKS admission")
        blocked["cross-format"] = reason
    fresh = folder / "invalid-configuration" / filename
    unavailable = WriteOptions(configuration="Unavailable", values=policy, overwrite=True)
    with audit.active("memory"):
        for target in (existing, fresh):
            reason = refuses(lambda: PrepareNative(document, target, STAMP, unavailable), (ValueError,))
            require("requested two-stock write configuration is unavailable" in reason,
                    "the internal preparation failed at an unexpected guard")
    with audit.active("path"):
        for target in (existing, fresh):
            must_need_receipt(lambda: write_document(
                document, target, destination_format=FORMAT, overwrite=True,
                allow_carrier=False, configuration="Unavailable", values=policy,
            ))
    require(
        existing.read_bytes() == stream.getvalue() == sentinel
        and tuple(existing.parent.iterdir()) == (existing,)
        and not fresh.parent.exists() and not (folder / "never-staged").exists(),
        "a refused candidate changed a prior destination or left staging state",
    )
    return {
        "blocked": blocked, "staged_refusals": 2, "prior_destinations_preserved": True,
        "no_staging_remains": True, "runtime_input_file_reads": len(audit.denied),
    }


def worker(mode, sdk):
    load_runtime(sdk)
    for dependency in ("ProofModels", "ProvePublicColdStocks", "ProveRebuiltColdStocks"):
        import_module(dependency)
    with TemporaryDirectory(prefix="KitQualifiedStockOutput-") as name:
        root = Path(name).resolve()
        if mode == "refusals":
            return denial(root)
        if mode in PROFILES:
            return publication(root, mode)
        return legacy_worker(root, mode)


def launch(mode, sdk):
    output = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode, "--sdk", str(sdk)),
        capture_output=True, check=False, timeout=90,
    )
    require(output.returncode == 0, mode + ": " + output.stderr.decode())
    return json.loads(output.stdout)


def prove():
    changed = check_output(("git", "diff", "--name-only", FROZEN, "--", "src"), cwd=ROOT)
    permitted = {GUARD_SCOPE + path for path in SOURCES}
    require(set(changed.decode().splitlines()) <= permitted,
            "a frozen construction or unrelated source file changed")
    sdk = ROOT / "src"
    results = {mode: launch(mode, sdk) for mode in (*PROFILES, "refusals")}
    first, second = (results[profile]["artifact"]["streams"] for profile in PROFILES)
    require(any(first[name]["bytes"] != second[name]["bytes"] for name in first),
            "independent source intent did not change generated stream lengths")
    with TemporaryDirectory(prefix="KitFrozenStockSdk-") as name:
        baseline = Path(name)
        raw = check_output(("git", "archive", FROZEN, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(raw)) as stream:
            stream.extractall(baseline, filter="data")
        controls = {}
        for mode in LEGACY:
            old = launch(mode, baseline / "src")
            controls[mode] = launch(mode, sdk)
            require(controls[mode] == old, "a prior native writer path changed: " + mode)
    return {
        "schema": "kit.sw2026.two-stock-preparation-gate.v1",
        "frozen_constructor_revision": FROZEN,
        "frozen_constructor_source_tree": "93f0ef018a2e403a5cf98ba2d832a2db16b362fa",
        "source_sha256": {
            name: sha256((ROOT / name).read_bytes()).hexdigest()
            for name in sorted(permitted | {str(HERE.relative_to(ROOT))})
        },
        "fresh_processes": len(results) + 2 * len(LEGACY),
        "native_runs": 0, "heldout_inputs_read": 0,
        "results": results, "legacy_parity": controls,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=(*PROFILES, "refusals", *LEGACY))
    parser.add_argument("--sdk", type=Path, default=ROOT / "src")
    args = parser.parse_args()
    print(json.dumps(worker(args.worker, args.sdk) if args.worker else prove(), indent=2))
