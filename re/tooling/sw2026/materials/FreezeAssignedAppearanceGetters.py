from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output, run
import sys

from ObserveAssignedAppearanceGetters import (
    ALL_TOOLS, ARCHIVE_RECEIPT, BASE, CASES, CONTROL_SHA, NATIVE_JOB, NATIVE_RESULT,
    ORACLE, PACKET_NAME, PACKET_TOOLS, PHASES, SCHEMA, SCRIPT, SDK_TREE, SOURCE_NAME,
    checked, digest, encode, native_authority, require, verify,
)


ARCHIVE_PATH = "re/solidworks/measurements/2026/AssignedMaterialAppearanceRead01.json"
TOOL_ROOT = "re/tooling/sw2026"
ROOT = Path(__file__).resolve(strict=True).parents[4]
FIELDS = ("model_rgb", "classic_rgb", "pbr_albedo_f10", "legacy_transparency_f58",
          "classic_roughness_f74", "pbr_roughness_f2c", "render_id_words", "classic_locator_sha256")


def git(*args):
    return check_output(["git", "-C", str(ROOT), *args])


def git_bytes(revision, path):
    return git("show", f"{revision}:{path}")


def cases(archive, authority):
    entries = {}
    for slot, (name, basename, expected) in CASES.items():
        measured = authority["phases"][name]
        arc = archive["cases"][name]
        native = measured["states"]["after_save"]
        require(measured["passed"] and measured["identity"]["sha256"] == ORACLE
                and measured["file"]["sha256"] == arc["file_sha256"] == expected,
                "disclosed candidate authorities diverge")
        physical = arc["physical"]
        require(physical["CfgName"] == native["configuration"] == "Default" and physical["NativeId"] == 258
                and physical["DensityValue"] == native["mass"]["density"] == 2700
                and arc["atom_id"] == 101 and arc["display"]["state_id"] == 1
                and arc["display"]["configuration_id"] == 0 and arc["display"]["exact_replay"],
                "the exact common physical assignment and archive owner profile differs")
        slots = {scope: {field: arc[scope][field] for field in FIELDS} for scope in ("part", "holder")}
        entries[slot] = {
            "relative": f"Inspection/{name}/{basename}", "sha256": expected, "bytes": measured["file"]["bytes"],
            "config": physical["CfgName"], "display": arc["display"]["state_name"], "body": native["body_name"],
            "physical": {"part": native["part_material"], "body": native["body_material"],
                         "body_id_name": native["body_material_id_name"],
                         "body_user_name": native["body_material_user_name"], "mass": native["mass"]},
            "archive": slots,
        }
    left, right = entries.values()
    require(left["physical"]["part"] == right["physical"]["part"]
            and left["physical"]["body"] == right["physical"]["body"]
            and left["display"] == right["display"] and left["body"] == right["body"]
            and archive["cases"][CASES["D01Author"][0]]["catalog_identity_sha256"]
            == archive["cases"][CASES["D02Swap"][0]]["catalog_identity_sha256"]
            and all(left["archive"]["part"][key] != right["archive"]["part"][key]
                    for key in ("model_rgb", "classic_rgb", "pbr_albedo_f10")),
            "the two immutable A saves do not retain the documented contrast")
    return entries


def control(source, authority):
    roles = ("ControlBefore", "ControlAfter")
    prior, projections = {}, []
    for role in roles:
        wanted = authority["phases"][role]["record_sha256"]
        document = json.loads(checked(source / "Inspection" / role / "Record.json", wanted).read_bytes())
        require(document["sha256"] == CONTROL_SHA and document["opened"] and document["rebuilt"]
                and document["bodies"] == 1 and document["whats_wrong"] == 0
                and document["oracle_identity"]["sha256"] == ORACLE, "original licensed control differs")
        prior[role] = wanted
        projections.append({"features": [{key: r[key] for key in ("name", "type")} for r in document["features"]],
                            "mass": document["mass"]})
    require(projections[0] == projections[1], "original control observations disagree")
    return {"sha256": CONTROL_SHA, "bytes": checked(source / "Control.SLDPRT", CONTROL_SHA).stat().st_size,
            "prior_record_sha256": prior} | projections[0]


def freeze(source, revision):
    require(source.name == SOURCE_NAME and source.parent.name == "SdkNamedMaterial01",
            "supply the exact disclosed NativeSourcePacket03")
    require(git("rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip() == revision
            and git("rev-parse", f"{revision}^").decode().strip() == BASE
            and git("rev-parse", f"{revision}:src").decode().strip() == SDK_TREE,
            "the tooling revision must be the exact research-only child of the pinned archive evidence")
    receipt = git_bytes(BASE, ARCHIVE_PATH)
    require(sha256(receipt).hexdigest() == ARCHIVE_RECEIPT, "archive receipt hash differs")
    archive = json.loads(receipt)
    require(archive["sdk_src_tree"] == SDK_TREE and archive["native_build"] == "34.5.2.0604",
            "archive receipt scope differs")
    native_job, authority = native_authority(source)
    case_data = cases(archive, authority)
    for entry in case_data.values():
        checked(source / entry["relative"], entry["sha256"], entry["bytes"])
    baseline = control(source, authority)
    tools = {name: checked(source / "Tools" / name, native_job["tools_sha256"][name]).read_bytes()
             for name in PACKET_TOOLS}
    tools |= {SCRIPT: git_bytes(revision, f"{TOOL_ROOT}/materials/{SCRIPT}"),
              "ObserveAssemblyLoad.py": git_bytes(BASE, f"{TOOL_ROOT}/ObserveAssemblyLoad.py")}
    require(set(tools) == ALL_TOOLS, "wrong standalone guest tool closure")
    job = {
        "schema": SCHEMA, "archive_revision": BASE, "sdk_tree": SDK_TREE, "method_revision": revision,
        "archive_receipt_sha256": ARCHIVE_RECEIPT, "native_source_job_sha256": NATIVE_JOB,
        "native_source_result_sha256": NATIVE_RESULT, "phases": list(PHASES), "cases": case_data,
        "control": baseline, "tools_sha256": {name: sha256(data).hexdigest() for name, data in tools.items()},
    }
    packet = source.with_name(PACKET_NAME)
    packet.mkdir()
    (packet / "Tools").mkdir()
    for name, data in tools.items():
        (packet / "Tools" / name).write_bytes(data)
    path = packet / "Job.json"
    path.write_bytes(encode(job))
    job_pin = digest(path)
    verify(packet, job_pin, source)
    result = run([sys.executable, "-B", str(packet / "Tools" / SCRIPT), "verify",
                  "--job-sha256", job_pin, "--source", str(source)], capture_output=True, text=True, check=True)
    confirmation = json.loads(result.stdout)
    require(confirmation["passed"] and confirmation["native_processes_started"] == 0
            and confirmation["job_sha256"] == job_pin, "frozen host-only verification failed")
    return {"packet": str(packet), "job_sha256": job_pin, "method_revision": revision,
            "observer_sha256": job["tools_sha256"][SCRIPT], "members": len(tools) + 1,
            "native_processes_started": 0, "heldout_credit": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    print(encode(freeze(args.source.resolve(strict=True), args.revision)).decode(), end="")


if __name__ == "__main__":
    main()
