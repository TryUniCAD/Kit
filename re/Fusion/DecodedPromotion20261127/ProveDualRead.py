import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import traceback

from convert import open_document
from tests.Convert.Integration.Fusion.DualSide.Admission.CheckAdmitDoc import CheckAdmitDoc
from tests.Convert.Integration.Fusion.DualSide.Admission.ReadAdmitCases import ReadAdmitCases
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases

root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();output.mkdir(exist_ok=False)
(output/'Documents').mkdir()
eligible={sample.Identity for sample in ReadAdmitCases()}
report=dict(base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=False,native_calls=0,native_acceptance=False,cases=[])
for sample in ReadDualCases():
    data=sample.Source.read_bytes();assert hashlib.sha256(data).hexdigest()==sample.Digest
    row=dict(source=sample.Source.relative_to(root).as_posix(),sha256=sample.Digest,eligible=sample.Identity in eligible)
    try:
        document=open_document(BytesIO(data),source_format='fusion.f3d',strict=True)
        if row['eligible']:CheckAdmitDoc(document,sample)
        target=output/'Documents'/(sample.Identity+'.json');target.write_text(document.to_json())
        row.update(outcome='decoded',document_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),features=len(document.feature_timeline),parameters=len(document.parameters),volume=document.bodies[0].topology.volume,read_only=document.metadata.get('fusion.read_only'))
    except Exception as error:
        row.update(outcome='rejected',reason=type(error).__name__+': '+str(error))
        if row['eligible']:row['unexpected_traceback']=traceback.format_exc().replace(str(root),'<checkout>')
    report['cases'].append(row)
    (output/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
paths=[root/'src/convert/adapters/Fusion/Native/Parameters/ReadParameters.py',root/'src/convert/adapters/Fusion/Native/Circular/Spans/ProjectSpan.py']
for name in ('DualSides','DualSnapshots'):
    paths.extend(sorted((root/'src/convert/adapters/Fusion/Native/Circular'/name).glob('*.py')))
report['sources']={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
report['summary']={outcome:sum(row['outcome']==outcome for row in report['cases']) for outcome in ('decoded','rejected')}
report['summary']['eligible_rejected']=sum(row['eligible'] and row['outcome']!='decoded' for row in report['cases'])
(output/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary']))
assert report['summary']==dict(decoded=56,rejected=12,eligible_rejected=0)
