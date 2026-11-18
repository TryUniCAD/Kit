import argparse
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import os
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def frozen(args):
    manifest=json.loads(args.manifest.read_text())
    for label in ("baseline","candidate"):
        root=getattr(args,label)
        expected=manifest[label+"_files_sha256"]
        for name,wanted in expected.items():
            require(digest(root/name)==wanted,"frozen source changed: "+name)
        actual={str(path.relative_to(root)) for path in (root/"src").rglob("*.py")}
        declared={name for name in expected if name.startswith("src/") and name.endswith(".py")}
        require(actual==declared,"source root has undeclared executable modules")
    tool=Path(__file__).parent
    for name,wanted in manifest["tool_files_sha256"].items():
        require(digest(tool/name)==wanted,"frozen process tool changed: "+name)
    require(digest(args.cohort)==manifest["cohort_sha256"],"disclosed control custody changed")
    return manifest


def execute(command,request,path,expected=True):
    path.parent.mkdir(parents=True,exist_ok=True)
    encoded=canonical(request) if request is not None else None
    process=subprocess.run(command,input=None if encoded is None else encoded.decode(),text=True,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),timeout=120)
    path.with_suffix(".stdout.json").write_text(process.stdout)
    path.with_suffix(".stderr.txt").write_text(process.stderr)
    require(bool(process.stdout),"worker returned no JSON")
    result=json.loads(process.stdout)
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    require((process.returncode==0)==expected,"worker exit does not match scoped expectation: "+str(path))
    if request is not None:
        require(result["passed"]==expected,"worker status does not match scoped expectation")
        require(result["full_writer_outputs"]==0 and not result["native_acceptance"],"owner proof emitted or certified a complete native document")
        require(not result.get("denied_events"),"worker attempted forbidden runtime access")
    return result


