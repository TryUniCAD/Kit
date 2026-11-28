from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path,PureWindowsPath
from shutil import copytree
import subprocess
import sys
from tempfile import TemporaryDirectory


def require(condition,message):
    if not condition:raise RuntimeError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n")


def observe(root,expected,run=False):
    command=[sys.executable,"-B",str(root/"Tools/AuthorConcentricMateSources.py"),"run" if run else "verify",str(root/"Source.json"),"--packet-sha256",expected]
    if run:command.extend(("--case-id","H01","--phase","author"))
    process=subprocess.run(command,capture_output=True,text=True,timeout=30)
    require(not process.stderr,"source verifier produced unexpected stderr")
    result=json.loads(process.stdout)
    require(process.returncode in (0,3) and type(result.get("passed")) is bool,"invalid verifier process boundary")
    return {"exit_code":process.returncode,"stdout":result}


def check(packet,expected,output):
    require(not output.exists(),"choose a new protocol receipt")
    require(digest(packet)==expected,"packet identity changed")
    root=packet.parent
    job=json.loads(packet.read_bytes())
    tools=root/"Tools"
    require(len(job["tools_sha256"])==16,"the pinned native tool closure changed")
    for name,wanted in job["tools_sha256"].items():
        require(digest(tools/name)==wanted,"pinned author source changed")
        ast.parse((tools/name).read_bytes(),filename=name)
    recipe=json.loads((root/"Recipe.json").read_bytes())
    require(recipe["packet_sha256"]==expected and set(recipe["cases"])=={"D01","D02","D03","H01","H02"},"source recipe custody changed")
    commands=[recipe["verify"],recipe["metadata"],recipe["seal"],*[row for value in recipe["cases"].values() for row in value.values()]]
    for command in commands:
        require(command[command.index("--packet-sha256")+1]==expected,"a command uses a different source packet")
        require(PureWindowsPath(command[3]).name=="AuthorConcentricMateSources.py" and PureWindowsPath(command[5]).name=="Source.json" and str(PureWindowsPath(command[3]))==command[3] and str(PureWindowsPath(command[5]))==command[5],"guest locators are not canonical Windows paths")
    rows={"unchanged":observe(root,expected),"wrong_packet_digest":observe(root,"0"*64),"host_hidden_phase":observe(root,expected,True)}
    require(rows["unchanged"]["exit_code"]==0 and rows["unchanged"]["stdout"]=={"passed":True,"native_processes_started":0,"heldout_inputs_read":0},"unchanged verifier failed")
    with TemporaryDirectory(prefix="ConcentricProtocolNegatives",dir=root.parent) as temporary:
        base=Path(temporary)
        mutations=("tool","control","binding","disclosed","schema","acceptance","writer_count","sealed_visibility")
        for name in mutations:
            target=base/name
            copytree(root,target)
            source=target/"Source.json"
            changed=json.loads(source.read_bytes())
            if name in ("tool","control","binding","disclosed"):
                file={"tool":target/"Tools/ConcentricSourcePlan.py","control":target/"Control.SLDPRT","binding":target/"NativeBinding.json","disclosed":target/"Disclosed.json"}[name]
                file.write_bytes(file.read_bytes()+b" ")
            elif name=="schema":changed["schema"]="unsupported"
            elif name=="acceptance":changed["native_acceptance"]=True
            elif name=="writer_count":changed["writer_output_count"]=1
            else:changed["heldout_designs_guest_private"]=False
            write_json(source,changed)
            rows[name]=observe(target,digest(source))
    require(all(row["exit_code"]==3 and row["stdout"]["passed"] is False for name,row in rows.items() if name!="unchanged"),"a mutation or host hidden phase was admitted")
    require(not (root/"Progress").exists(),"host protocol validation created native progress")
    require(digest(packet)==expected and all(digest(tools/name)==value for name,value in job["tools_sha256"].items()),"protocol validation mutated frozen inputs")
    result={"schema":"kit.sw2026.concentric-source-host-protocol-check.v1","passed":True,"packet_sha256":expected,"recipe_sha256":digest(root/"Recipe.json"),"native_binding_sha256":digest(root/"NativeBinding.json"),"host_preflight_sha256":digest(root/"HostPreflight.json"),"tool_hashes":job["tools_sha256"],"checked_sources":16,"canonical_guest_commands":len(commands),"process_count":len(rows),"refusals":len(rows)-1,"results":rows,"frozen_inputs_unchanged":True,"native_processes_started":0,"heldout_inputs_read":0,"heldout_designs_created":0,"writer_output_count":0,"python_version":sys.version,"checker_sha256":digest(Path(__file__))}
    write_json(output,result)
    return {"passed":True,"receipt_sha256":digest(output),"process_count":len(rows),"refusals":len(rows)-1,"native_processes_started":0,"heldout_inputs_read":0}


def main():
    parser=argparse.ArgumentParser(description="Exercise the exact concentric source freezer and verifier at fresh host process boundaries")
    parser.add_argument("packet",type=Path)
    parser.add_argument("--packet-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(check(args.packet.resolve(strict=True),args.packet_sha256,args.output),sort_keys=True))


if __name__=="__main__":
    main()
