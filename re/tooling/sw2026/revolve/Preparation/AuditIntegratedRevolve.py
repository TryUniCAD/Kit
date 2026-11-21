from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from subprocess import run
import sys

repo=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(repo),str(repo/"src")]

from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
from interchange.document.Behavior.DocumentIo import FromJson,ToJson
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve
from RevolveStreamAudit02 import stream_audit


def digest(raw):
    return sha256(raw).hexdigest()


def build_case(out,case):
    label,request,rejected=case
    tool=Path(__file__).with_name("AuditRevPrep01.py")
    encoded=json.dumps(request,sort_keys=True,allow_nan=False).encode()
    (out/(label+".request.json")).write_bytes(encoded)
    receipt=run([sys.executable,"-I","-B",str(tool),"--sdk",str(repo)],input=encoded,capture_output=True,timeout=90)
    (out/(label+".stdout")).write_bytes(receipt.stdout)
    (out/(label+".stderr")).write_bytes(receipt.stderr)
    assert receipt.returncode==0 and not receipt.stderr,label
    state=json.loads(receipt.stdout)
    assert state["passed"] and state["rejected"]==rejected and not state["runtime_external_attempts"]
    assert state["heldout_inputs_read"]==state["native_processes"]==0
    assert all(Path(module).is_relative_to(repo/"src") for module in state["sdk_modules"])
    state.pop("sdk_modules")
    state.pop("actual_self_path",None)
    if not rejected:
        assert state["sha256"]==request["sha256"]
    return {"case":label,"request_sha256":digest(encoded),**state}


def read_case(row):
    path=Path(row["path"])
    raw=path.read_bytes()
    assert digest(raw)==row["sha256"]
    archive=SldprtArchive.from_bytes(raw)
    link=ReadNativeLink(archive,0)
    (owner,)=ReadRevOwners(link)
    expected=row["expected"]
    assert isclose(owner.AngleValue.RadiansValue,expected["angle_rad"],rel_tol=1e-12,abs_tol=1e-14)
    assert owner.IsReverse==expected["reverse"]
    body_streams,metadata=stream_audit(archive,link)
    assert len(body_streams)==8 and len(metadata)==2 and all(value["qualified"] for value in metadata.values())
    modes=(
        ("default",{},True),
        ("semantic",{"include_brep":False,"include_tessellation":False},False),
        ("brep",{"include_brep":True,"include_tessellation":False},True),
        ("tessellation",{"include_brep":False,"include_tessellation":True},False),
        ("both",{"include_brep":True,"include_tessellation":True},True),
    )
    for label,options,geometry in modes:
        document=open_document(raw,source_format="solidworks.sldprt",strict=True,**options)
        assert not document.validate(),(row["name"],label)
        assert (document.brep is not None)==geometry
        assert bool(document.brep_payloads)==(geometry and row["has_native_payload"])
        (feature,)=tuple(value for value in document.feature_timeline if isinstance(value.definition,AngularRevolve))
        assert len(feature.parameter_ids)==len(feature.selection_ids)==1
        assert feature.attributes["native_reverse_direction"]==expected["reverse"]
        encoded=ToJson(document)
        assert ToJson(FromJson(CadDocument,encoded))==encoded
    assert digest(path.read_bytes())==row["sha256"]
    return {"case":row["name"],"role":row["role"],"input_sha256":row["sha256"],
            "reader_modes":len(modes),"exact_streams":len(body_streams)+len(metadata),
            "streams":body_streams|metadata}


def main():
    parser=ArgumentParser(description="Verify ordinary revolve preparation and the integrated cache-free and metadata readers")
    parser.add_argument("--inputs",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    source=args.inputs.read_bytes()
    assert digest(source)=="ed2dd83b79191a3b50c6f597f49a441e001b33459fe9d65284e8d86dd81dc3ad"
    inputs=json.loads(source)
    assert inputs["heldout_inputs_read"]==0
    args.output.mkdir()
    variants=("configuration","unknown_option","unnamed_stream","wrong_suffix","wrong_basename","wrong_format","bad_epoch","wrong_stream_final")
    requests=[("prepared-"+str(index),row,False) for index,row in enumerate(inputs["generated_requests"])]
    requests.extend((variant,inputs["generated_requests"][1]|{"variant":variant},True) for variant in variants)
    with ThreadPoolExecutor(max_workers=4) as pool:
        proofs=list(pool.map(lambda row:build_case(args.output,row),requests))
    readers=[read_case(row) for row in inputs["reader_fixtures"]]
    result={"schema":"kit.sw2026.integrated-revolve-preparation-readback.v1","passed":True,
            "input_sha256":digest(source),"method_sha256":digest(Path(__file__).read_bytes()),
            "lifecycle_sha256":inputs["lifecycle_adjudication_sha256"],"fresh_guarded_workers":len(proofs),
            "reader_modes":sum(row["reader_modes"] for row in readers),
            "exact_streams":sum(row["exact_streams"] for row in readers),
            "prepared_cases":proofs,"reader_cases":readers,"native_processes":0,"heldout_inputs_read":0}
    capture=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    (args.output/"Result.json").write_bytes(capture)
    print(json.dumps({"passed":True,"workers":len(proofs),"modes":result["reader_modes"],
                      "exact_streams":result["exact_streams"],"result_sha256":digest(capture)}))


if __name__=="__main__":
    main()
