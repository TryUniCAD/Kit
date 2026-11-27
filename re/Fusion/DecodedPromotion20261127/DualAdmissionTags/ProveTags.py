import dataclasses
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

from convert import open_document
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import CheckDualLive
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ChangeTagModel import ChangeTagModel
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample


root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();output.mkdir(parents=True,exist_ok=False)
(output/'Documents').mkdir();(output/'Counterexamples').mkdir()
names=('CheckDualLive','CheckDualGeo','CheckDualLinks','CheckDualCover','CheckDualRims','CheckDualTags','ReadDualLive','ReadDualOwners','ReadDualLabel')
sources=[*(root/'src/convert/adapters/Fusion/Native/Circular/DualSides'/(name+'.py') for name in names),*sorted((root/'tests/Convert/Integration/Fusion/DualSide/Tags').glob('*.py'))]
report=dict(sdk_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=False,native_api_calls=0,validator_source_files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rules_sha256=hashlib.sha256((Path(__file__).parent/'Rules.md').read_bytes()).hexdigest(),sources=[],counterexamples=[])
samples=ReadDualCases()
for sample in samples:
    expected='control' if sample.FirstTaper==sample.SecondTaper==0 else 'accepted' if sample.Frame.z_axis.z==1.0 else 'rejected'
    row=dict(source=str(sample.Source.relative_to(root)),sha256=sample.Digest,expected=expected,holdout=sample.Identity.startswith('holdout'))
    try:
        model,graph,context,shape=ReadTagSample(sample)
        try:
            state=CheckDualLive(graph,context,model,shape,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)
            row.update(outcome='accepted',live_entities=len(state.Entities))
            path=output/'Documents'/(sample.Identity+'.json');path.write_text(json.dumps(EncodeState(state),indent=2,sort_keys=True))
            row.update(document=str(path.relative_to(output)),document_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        except ValueError as error:
            row.update(outcome='rejected',reason=str(error))
        if expected=='control':
            doc=open_document(sample.Source);row['control_reader_pass']=len(doc.bodies)==1 and not doc.diagnostics
        row['passed']=row['outcome']==expected if expected!='control' else row['outcome']=='rejected' and row['control_reader_pass']
    except Exception:
        row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'))
    report['sources'].append(row)
sample=next(s for s in samples if s.Identity=='baseline')
model,*_=ReadTagSample(sample)
cases=('side_operation','joint_missing','joint_reversed','joint_label','body_secondary','body_operation','cap_label','rim_label','attribute_chain','extended_tag','sketch_owner','sketch_circle','time_value','body_uuid','history_end','allocator_owner')
for case in cases:
    row=dict(case=case)
    try:
        changed=ChangeTagModel(model,sample,case);raw=EmitParsed(changed)
        path=output/'Counterexamples'/(case+'.f3d');path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
        row.update(file=str(path.relative_to(output)),sha256=digest,serialized=True)
        altered=dataclasses.replace(sample,Source=path,Digest=digest)
        try:
            changed,graph,context,shape=ReadTagSample(altered)
            row['typed_read']=True
            CheckDualLive(graph,context,changed,shape,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)
            row['passed']=False
        except ValueError as error:
            row.update(passed=True,reason=str(error),rejection_stage='live validator' if row.get('typed_read') else 'typed reader')
    except Exception:
        row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'))
    report['counterexamples'].append(row)
report['summary']=dict(sources=len(report['sources']),drafted_xy_accepts=sum(r.get('outcome')=='accepted' for r in report['sources']),xz_refusals=sum(r.get('outcome')=='rejected' and r['expected']=='rejected' for r in report['sources']),healthy_controls=sum(r.get('control_reader_pass',False) for r in report['sources']),source_passes=sum(r['passed'] for r in report['sources']),counterexamples=len(report['counterexamples']),serialized_counterexamples=sum(r.get('serialized',False) for r in report['counterexamples']),counterexample_passes=sum(r['passed'] for r in report['counterexamples']))
(output/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True));print(json.dumps(report['summary'],indent=2))
