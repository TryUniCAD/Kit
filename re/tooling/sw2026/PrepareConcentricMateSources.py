from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest,require,write_json
from AuthorConcentricMateSources import CONTROL,ORACLE,SCHEMA,TOOLS,checked
from ConcentricSourcePlan import SCHEMA as SPEC_SCHEMA,SLOTS,coaxial_residual,disclosed_cases,expected_transforms,geometry

SCRIPT=Path(__file__).resolve()
BASELINE="7d5207f039d01788ff44f0df564fa50b485a9b0d"


def windows_path(path):
    return str(PureWindowsPath(r"\\Mac\Home")/path.resolve(strict=True).relative_to(Path.home()))


def external_root(value):
    root=value.resolve()
    require(root.parent.is_dir() and not root.exists(),"choose an unused external source packet")
    require(not any((ancestor/".git").exists() for ancestor in (root,*root.parents)),"native source packets stay outside Git checkouts")
    return root


def prior_seal(args,base):
    require((args.previous_packet is None)==(args.previous_packet_sha256 is None),"bind both prior packet and exact digest")
    if args.previous_packet is None:return None
    prior_file=checked(args.previous_packet.resolve(strict=True),args.previous_packet_sha256)
    prior_job=json.loads(prior_file.read_bytes())
    progress=json.loads((prior_file.parent/"Progress/D00/seal/Record.json").read_bytes())
    require(prior_job["schema"]==SCHEMA and prior_job["guest_private_base"]==str(base) and progress["packet_sha256"]==args.previous_packet_sha256 and progress["case_id"]=="D00" and progress["phase"]=="seal" and progress["stage"]=="passed" and progress["passed"] is True,"the previous opaque sealed specification lock differs")
    wanted=progress["sealed_spec_sha256"]
    require(type(wanted) is str and len(wanted)==64 and all(char in "0123456789abcdef" for char in wanted),"previous sealed digest is invalid")
    return {"windows_path":str(base/args.previous_packet_sha256/"D00"/"SealedSpecs.json"),"sha256":wanted}


def prepare(args):
    root=external_root(args.output)
    seed=checked(args.control.resolve(strict=True),CONTROL)
    source=args.native_evidence.resolve(strict=True)
    evidence=json.loads(source.read_bytes())
    require(evidence["schema"]=="kit.sw2026.concentric-native-source.v1" and evidence["document_version"]==19000 and evidence["native_build"]=="34.5.2.0604" and evidence["native_processes_started"]==evidence["writer_output_count"]==evidence["heldout_inputs_read"]==0,"use the exact source-only native ownership receipt")
    base=PureWindowsPath(args.guest_private_base)
    require(base.is_absolute() and base.drive.upper().endswith(":") and ".." not in base.parts and len(base.parts)>=2,"source privacy requires an explicit fixed-drive guest root")
    sealed_source=prior_seal(args,base)
    root.mkdir()
    tools=root/"Tools"
    tools.mkdir()
    hashes={}
    for name in TOOLS:
        copyfile(SCRIPT.parent/name,tools/name)
        hashes[name]=digest(tools/name)
    copyfile(seed,root/"Control.SLDPRT")
    copyfile(source,root/"NativeBinding.json")
    write_json(root/"Disclosed.json",{"schema":SPEC_SCHEMA,"cases":disclosed_cases()})
    packet=root/"Source.json"
    write_json(packet,{"schema":SCHEMA,"baseline_revision":BASELINE,"oracle_sha256":ORACLE,"control_sha256":CONTROL,"native_binding_sha256":digest(root/"NativeBinding.json"),"tools_sha256":hashes,"disclosed_sha256":digest(root/"Disclosed.json"),"guest_private_base":str(base),"heldout_designs_guest_private":True,"writer_output_count":0,"native_acceptance":False,"sealed_source":sealed_source,"scope":"ordinary two direct shared-circle-child cylinder-face concentric mate; aligned or anti-aligned, free or locked rotation; valid axial slide, unlocked spin and child-depth edit persistence","excluded_scope":["datum-axis/line/circular-edge/conical/spherical endpoints","misaligned or linked concentric mates","invalid-pose correction","locked-spin rejection","generated native writer or public registration"]})
    expected=digest(packet)
    command=[sys.executable,"-B",str(tools/"AuthorConcentricMateSources.py"),"verify",str(packet),"--packet-sha256",expected]
    result=subprocess.run(command,capture_output=True,text=True,check=True,timeout=30)
    require(json.loads(result.stdout)=={"passed":True,"native_processes_started":0,"heldout_inputs_read":0},"the independent host verifier did not qualify the source packet")
    predictions=[{"id":case["id"],"initial":geometry(case),"edited":geometry(case,True),"initial_coaxial_residual":coaxial_residual(case,expected_transforms(case)),"edited_coaxial_residual":coaxial_residual(case,expected_transforms(case,True))} for case in disclosed_cases()]
    write_json(root/"HostPreflight.json",{"passed":True,"native_processes_started":0,"heldout_inputs_read":0,"heldout_designs_created":0,"writer_output_count":0,"source_packet_sha256":expected,"verifier_stdout":json.loads(result.stdout),"python_version":sys.version,"disclosed_analytic_predictions":predictions})
    prefix=["py",args.guest_python,"-B",windows_path(tools/"AuthorConcentricMateSources.py")]
    shared=[windows_path(packet),"--packet-sha256",expected]
    def phase(identifier,name):
        return [*prefix,"run",*shared,"--case-id",identifier,"--phase",name]
    recipe={"schema":SCHEMA,"packet_sha256":expected,"verify":[*prefix,"verify",*shared],"metadata":phase("D00","metadata"),"seal":phase("D00","seal"),"cases":{identifier:{name:phase(identifier,name) for name in ("before","author","reopen-source","reopen-edited","after","lock")} for identifier in SLOTS},"phase_timeout_seconds":480,"trailing_control_timeout_seconds":240,"always_run_after_control_independently":True,"case_failure_stops_later_case_exposure":True,"metadata_must_pass_before_any_native_launch":True,"seal_must_pass_before_any_heldout_author":True,"progress_windows_directory":str(PureWindowsPath(windows_path(packet)).parent/"Progress"),"native_processes_started":0,"heldout_specs_created_on_host":False,"writer_output_count":0,"invalid_pose_correction_is_separate":True,"locked_spin_rejection_is_separate":True}
    write_json(root/"Recipe.json",recipe)
    return {"packet":str(packet),"packet_sha256":expected,"recipe_sha256":digest(root/"Recipe.json"),"host_preflight_sha256":digest(root/"HostPreflight.json"),"tool_hashes":hashes,"native_processes_started":0,"heldout_inputs_read":0,"heldout_designs_created":0,"writer_output_count":0}


def main():
    parser=argparse.ArgumentParser(description="Freeze concentric native source method and disclosed designs before any writer")
    parser.add_argument("output",type=Path)
    parser.add_argument("control",type=Path)
    parser.add_argument("--native-evidence",type=Path,required=True)
    parser.add_argument("--guest-private-base",default=r"C:\KitConcentricSource121")
    parser.add_argument("--guest-python",default="-3.12",choices=("-3.11","-3.12"))
    parser.add_argument("--previous-packet",type=Path)
    parser.add_argument("--previous-packet-sha256")
    args=parser.parse_args()
    print(json.dumps(prepare(args),sort_keys=True))


if __name__=="__main__":
    main()
