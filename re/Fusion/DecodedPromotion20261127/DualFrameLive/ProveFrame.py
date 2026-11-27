import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

from FrameProof import read_frame, local_view, restore_view
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualOwners import ReadDualOwners
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualCover import CheckDualCover
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualGeo import CheckDualGeo
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualRims import CheckDualRims
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualTags import CheckDualTags
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLinks import CheckDualLinks
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualParams import ReadDualParams
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();case_name=sys.argv[3]
output.mkdir(parents=True,exist_ok=False);(output/'Documents').mkdir()
folder=Path(__file__).parent
capture_path=root/'re/Fusion/TwoSidedDraft20261127/Capture.json';capture=json.loads(capture_path.read_text())
case=next(c for c in capture['cases'] if c['id']==case_name);readings={r['stage']:r['value'] for r in case['observations']}
names=('ReadDualLive','ReadDualOwners','CheckDualCover','CheckDualGeo','CheckDualRims','CheckDualTags','CheckDualLinks')
source_files=[root/'src/convert/adapters/Fusion/Native/Circular/DualSides'/(n+'.py') for n in names]
report=dict(case=case_name,base_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=False,native_api_calls=0,rules_sha256=hashlib.sha256((folder/'Rules.md').read_bytes()).hexdigest(),frame_proof_sha256=hashlib.sha256((folder/'FrameProof.py').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),capture_sha256=hashlib.sha256(capture_path.read_bytes()).hexdigest(),validator_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},rows=[])
for archive in case['archives']:
    path=root/'re/Fusion/TwoSidedDraft20261127/Native'/archive['file'];row=dict(source=str(path.relative_to(root)),sha256=archive['sha256'],checks=[])
    try:
        raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==archive['sha256']
        model=ReadDocument(raw);graph=BuildGraph(model);context=SelectExtrusion(graph);shape=ReadCircle(graph,context)
        frame,graph_checks,values=read_frame(graph,context,model);row['checks'].extend(graph_checks)
        suffix=path.stem.removeprefix(case_name);stage='restore_draft_second' if suffix=='_restored' else suffix.lstrip('_') or 'baseline';actual=readings[stage]
        for index,(value,wanted) in enumerate(zip(values,actual['profile']['transform'],strict=True)):
            row['checks'].append(dict(field='api_matrix_'+str(index),actual=value,expected=wanted,passed=value==wanted))
        parameters=ReadDualParams(graph,context);roles={p.attributes['native_name']:p for p in parameters}
        first=roles['AlongDistance'].value.value;second=roles['AgainstDistance'].value.value;a=roles['TaperAngle'].value.value;b=roles['Side2TaperAngle'].value.value
        state=ReadDualLive(model.Bodies[0].History,context.Extrude.Fields['endModelHS'])
        view,metadata=local_view(state,frame)
        CheckDualCover(view);CheckDualGeo(view,shape,first,second,a,b);CheckDualRims(view,shape,first,second,a,b)
        ops,primary=ReadDualOwners(graph,context,model,shape,view);CheckDualTags(view,shape,ops,primary,first,second);CheckDualLinks(view,shape,first,second)
        row['checks'].append(dict(field='all_local_live_geometry_tags_and_attributes',passed=True))
        restored=restore_view(view,frame,metadata)
        row['checks'].append(dict(field='complete_typed_world_state_restoration',passed=restored==state))
        row['checks'].append(dict(field='original_world_state_retained',passed=ReadDualLive(model.Bodies[0].History,context.Extrude.Fields['endModelHS'])==state))
        row['documents']={}
        for role,value in [('World',state),('Local',view),('Restored',restored),('Placement',metadata)]:
            doc=output/'Documents'/(path.stem+'_'+role+'.json');doc.write_text(json.dumps(EncodeState(value),indent=2,sort_keys=True));row['documents'][str(doc.relative_to(output))]=hashlib.sha256(doc.read_bytes()).hexdigest()
        row.update(passed=all(c['passed'] for c in row['checks']),world_entities=len(state.Entities),local_entities=len(view.Entities),operations=ops)
    except Exception:
        row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'))
    report['rows'].append(row)
report['summary']=dict(files=len(report['rows']),passed=sum(r['passed'] for r in report['rows']),comparisons=sum(len(r['checks']) for r in report['rows']),failed=sum(not c['passed'] for r in report['rows'] for c in r['checks']),errors=sum('error' in r for r in report['rows']))
(output/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True));print(json.dumps(report['summary'],indent=2))
