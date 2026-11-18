from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require, write_json
from AuthorPerpendicularMateSources import CONTROL, ORACLE, SCHEMA, TOOLS, checked
from PerpendicularSourcePlan import SCHEMA as SPEC_SCHEMA, SLOTS, disclosed_cases, expected_transforms, geometry, orthogonality, validate


SCRIPT = Path(__file__).resolve()


def windows_path(path):
    return str(PureWindowsPath(r"\\Mac\Home") / path.resolve(strict=True).relative_to(Path.home()))


def prepare(args):
    root = args.output.resolve()
    require(root.parent.is_dir() and not root.exists() and not root.is_relative_to(SCRIPT.parents[3]), "choose an unused packet outside the checkout")
    seed = checked(args.control.resolve(strict=True), CONTROL)
    source = args.native_evidence.resolve(strict=True)
    evidence = json.loads(source.read_bytes())
    require(evidence["schema"] == "kit.sw2026.perpendicular-mate-native-source.v1" and evidence["document_version"] == 19000
            and evidence["native_processes_started"] == evidence["writer_output_count"] == evidence["heldout_inputs_read"] == 0,
            "use the current source-only native ownership receipt")
    base = PureWindowsPath(args.guest_private_base)
    require(base.is_absolute() and base.drive.upper().endswith(":") and ".." not in base.parts and len(base.parts) >= 2,
            "choose an unused fixed-drive guest privacy root")
    root.mkdir()
    tools = root / "Tools"
    tools.mkdir()
    hashes = {}
    for name in TOOLS:
        target = tools / name
        copyfile(SCRIPT.parent / name, target)
        hashes[name] = digest(target)
    copyfile(seed, root / "Control.SLDPRT")
    copyfile(source, root / "NativeBinding.json")
    write_json(root / "Disclosed.json", {"schema": SPEC_SCHEMA, "cases": disclosed_cases()})
    packet = root / "Source.json"
    write_json(packet, {"schema": SCHEMA, "oracle_sha256": ORACLE, "control_sha256": CONTROL,
                        "native_binding_sha256": digest(root / "NativeBinding.json"), "tools_sha256": hashes,
                        "disclosed_sha256": digest(root / "Disclosed.json"), "guest_private_base": str(base),
                        "heldout_designs_guest_private": True, "writer_output_count": 0, "native_acceptance": False,
                        "scope": "ordinary single perpendicular datum-plane source construction and valid live reorientation plus child-depth persistence"})
    expected = digest(packet)
    command = [sys.executable, "-B", str(tools / "AuthorPerpendicularMateSources.py"), "verify", str(packet), "--packet-sha256", expected]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    require(json.loads(result.stdout) == {"passed": True, "native_processes_started": 0, "heldout_inputs_read": 0},
            "the source-only host verifier did not qualify the packet")
    write_json(root / "HostPreflight.json", {"passed": True, "native_processes_started": 0, "heldout_inputs_read": 0,
                                           "source_packet_sha256": expected, "verifier_stdout": json.loads(result.stdout),
                                           "python_version": sys.version, "disclosed_analytic_predictions": [
                                               {"id": case["id"], "initial": geometry(case), "edited": geometry(case, True),
                                                "initial_orthogonality": orthogonality(case, expected_transforms(case)),
                                                "edited_orthogonality": orthogonality(case, expected_transforms(case, True))}
                                               for case in disclosed_cases()]})
    native = windows_path(tools / "AuthorPerpendicularMateSources.py")
    prefix = ["py", args.guest_python, "-B", native]
    shared = [windows_path(packet), "--packet-sha256", expected]
    def phase(identifier, name):
        return [*prefix, "run", *shared, "--case-id", identifier, "--phase", name]
    recipe = {"schema": SCHEMA, "packet_sha256": expected, "verify": [*prefix, "verify", *shared],
              "metadata": phase("D00", "metadata"), "seal": phase("D00", "seal"),
              "cases": {identifier: {name: phase(identifier, name) for name in ("before", "author", "reopen-source", "reopen-edited", "after", "lock")}
                        for identifier in SLOTS},
              "phase_timeout_seconds": 480, "trailing_control_timeout_seconds": 240,
              "always_run_after_control_independently": True, "case_failure_stops_later_case_exposure": True,
              "progress_windows_directory": str(PureWindowsPath(windows_path(packet)).parent / "Progress"),
              "native_processes_started": 0, "heldout_specs_created_on_host": False, "writer_output_count": 0,
              "active_angular_correction_is_separate": True}
    write_json(root / "Recipe.json", recipe)
    return {"packet": str(packet), "packet_sha256": expected, "recipe_sha256": digest(root / "Recipe.json"),
            "host_preflight_sha256": digest(root / "HostPreflight.json"), "tool_hashes": hashes,
            "native_processes_started": 0, "heldout_inputs_read": 0, "heldout_designs_created": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze only the authoring method and disclosed perpendicular designs before native source production")
    parser.add_argument("output", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("--native-evidence", required=True, type=Path)
    parser.add_argument("--guest-private-base", default=r"C:\KitPerpendicularSource121")
    parser.add_argument("--guest-python", default="-3.12", choices=("-3.11", "-3.12"))
    args = parser.parse_args()
    print(json.dumps(prepare(args), sort_keys=True))


if __name__ == "__main__":
    main()
