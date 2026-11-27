from pathlib import Path
import hashlib
import json
import sys
import traceback

from Generate import generate
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed

output=Path(sys.argv[1]);output.mkdir(exist_ok=False)
base=(13.,17.,29.,7.)
cases=[('baseline',base)]
for axis,values in [(0,(7.1,19.7)),(1,(3.7,61.3)),(2,(5.9,53.1)),(3,(-41.9,0.,1e-6,83.7))]:
    for value in values:
        row=list(base);row[axis]=value;cases.append(('axis'+str(axis)+'-'+str(value),tuple(row)))
cases.extend([('holdout_a',(11.3,23.9,37.7,-13.1)),('holdout_b',(29.3,13.7,47.9,61.1))])
reads=[];active=False;root=Path(__file__).resolve().parents[3]
def audit(event,args):
    if not active or event!='open' or not isinstance(args[0],str):return
    path=Path(args[0]).resolve();flags=args[2]
    if flags&3:return
    if path.is_relative_to(root/'src') or path.is_relative_to(Path(sys.base_prefix)) or path.suffix in ('.py','.pyc','.so','.dylib'):
        reads.append(str(path));return
    raise RuntimeError('writer attempted non grammar input read: '+str(path))
sys.addaudithook(audit)
results=[]
for name,values in cases:
    row=dict(case=name,values_mm=values,holdout=name.startswith('holdout'),vendor_loadable=False,application_usable=False)
    try:
        active=True
        try:raw=generate(*values)
        finally:active=False
        path=output/(name+'.f3d');path.write_bytes(raw);model=ReadDocument(raw)
        row.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),typed_roundtrip=ReadDocument(EmitParsed(model))==model)
    except Exception:row['error']=traceback.format_exc()
    results.append(row)
report=dict(generator_sha256=hashlib.sha256(Path(__file__).with_name('Generate.py').read_bytes()).hexdigest(),sdk_revision='91a73de348894a5791a51b977cd6fe0fe677a617',models=False,native_acceptance='not_run_transport_unavailable',files=len(results),passed=sum(row.get('typed_roundtrip',False) for row in results),cases=results,writer_reads=sorted(set(reads)))
(output/'Results.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('cases','writer_reads')}));assert report['passed']==report['files']