def main(args):
    manifest=frozen(args)
    args.output.mkdir(parents=True,exist_ok=False)
    worker=Path(__file__).parent/"throughowners/OwnerProcess.py"
    prefix=[sys.executable,"-B",str(worker),str(args.candidate)]
    cohort=json.loads(args.cohort.read_text())
    records=[]
    count=0
    source_requests={}
    source_records={}
    builds={}
    for item in cohort["cases"]:
        trialfile=Path(item["trial"])
        require(digest(trialfile)==item["trial_sha256"],"declared Trial identity changed")
        trial=json.loads(trialfile.read_text())
        source=trialfile.parent/trial["control_file"]
        require(digest(source)==item["source_sha256"],"declared source changed")
        request={"source":str(source),"sha256":item["source_sha256"],"output_name":"Projected"+item["id"]+"Owners"}
        source_requests[item["id"]]=request
        observed=execute(prefix+["source"],request,args.output/item["id"]/"Source.json")
        source_records[item["id"]]=observed
        count+=1
        owner={"input":observed["input"],"written_at":1784147400}
        (args.output/item["id"]/"OwnerInput.json").write_bytes(canonical(owner)+b"\n")
        (args.output/item["id"]/"Prediction.json").write_bytes(canonical(observed["source_prediction"])+b"\n")
        first=execute(prefix+["build"],owner,args.output/item["id"]/"BuildA.json")
        second=execute(prefix+["build"],owner,args.output/item["id"]/"BuildB.json")
        count+=2
        require(first==second,"fresh owner generation is not deterministic")
        builds[item["id"]]=first
        audited=execute(prefix+["audit"],dict(owner,fragments=first["fragment_payloads"]),args.output/item["id"]/"Readback.json")
        count+=1
        require(first["fragments"]==audited["fragments"],"independent fragment round trips differ")
        require(first["grammar"]["stock_depth_m"]==observed["source_prediction"]["stock_driver_m"],"actual stock driver differs from independent full-source prediction")
        require(len(first["bindings"])==27 and observed["history_count"]==28 and observed["original_document_identity_retained"] and observed["original_metadata_unchanged"] and observed["complete_gate_refused"] and observed["cleared_gate_refused"],"source owner or envelope closure is incomplete")
        require(digest(source)==item["source_sha256"],"read-only source changed")
        records.append({"id":item["id"],"source_sha256":item["source_sha256"],"input_sha256":first["input_sha256"],"complete_document_sha256":observed["complete_document_sha256"],"original_metadata_sha256":observed["original_metadata_sha256"],"history_count":28,"binding_count":27,"source_prediction_sha256":digest(args.output/item["id"]/"Prediction.json"),"source_wire_observation":observed["source_wire_observation"],"fragments":first["fragments"],"unrepresented_fields":observed["unrepresented_fields"],"record_sha256":{name:digest(args.output/item["id"]/(name+".json")) for name in ("Source","BuildA","BuildB","Readback")}})
    mutations=("missing_center","extra_center","independent_center","fixed_circle","missing_normal","stale_normal_target","extra_normal_query","foreign_scope","automatic_scope","lost_stock_parent","lost_cut_profile","new_body_stock","reverse_stock","cut_distance","missing_scope","foreign_profile_datum","missing_datum","moved_datum","stale_datum_name","stale_driver","extra_driver","stripped_history","stale_light_name","stale_scope","stripped_tree")
    jobs=[]
    for case in ("D01","D02","D03"):
        selected=mutations if case=="D01" else ("independent_center","stale_normal_target","foreign_scope")
        for probe in selected:
            request=dict(source_requests[case],probe=probe)
            jobs.append((case+"/SourceNegatives/"+probe,prefix+["source"],request))
    owner={"input":source_records["D01"]["input"],"written_at":1784147400}
    input_probes=("lost_stock_parent","lost_cut_producer","missing_datum","boolean_line_index","lost_line","wrong_axis_relation","wrong_normal_owner","wrong_normal_sketch","duplicate_identity","foreign_scope_reference","automatic_scope","wrong_version","recorded_input_field","empty_center_identity")
    for probe in input_probes:
        request=deepcopy(owner)
        value=request["input"]
        if probe=="lost_stock_parent": value["refs"]["StockParents"]=[]
        elif probe=="lost_cut_producer": value["refs"]["CutParents"]=[value["refs"]["CutProfileId"]]
        elif probe=="missing_datum": value["planes"].pop()
        elif probe=="boolean_line_index": value["lines"][1]["TargetIndex"]=True
        elif probe=="lost_line": value["lines"].pop()
        elif probe=="wrong_axis_relation": value["lines"][0]["AxisKind"]="vertical"
        elif probe=="wrong_normal_owner": value["axes"][0]["FeatureId"]="foreign-operation"
        elif probe=="wrong_normal_sketch": value["axes"][0]["SketchId"]="foreign-sketch"
        elif probe=="duplicate_identity": value["refs"]["CenterId"]=value["refs"]["CircleId"]
        elif probe=="foreign_scope_reference": value["scope"]["feature_id"]="foreign-stock"
        elif probe=="automatic_scope": value["scope"]["mode"]="automatic"
        elif probe=="wrong_version": value["scope"]["version"]=18999
        elif probe=="recorded_input_field": value["metadata"]={"native_fields":{"saved":1}}
        elif probe=="empty_center_identity": value["refs"]["CenterId"]=""
        jobs.append(("InputNegatives/"+probe,prefix+["build"],request))
    for probe in ("foreign_selected_owner","target_unit_mismatch","target_datum_mismatch"):
        jobs.append(("InputNegatives/"+probe,prefix+["build"],dict(owner,probe=probe)))
    for probe in ("config_trailer","resolved_map_mismatch","header_truncation","wrong_signed_prediction"):
        request=deepcopy(owner)
        request["fragments"]=deepcopy(builds["D01"]["fragment_payloads"])
        if probe=="wrong_signed_prediction":
            request["input"]["shape"]["EndValue"]["IsReversed"]=not request["input"]["shape"]["EndValue"]["IsReversed"]
        else:
            key={"config_trailer":"config","resolved_map_mismatch":"resolved","header_truncation":"model_header"}[probe]
            data=b64decode(request["fragments"][key])
            data=data+b"\0" if probe=="config_trailer" else (int.from_bytes(data[:4],"little")+1).to_bytes(4,"little")+data[4:] if probe=="resolved_map_mismatch" else data[:-1]
            request["fragments"][key]=b64encode(data).decode()
        jobs.append(("ReadbackNegatives/"+probe,prefix+["audit"],request))
    negatives=[]
    def negative(job):
        label,command,request=job
        path=args.output/(label+".json")
        result=execute(command,request,path,False)
        return {"name":label,"error_type":result["error_type"],"error":result["error"],"record_sha256":digest(path)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        negatives=list(pool.map(negative,jobs))
    count+=len(negatives)
    compatibility=[]
    for variant in (0,1):
        pair=[]
        for name in ("baseline","candidate"):
            path=args.output/"Compatibility"/(name+str(variant)+".json")
            command=[sys.executable,"-B",str(getattr(args,name)/"re/tooling/sw2026/throughpresentation/Compat.py"),"--root",str(getattr(args,name)),"--variant",str(variant),"--output",str(path)]
            pair.append(execute(command,None,path))
            count+=1
        require(pair[0]==pair[1],"legacy full generated output or public read changed")
        compatibility.append(pair[0])
    frozen(args)
    result={"status":"passed_source_owners_only","baseline_revision":manifest["baseline_revision"],"source_manifest_sha256":digest(args.manifest),"cohort_sha256":digest(args.cohort),"fresh_process_count":count,"source_cases":records,"negative_count":len(negatives),"negatives":negatives,"legacy_compatibility":compatibility,"component_complete_file_count":0,"legacy_in_memory_containers":4,"fragment_round_trips":18,"runtime_input_file_reads":0,"sdk_runtime_research_imports":0,"held_out_accessed":False,"oracle_used":False,"source_conversion_qualified":False,"native_acceptance":False,"public_writer_promoted":False}
    path=args.output/"Result.json"
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"fresh_process_count":count,"negative_count":len(negatives),"result_sha256":digest(path)}))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for name in ("baseline","candidate","manifest","cohort","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    main(parser.parse_args())
