from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require, write_json
from AuthorThroughAllSources import CONTROL, ORACLE, PHASES, SCHEMA, TOOLS, checked
from ThroughAllSourcePlan import SCHEMA as CASE_SCHEMA, SLOTS, disclosed_cases, geometry

SCRIPT = Path(__file__).resolve()


def windows_path(path):
    return str(
        PureWindowsPath(r"\\Mac\Home")
        / path.resolve(strict=True).relative_to(Path.home())
    )


def prepare(args):
    output = args.output.resolve()
    require(
        output.parent.is_dir()
        and not output.exists()
        and not output.is_relative_to(
            args.shared_tools.resolve(strict=True).parents[2]
        ),
        "choose an unused packet outside the checkout",
    )
    control = checked(args.control.resolve(strict=True), CONTROL)
    evidence = args.native_evidence.resolve(strict=True)
    custody = args.custody.resolve(strict=True)
    base = PureWindowsPath(args.guest_private_base)
    require(
        base.is_absolute()
        and base.drive.upper().endswith(":")
        and ".." not in base.parts
        and len(base.parts) >= 2,
        "choose an unused fixed guest privacy root",
    )
    source = json.loads(evidence.read_bytes())
    require(
        source["schema"] == "kit.sw2026.through-all-construction-evidence.v1"
        and source["native_build"] == "34.5.2.0604"
        and source["writer_output_count"] == source["native_processes_started"] == 0,
        "use the exact source-only native evidence",
    )
    output.mkdir()
    (output / "Tools").mkdir()
    hashes = {}
    for name in TOOLS:
        candidate = SCRIPT.parent / name
        if not candidate.is_file():
            candidate = args.shared_tools.resolve(strict=True) / name
        target = output / "Tools" / name
        copyfile(candidate, target)
        hashes[name] = digest(target)
    copyfile(control, output / "Control.SLDPRT")
    copyfile(evidence, output / "NativeBinding.json")
    copyfile(custody, output / "Custody.json")
    write_json(
        output / "Disclosed.json", {"schema": CASE_SCHEMA, "cases": disclosed_cases()}
    )
    require(
        bool(args.previous_packet) == bool(args.previous_packet_sha256),
        "the prior source packet and exact SHA must be supplied together",
    )
    sealed_source = None
    if args.previous_packet is not None:
        prior = checked(
            args.previous_packet.resolve(strict=True), args.previous_packet_sha256
        )
        prior_job = json.loads(prior.read_bytes())
        progress = prior.parent / "Progress/D00/seal/Record.json"
        previous = json.loads(progress.read_bytes())
        require(
            prior_job["schema"] == SCHEMA
            and prior_job["guest_private_base"] == str(base)
            and prior_job["disclosed_sha256"] == digest(output / "Disclosed.json")
            and previous["packet_sha256"] == args.previous_packet_sha256
            and previous["case_id"] == "D00"
            and previous["phase"] == "seal"
            and previous["stage"] == "passed"
            and previous["passed"] is True
            and previous["writer_output_count"] == 0,
            "the prior public sealed-source custody does not qualify",
        )
        sealed_source = {
            "windows_path": str(
                base / args.previous_packet_sha256 / "D00" / "SealedSpecs.json"
            ),
            "sha256": previous["sealed_spec_sha256"],
            "packet_sha256": args.previous_packet_sha256,
            "seal_progress_sha256": digest(progress),
        }
    packet = output / "Source.json"
    write_json(
        packet,
        {
            "schema": SCHEMA,
            "oracle_sha256": ORACLE,
            "control_sha256": CONTROL,
            "tools_sha256": hashes,
            "native_binding_sha256": digest(output / "NativeBinding.json"),
            "custody_sha256": digest(output / "Custody.json"),
            "disclosed_sha256": digest(output / "Disclosed.json"),
            "guest_private_base": str(base),
            "heldout_designs_guest_private": True,
            "writer_output_count": 0,
            "native_acceptance": False,
            "guest_sealed_cases": 4,
            "scope": "ordinary principal-plane forward/reverse/both through-all cut sources; boss sources are extent discovery only",
            "public_api_enum_9_exercised": False,
            "both_encoding": "Sd false, T1 and T2 native type 1",
            "sealed_source": sealed_source,
        },
    )
    expected = digest(packet)
    command = [
        sys.executable,
        "-B",
        str(output / "Tools" / "AuthorThroughAllSources.py"),
        "verify",
        str(packet),
        "--packet-sha256",
        expected,
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, check=True, timeout=45
    )
    require(
        json.loads(result.stdout)
        == {
            "passed": True,
            "native_processes_started": 0,
            "new_heldout_inputs_read": 0,
        },
        "the frozen host verifier failed",
    )
    write_json(
        output / "HostPreflight.json",
        {
            "passed": True,
            "packet_sha256": expected,
            "python_version": sys.version,
            "native_processes_started": 0,
            "new_heldout_inputs_read": 0,
            "writer_output_count": 0,
            "disclosed_predictions": [
                {
                    "id": case["id"],
                    "source": geometry(case),
                    "edited": geometry(case, True),
                }
                for case in disclosed_cases()
            ],
        },
    )
    prefix = [
        args.guest_python,
        *(
            ["-3.12"]
            if PureWindowsPath(args.guest_python).name.casefold() in ("py", "py.exe")
            else []
        ),
        "-B",
        windows_path(output / "Tools" / "AuthorThroughAllSources.py"),
    ]
    shared = [windows_path(packet), "--packet-sha256", expected]

    def phase(identifier, name):
        return [*prefix, "run", *shared, "--case-id", identifier, "--phase", name]

    write_json(
        output / "Recipe.json",
        {
            "schema": SCHEMA,
            "packet_sha256": expected,
            "verify": [*prefix, "verify", *shared],
            "metadata": phase("D00", "metadata"),
            "seal": phase("D00", "seal"),
            "cases": {
                identifier: {
                    name: phase(identifier, name)
                    for name in PHASES
                    if name not in ("metadata", "seal")
                }
                for identifier in SLOTS
            },
            "phase_timeout_seconds": 480,
            "trailing_control_timeout_seconds": 240,
            "always_run_after_control_independently": True,
            "case_failure_stops_later_case_exposure": True,
            "progress_windows_directory": str(
                PureWindowsPath(windows_path(packet)).parent / "Progress"
            ),
            "native_processes_started": 0,
            "new_heldout_inputs_read": 0,
            "heldout_specs_created_on_host": False,
            "writer_output_count": 0,
            "boss_extent_qualification_required_before_writer": True,
        },
    )
    return {
        "packet": str(packet),
        "packet_sha256": expected,
        "recipe_sha256": digest(output / "Recipe.json"),
        "host_preflight_sha256": digest(output / "HostPreflight.json"),
        "tool_hashes": hashes,
        "native_processes_started": 0,
        "new_heldout_inputs_read": 0,
        "heldout_designs_created": 0,
        "writer_output_count": 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Freeze an independent through-all source author packet without creating or exposing heldout designs on the host"
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("--native-evidence", required=True, type=Path)
    parser.add_argument("--custody", required=True, type=Path)
    parser.add_argument("--shared-tools", required=True, type=Path)
    parser.add_argument("--guest-private-base", default=r"C:\KitThroughAllSource121")
    parser.add_argument("--guest-python", default="py")
    parser.add_argument("--previous-packet", type=Path)
    parser.add_argument("--previous-packet-sha256")
    args = parser.parse_args()
    print(json.dumps(prepare(args), sort_keys=True))


if __name__ == "__main__":
    main()
