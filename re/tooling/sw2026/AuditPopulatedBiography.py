from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys

root=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(root),str(root/"src")]

from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(payload):
    return sha256(payload).hexdigest()


def read_locked(path, expected):
    payload=path.read_bytes()
    assert digest(payload)==expected,path.name
    return payload


def inspect_records(graph):
    records=graph.RootValue.FieldsValue["records"]
    assert len(records)==graph.RootValue.FieldsValue["n"]
    assert len(graph.MapValue.EntriesValue)==2
    for row in records:
        record=row["r"]
        assert tuple(record)==("f08","f0c","f10","f14","f18","f1c","f20","f24","f28","f30","f38","f40","fe8")
        for name in ("f40","fe8"):
            station=record[name]
            assert tuple(station)==("f08","f0c","f10")+tuple(
                f"{prefix}{index}" for index in range(6) for prefix in ("s","l","a","b"))
    return len(records)


def main():
    parser=ArgumentParser(description="Audit saved Biography and History bytes without reporting telemetry values")
    parser.add_argument("--cohort",type=Path,required=True)
    parser.add_argument("--native-layout",type=Path,required=True)
    parser.add_argument("--compatibility-result",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    cohort_sha="5b490f035ff90e05e3772572754350c0b2b5d836961d64467915a0286038e811"
    compat_sha="5f8bd673c37893079e24e649199db63f48a71dbbc17a4c7cebe0a104df172a6b"
    cohort=json.loads(read_locked(args.cohort,cohort_sha))
    compat=json.loads(read_locked(args.compatibility_result,compat_sha))
    assert compat["passed"] and compat["guarded_workers"]==21
    static_raw=args.native_layout.read_bytes()
    static=json.loads(static_raw)
    assert static["image_sha256"]=="569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
    facts={}
    for label,span in zip(("Root","BiographyRecord","StartEndRecord"),
                          (("0x4c71ec40","0x4c71f5a6"),("0x4c71ea50","0x4c71ec3e"),("0x4c71f700","0x4c71fb6b")),strict=True):
        row=static["ranges"][label]
        assert (row["virtual_start"],row["end_exclusive"])==span
        facts[label]={key:row[key] for key in ("virtual_start","end_exclusive","byte_sha256","instruction_lines")}
    bio_name="_MO_VERSION_19000/Biography"
    history_name="_MO_VERSION_19000/History"
    cases=[]
    for case in cohort["cases"]:
        archive=SldprtArchive.from_bytes(read_locked(Path(case["file"]),case["file_sha256"]))
        files={}
        for name in (bio_name,history_name):
            data=archive.require(name)
            known=case["streams"][name]
            assert len(data)==known["bytes"] and digest(data)==known["sha256"] and known["research_roundtrip"]
            graph=ReadHistMut(data,19000)
            again,replayed=WriteHistMut(graph.RootValue,19000)
            assert again==data and replayed.MapValue==graph.MapValue
            count=inspect_records(graph) if name==bio_name else graph.RootValue.FieldsValue["n"]
            if name==bio_name:
                if count:
                    assert known["original_sdk_diagnostic"]
                    populated=data
                else:
                    assert not known["original_sdk_diagnostic"]
                    fresh=data
                graph.RootValue.FieldsValue["n"]=count+1
                normalized,_=WriteHistMut(graph.RootValue,19000)
                assert normalized==data
            files[name]={"bytes":len(data),"sha256":digest(data),"rows":count,"byte_identity":True,
                         "map_entries":len(graph.MapValue.EntriesValue)}
        cases.append({"case":case["label"],"format":case["document_type"],
                      "source_sha256":case["file_sha256"],"streams":files})
    faults=[]
    for label,data,version in (
        ("negative-biography-count",fresh[:-4]+pack("<i",-1),19000),
        ("truncated-embedded-record",populated[:-1],19000),
        ("undeclared-archive-version",populated,18000),
    ):
        try:
            ReadHistMut(data,version)
        except (ValueError,EOFError) as error:
            faults.append({"fault":label,"error":type(error).__name__})
        else:
            raise ValueError("unexpected biography input passed: "+label)
    receipt={"schema":"kit.sw2026.saved-biography-sdk-roundtrip.v1","passed":True,
             "cohort_sha256":cohort_sha,"existing_generator_replay_sha256":compat_sha,
             "binary_layout_observation_sha256":digest(static_raw),"binary_image_sha256":static["image_sha256"],
             "native_serializer_ranges":facts,"case_count":len(cases),"exact_metadata_streams":2*len(cases),
             "populated_biography_cases":sum(case["streams"][bio_name]["rows"]>0 for case in cases),
             "cases":cases,"expected_rejections":faults,"hidden_inputs_read":0}
    capture=(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    with args.output.open("xb") as file:
        file.write(capture)
    print(json.dumps({"passed":True,"streams":receipt["exact_metadata_streams"],"faults":len(faults),
                      "result_sha256":digest(capture)}))


if __name__=="__main__":
    main()
