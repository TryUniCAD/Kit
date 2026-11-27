import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path(sys.argv[1]).resolve();previous=Path(sys.argv[2]).resolve();output=Path(sys.argv[3]).resolve()
receipt=json.loads((root/'re/Fusion/DecodedPromotion20261127/DualAdmissionPublic/ReadReceipt.json').read_text())
rows=[row for row in receipt['cases'] if row['outcome']=='decoded']
paths=[str(root/row['source']) for row in rows]
program="from io import BytesIO; import hashlib,json,sys; from pathlib import Path; from convert import open_document; print(json.dumps([hashlib.sha256(open_document(BytesIO(Path(p).read_bytes()),source_format='fusion.f3d').to_json().encode()).hexdigest() for p in sys.argv[1:]]))"
results=[]
for sdk in (previous,root):
    environment=dict(os.environ);environment['PYTHONPATH']=str(sdk/'src')
    result=subprocess.run([sys.executable,'-c',program,*paths],cwd=sdk,env=environment,capture_output=True,text=True,timeout=180,check=True);results.append(json.loads(result.stdout))
comparisons=[dict(source=row['source'],sha256=row['sha256'],previous_document=first,current_document=second,equal=first==second) for row,first,second in zip(rows,*results,strict=True)]
report=dict(previous_sdk=subprocess.check_output(['git','rev-parse','HEAD'],cwd=previous,text=True).strip(),models=False,native_calls=0,rows=comparisons,passed=sum(row['equal'] for row in comparisons))
output.write_text(json.dumps(report,indent=2)+'\n')
if len(comparisons)!=56 or not all(row['equal'] for row in comparisons):raise ValueError('existing XY source documents changed')
print('all fifty six earlier XY document hashes unchanged')
