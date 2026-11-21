from ast import dump, parse
from hashlib import sha256
from json import loads, dumps
from pathlib import Path
from shutil import copytree
from subprocess import run
import os
import sys

base=Path(r"C:\KitBlankDrawingPublicEval01")
stage=base/"PublicationStyleReplay03"
bind_sha="9c2fc4de170e96b29b01ee1a92f358c495f7d84b3829c0cfc394e6d499df9988"
gen_sha="8ef2fa34d4facecd328178ab0cd106215047b3d097e69b305a36e6d913c695d9"
bundle=Path(sys.argv[1])
pins=sys.argv[2]
assert sha256((bundle/"Pairs.json").read_bytes()).hexdigest()==pins
pairs=loads((bundle/"Pairs.json").read_bytes())
assert len(pairs)==6
def fp(p):
    return sha256(p.read_bytes()).hexdigest()
assert fp(base/"MethodBinding.json")==bind_sha and fp(base/"GenerationFreeze.json")==gen_sha
original=loads((base/"WriterManifest.json").read_bytes())
stage.mkdir()
copytree(base/"src",stage/"src")
revised=dict(original["files"])
rows={}
for name,pair in pairs.items():
    rel=Path(name)
    assert name.startswith("src/") and rel.suffix==".py" and ".." not in rel.parts
    before=(base/rel).read_bytes()
    after=(bundle/rel).read_bytes()
    assert sha256(before).hexdigest()==pair["before_sha256"]==original["files"][name]
    assert sha256(after).hexdigest()==pair["after_sha256"]
    prior=dump(parse(before));current=dump(parse(after))
    assert prior==current
    (stage/rel).write_bytes(after)
    revised[name]=pair["after_sha256"]
    rows[name]={**pair,"exact_ast_sha256":sha256(current.encode()).hexdigest()}
for name,h in revised.items():
    source=(stage if name.startswith("src/") else base)/name
    assert fp(source)==h
manifest=stage/"ReplaySource.json"
m={"schema":"kit.sw2026.blank-writer-style-only-manifest.v1","original_manifest_sha256":fp(base/"WriterManifest.json"),
   "changes":rows,"file_count":len(revised),"files":revised}
with manifest.open("x",encoding="utf-8",newline="\n") as f:
    f.write(dumps(m,indent=2,allow_nan=False)+"\n")
proof=loads((base/"GenerationFreeze.json").read_bytes())
opts=base/"ExplicitOptions.json"
workers={}
for slot,slot_record in proof["slots"].items():
    workspace=base/"Generation"/slot
    neutral=workspace/"Neutral.json"
    row=slot_record["builds"][1]
    dest=Path(row["target_path"])
    assert dest.parent==workspace and not dest.exists()
    report=stage/(slot+".json")
    command=[sys.executable,"-B",str(base/"Tools/BuildPublicBlankDrawing.py"),"--intent",str(neutral),
             "--intent-sha256",fp(neutral),"--options",str(opts),"--options-sha256",fp(opts),"--target",str(dest),
             "--report",str(report),"--route",row["route"],"--epoch",str(row["writer_epoch"]),
             "--block-id",row["block_id"],"--writer-manifest-sha256",fp(manifest)]
    result=run(command,cwd=stage,env={**os.environ,"PYTHONPATH":str(stage/"src"),"PYTHONNOUSERSITE":"1"},
               check=False,capture_output=True,timeout=100)
    if result.returncode:
        with (stage/(slot+".stderr")).open("xb") as s:
            s.write(result.stderr)
        raise ValueError("guarded replay failed")
    review=loads(report.read_bytes())
    assert review["atomic_write_verified"] and review["no_overwrite_verified"] and not review["dropped"]
    assert review["data_file_reads"]==review["native_template_reads"]==review["cad_runtime_calls"]==0
    payload=dest.read_bytes()
    expected=Path(row["output"]["path"]).read_bytes()
    assert payload==expected and fp(dest)==row["output"]["sha256"]
    dest.rename(stage/dest.name)
    workers[slot]={"byte_identical_to_native_measured_file":True,"output_sha256":row["output"]["sha256"],
                   "guard_receipt_sha256":fp(report),"runtime_data_reads":0}
print(dumps({"schema":"kit.sw2026.blank-drawing-source-style-replay.v1","passed":True,
             "verified_manifest_entries":len(revised),"source_manifest_sha256":fp(manifest),
             "source_style_changes":rows,"native_generation_sha256":gen_sha,
             "guards":workers,"native_launches":0},sort_keys=True))
