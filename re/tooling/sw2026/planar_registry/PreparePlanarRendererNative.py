from argparse import ArgumentParser
from base64 import b64decode
from io import BytesIO
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarRegistryBuild import ROOT, file_sha, fingerprint, load, require, subtask, write
from PlanarRendererNativeSpec import CONTROL, ENTRY, HOST_PROOF, ORACLE, PHASES, SCHEMA, SOURCE_TREE, TRIALS, WRITER, encoded, source, verify
from ProvePlanarVisualComposition import IDENTITY, LABELS, bind_sdk, canonical, source_request


OVERLAYS = (ENTRY, "re/tooling/sw2026/InspectCombinedPlanarMates.py", *(
    "re/tooling/sw2026/planar_registry/" + name + ".py" for name in (
        "PlanarRendererNativeSpec", "ReadPlanarRendererNative", "ProvePlanarVisualComposition")))
READBACK = "re/tooling/sw2026/planar_registry/ReadPlanarRendererNative.py"


def snapshot(target):
    code = target / "CodeRoot"
    code.mkdir()
    tree = subprocess.check_output(("git", "rev-parse", WRITER + ":src"), cwd=ROOT).decode().strip()
    require(tree == SOURCE_TREE, "the pinned production source tree changed")
    folders = ("src", "re/tooling/sw2026", "tests/Convert/Solidworks")
    layouts = {"src/convert/adapters/solidworks/Config/RootLayout.json"}
    for folder in folders:
        data = subprocess.check_output(("git", "archive", "--prefix=" + folder + "/", WRITER + ":" + folder), cwd=ROOT)
        with open_tar(fileobj=BytesIO(data)) as archive:
            archive.extractall(code, members=(row for row in archive.getmembers() if row.isfile()
                                             and (row.name.endswith(".py") or row.name in layouts)), filter="data")
    for relative in ("tests/__init__.py", "tests/Convert/__init__.py"):
        (code / relative).write_bytes(subprocess.check_output(("git", "show", WRITER + ":" + relative), cwd=ROOT))
    for relative in OVERLAYS:
        copyfile(ROOT / relative, code / relative)
    files = {path.relative_to(code).as_posix(): file_sha(path) for path in sorted(code.rglob("*")) if path.is_file()}
    return code, write(target / "CodeManifest.json", {"writer_revision": WRITER, "writer_src_tree": tree, "files": files})


def files(paths, digests):
    return {role: {"file": str(path), "sha256": digests[role]} for role, path in paths.items() if role in ("parent", "child")}


def delivery(code, request):
    script = code / "re/tooling/sw2026/planar_registry/ProvePlanarVisualComposition.py"
    built = subtask((script, "deliver", "--root", code), canonical(request))
    generated = {key: b64decode(value, validate=True) for key, value in built.pop("generated_bytes").items()}
    require(set(generated) == {"parent", "child"} and built["runtime_input_reads"] == 0
            and all(fingerprint(data) == {key: built[role][key] for key in ("bytes", "sha256")}
                    for role, data in generated.items()), "the guarded worker did not export its exact in-memory archive")
    return built, generated


def build_case(code, target, packet_name, disclosed, slot, prior, identity, host):
    from PlanarRendererInput import request_look
    from para.concentric.ProveVisualStateStore import registry
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    original, row, prediction = source(disclosed, slot)
    request, source_pid, scope = source_request(row, prior, identity)
    request["native_parent"] = encoded(packet_name, slot, original["parent"].name)
    authored, source_look = request_look(SldprtArchive.from_bytes(original["child"].read_bytes()), registry())
    require(fingerprint(canonical(authored))["sha256"] == host["packed_author_input_sha256"]
            and source_look == host["source"] and scope["source_locks"] == host["source_locks"],
            "the packet needs the independently verified named owner and exact prior source locks")
    request["self_appearance"]["appearance"] = authored
    target.mkdir()
    request_sha = write(target / "NeutralRequest.json", request)
    prediction_sha = write(target / "Prediction.json", prediction)
    prepare_sha = write(target / "RequestFreeze.json", {"request_sha256": request_sha, "prediction_sha256": prediction_sha,
                                                       "writer_revision": WRITER, "constructor_invocations": 0})
    first, raw = delivery(code, request)
    second, repeated = delivery(code, request)
    require(raw == repeated and len({first["pid"], second["pid"], source_pid}) == 3
            and all(first[key] == second[key] for key in first if key != "pid"),
            "two fresh guarded workers must deliver identical complete renderer archives")
    receipts = {name: write(target / name, result) for name, result in (
        ("GuardedBuildA.json", first), ("GuardedBuildB.json", second))}
    frozen = target / "FrozenGenerated"
    frozen.mkdir()
    roles = ("parent", "child")
    candidates = {role: frozen / original[role].name for role in roles}
    for role, path in candidates.items():
        path.write_bytes(raw[role])
    read = subtask((code / READBACK,), canonical({"files": {
        "original": files(original, {role: row[role + "_sha256"] for role in roles}),
        "generated": files(candidates, {role: first[role]["sha256"] for role in roles}),
    }, "prediction": prediction["initial"], "appearance": authored, "display": request["display"],
        "source_labels": prior["exact_source_display"]}))
    host_sha = write(target / "StrictHostRead.json", read)
    require(read["passed"] and read["pid"] not in {first["pid"], second["pid"], source_pid},
            "strict host preflight found a scoped owner difference: " + repr({
                mode: {key: result[key] for key in ("error", "label_discrepancies", "passed") if key in result}
                for mode, result in read["stages"].items()}))
    return {"request_sha256": request_sha, "prediction_sha256": prediction_sha, "request_freeze_sha256": prepare_sha,
            "guarded_receipts": receipts, "strict_host_read_sha256": host_sha,
            "generated": {role: first[role] for role in roles}}


def prepare(output):
    require(not output.exists() and not output.is_symlink() and output.name.startswith("PlanarRendererNative")
            and not output.is_relative_to(ROOT), "choose a new owned named-renderer packet outside the checkout")
    disclosed = output.parent
    bind_sdk(ROOT)
    root = ROOT / "re/solidworks/measurements/2026"
    prior = load(root / "SdkPlanarPriorSourceAdmission01.json", LABELS)["cases"]
    identity = load(root / "SdkPlanarAssemblyIdentity01.json", IDENTITY)["cases"]
    host = load(root / "SdkPlanarRendererComposition01.json", HOST_PROOF)["cases"]
    with TemporaryDirectory(prefix="KitPlanarRendererFreeze", dir=disclosed) as scratch:
        prepared = Path(scratch) / output.name
        prepared.mkdir()
        code, manifest = snapshot(prepared)
        _, _, control = source(disclosed, CONTROL)
        control_sha = write(prepared / "Control.json", control)
        cases = {slot: build_case(code, prepared / slot, output.name, disclosed, slot, prior[slot], identity[slot], host[slot])
                 for slot in TRIALS}
        sha = write(prepared / "Packet.json", {"schema": SCHEMA, "oracle_sha256": ORACLE, "writer_revision": WRITER,
                "writer_src_tree": SOURCE_TREE, "host_renderer_proof_sha256": HOST_PROOF, "native_acceptance": False,
                "new_heldout_credit": 0, "writer_runtime_file_reads": 0, "code_manifest_sha256": manifest,
                "control_sha256": control_sha, "cases": cases, "phases": list(PHASES)})
        prepared.rename(output)
    verify(output, sha)
    return sha


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    print(prepare(parser.parse_args().output.resolve()))


if __name__ == "__main__":
    main()
