import hashlib
import json
from pathlib import Path
import subprocess
import sys

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.State.EncodeState import EncodeState


root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]);case_name=sys.argv[3]
if output.exists():raise ValueError('output must be unused')
capture_path=root/'re/Fusion/TwoSidedDraft20261127/Capture.json'
capture=json.loads(capture_path.read_text());case=next(c for c in capture['cases'] if c['id']==case_name)
observations={o['stage']:o['value'] for o in case['observations']};rows=[]
for archive in case['archives']:
    path=root/'re/Fusion/TwoSidedDraft20261127/Native'/archive['file'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==archive['sha256']
    model=ReadDocument(raw);graph=BuildGraph(model);context=SelectExtrusion(graph)
    matrix=ResolveField(graph,context.SketchFeature,'rSketchPlaneMatrix','DRMatrix')
    refs=LinkedNodes(graph,matrix,'dataRefs');assert len(refs)==1
    reference=refs[0];recipe=ResolveField(graph,reference,'rRecipe','EntityRecipe');datum=graph.ResolveId(recipe.Fields['m_entityId'])
    origin=ResolveField(graph,context.Component,'m_rOriginWorkGeometry','OriginWorkGeometry')
    nodes={'ucs':context.Plane,'sketch':context.Sketch,'matrix':matrix,'reference':reference,'recipe':recipe,'datum':datum,'origin':origin,'extrusion':context.Extrude,'instance':graph.OneClass('ComponentInstance')}
    subset={'ucs':('rParent','transform'),'sketch':('UCS','rDcNode','rParent','occurrenceTransform'),'extrusion':('profileNormal','rParent'),'instance':('rTargetComponent','transform','rParent'),'origin':('rParent','children')}
    for name,node in list(nodes.items()):
        if name in ('matrix','reference'):
            nodes[name+'_update']=ResolveField(graph,node,'rDynamicUpdateData','DynamicUpdateData')
    suffix=path.stem.removeprefix(case_name);stage='restore_draft_second' if suffix=='_restored' else suffix.lstrip('_') or 'baseline';reading=observations[stage]
    rows.append(dict(source=str(path.relative_to(root)),sha256=archive['sha256'],stage=stage,api_transform=reading['profile']['transform'],api_normal=[reading['profile']['transform'][i] for i in (2,6,10)],api_center=reading['profile']['center_world_cm'],nodes={name:dict(identity=node.Identity,class_name=node.ClassName,fields=EncodeState({key:value for key,value in node.Fields.items() if name not in subset or key in subset[name]})) for name,node in nodes.items()}))
result=dict(sdk_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=False,native_api_calls=0,capture_sha256=hashlib.sha256(capture_path.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),case=case_name,rows=rows)
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True));print(json.dumps(dict(case=case_name,files=len(rows),source_hashes=[r['sha256'] for r in rows])))
