from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path
from subprocess import run
import sys

LOCK = "ec77426e3a5e4c9f8e95252121bea1c1c2330e496d6d9db07b6286e9e07b5c5b"


def hash_bytes(data):
    return sha256(data).hexdigest()


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def read_exact(path, value):
    data = path.read_bytes()
    require(hash_bytes(data) == value, "disclosed path does not contain its locked artifact")
    return data


def sdk_probe(source, destination, input_hash, intent_path, intent_hash, label):
    from convert import open_document, write_document
    from convert.adapters.registry import AdapterNotFoundError
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange import DrawingNote
    from interchange.serialization.Deserialize import FromData
    from interchange.serialization.EncodeData import ToData

    data = read_exact(source, input_hash)
    wanted = loads(read_exact(intent_path, intent_hash))
    doc = open_document(data, source_format="solidworks.slddrw", strict=False)
    doc.AssertValid()
    sheet, = doc.drawing.Sheets
    note, = sheet.Notes
    require(isinstance(note,DrawingNote) and note.TextValue == wanted[label+"_text"], "public note text differs")
    point = note.PositionValue
    coordinates=(point.XCoord,point.YCoord,point.ZCoord)
    require(all(isclose(a,b,rel_tol=0,abs_tol=1e-15) for a,b in zip(coordinates,wanted[label+"_position"],strict=True)),
            "public note coordinates differ")
    neutral = ToData(doc)
    require(FromData(neutral) == doc and ToData(FromData(neutral)) == neutral, "serializing the drawing loses its note")
    typed_note = neutral["drawing"]["sheets"]["$tuple"][0]["notes"]["$tuple"][0]
    require(typed_note["$type"]=="DrawingNote" and typed_note["text"]==note.TextValue,"portable record lacks the actual note")
    clean_source = replace(doc.source, attributes={})
    clean = replace(doc, source=clean_source, diagnostics=(), metadata={"name":destination.stem})
    blank = replace(clean,drawing=replace(doc.drawing,Sheets=(replace(sheet,Notes=None),)))
    require(SldprtWriter().supports(blank,destination) and not SldprtWriter().supports(clean,destination),
            "blank writer must refuse the note while accepting the same empty sheet")
    try:
        write_document(clean,destination)
    except AdapterNotFoundError:
        pass
    else:
        raise ValueError("blank writer accepted note-bearing content")
    require(not destination.exists() and read_exact(source,input_hash)==data,"source or refused destination changed")
    return {"drawing":neutral["drawing"],"json_round_trip":True,"blank_writer_refused_without_publication":True}


def run_case(script, source, target, record, intent, case, stage):
    key = stage+"_sha256"
    digest = record[key]
    read_exact(source,digest)
    metadata = [str(source),str(target),digest,str(intent),record["intent_sha256"],"initial" if stage=="original" else "edited"]
    worker = run([sys.executable,"-B",str(script),"worker",*metadata],capture_output=True,text=True,check=True,timeout=120)
    sdk = loads(worker.stdout)
    arguments=[sys.executable,"-B","-m","KitCli","decode",str(source)]
    cli = run(arguments+["--partial"],capture_output=True,text=True,check=True,timeout=120)
    decoded = loads(cli.stdout)
    require(decoded["partial"] is True and decoded["layer"]=="neutral"
            and sdk["drawing"] == decoded["document"]["drawing"], "normal SDK and CLI notes differ")
    strict = run(arguments,capture_output=True,text=True,timeout=120)
    require(strict.returncode != 0 and "strict generated blank drawing is unsupported" in strict.stderr,
            "strict CLI unexpectedly accepted the partial note source")
    return {
        "case":case,"stage":stage,"source_sha256":digest,"semantic_drawing_sha256":hash_bytes(dumps(sdk["drawing"],sort_keys=True).encode()),
        "normal_sdk_partial_passed":True,"normal_cli_partial_passed":True,"normal_cli_strict_rejected":True,
        "blank_writer_refused_before_publication":sdk["blank_writer_refused_without_publication"],
        "neutral_json_round_trip":sdk["json_round_trip"],"source_preserved":hash_bytes(source.read_bytes())==digest,
    }


def check(args):
    current=Path(__file__).resolve()
    lock = loads(read_exact(args.source_lock,LOCK))
    require(lock["passed"] and lock["distinct_passing_processes"]==14,"source authority changed")
    approved={name:entry for name,entry in lock["source_cases"].items() if entry["private"] is False}
    require(set(approved)=={"Disclosed01","Disclosed02"},"expected the two disclosed and no private sources")
    output=args.output_directory
    output.mkdir()
    rows=[]
    for name,record in sorted(approved.items()):
        for stage,tail in (("original",""),("edited","Edit")):
            directory=args.disclosed_sources_directory/name
            source=directory/(name+tail+".SLDDRW")
            target=output/("Refused"+name+tail+".SLDDRW")
            rows.append(run_case(current,source,target,record,directory/"Intent.json",name,stage))
    report={"schema":"kit.sw2026.plain-note-public-read-process.v1","source_lock_sha256":LOCK,"processes":3*len(rows),
            "passed":len(rows)==4,"heldout_inputs_read":0,"native_processes":0,"public_note_writer_enabled":False,"rows":rows}
    (output/"Result.json").write_bytes((dumps(report,sort_keys=True,indent=2)+"\n").encode())
    print(dumps({"passed":report["passed"],"processes":report["processes"]}))


def main():
    if len(sys.argv)>1 and sys.argv[1]=="worker":
        source,destination,input_hash,intent,intent_hash,label=sys.argv[2:]
        print(dumps(sdk_probe(Path(source),Path(destination),input_hash,Path(intent),intent_hash,label),sort_keys=True))
        return
    parser=ArgumentParser()
    parser.add_argument("--source-lock",type=Path,required=True)
    parser.add_argument("--disclosed-sources-directory",type=Path,required=True)
    parser.add_argument("--output-directory",type=Path,required=True)
    check(parser.parse_args())


if __name__=="__main__":
    main()
