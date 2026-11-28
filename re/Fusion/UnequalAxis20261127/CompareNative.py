import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

root=Path(sys.argv[1]).resolve()
campaign=Path(sys.argv[2]).resolve()
output=Path(sys.argv[3]).resolve()
output.mkdir()
sys.path.insert(0,str(root/'re/Fusion/Study'))
from decode_basics import decode_basics
truth=json.loads((campaign/'Capture.json').read_text())
rows=[]
for case in truth['cases']:
    for archive in case['archives']:
        path=campaign/'Native'/archive['file']
        stage='edit_first' if '_edit_first.' in path.name else 'edit_second' if '_edit_second.' in path.name else 'baseline'
        observation=next(x['value'] for x in case['observations'] if x['stage']==stage)
        raw=path.read_bytes()
        row=dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),case=case['id'],stage=stage)
        try:
            if row['sha256']!=archive['sha256']:
                raise ValueError('native bytes changed')
            document=decode_basics(path)
            (output/(path.stem+'.json')).write_text(json.dumps(document,indent=2))
            stream=document['streams'][0]
            f=next(f for f in stream['features'] if f['kind']=='Revolve')
            axis=next(f for f in stream['features'] if f['kind']=='ConstructionAxis')
            values=f['revolve']
            checks=dict(first=math.isclose(values['angle_radians'],observation['first'],abs_tol=1e-10),second=math.isclose(values['against_angle_radians'],observation['second'],abs_tol=1e-10),mode=values['mode']=='TwoSided',operation=f['operation']['kind']=='NewBody' and observation['operation']==3,solid=f['is_solid']==observation['solid'],project_axis=f['is_project_axis']==observation['project_axis'],axis_origin=math.dist(values['axis']['entity']['origin_cm'],observation['axis']['origin_cm'])<1e-10,axis_direction=math.dist(values['axis']['entity']['direction'],observation['axis']['direction'])<1e-10,axis_owner=values['axis']['entity']['feature_object_id']==axis['object_id'],axis_supports=axis.get('construction_definition',{}).get('definition_kind')=='TwoPoints' and axis['construction_definition']['support_consistency']['matches'],component_owner=f['component_object_id']==axis['component_object_id'])
            profile=next(x for x in stream['features'] if x.get('name')=='RevolveProfile')
            spec=case['spec']
            normal=[-spec['direction'][1],spec['direction'][0],0]
            corners=[[o+t*d+r*n for o,d,n in zip(spec['origin'],spec['direction'],normal)] for t,r in [(spec['axial'],spec['radial']),(spec['axial']+1.9,spec['radial']),(spec['axial']+1.9,spec['radial']+0.7),(spec['axial'],spec['radial']+0.7)]]
            endpoints=[g[k] for g in profile['geometry'] if g['kind']=='Line' for k in ('component_start_cm','component_end_cm')]
            checks['profile_placement']=len(endpoints)==8 and all(any(math.dist(p,q)<1e-10 for q in endpoints) for p in corners) and all(any(math.dist(p,q)<1e-10 for q in corners) for p in endpoints)
            row.update(checks=checks,feature=f,axis=axis,body_asm_identifiers=stream['body_asm_identifiers'],reconstruction=stream['revolve_reconstruction'],native_geometry=observation)
        except Exception:
            row['error']=traceback.format_exc()
        rows.append(row)
        (output/'Comparison.json').write_text(json.dumps(dict(reader_root_revision=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),rows=rows),indent=2))
print(json.dumps(dict(files=len(rows),errors=sum('error' in r for r in rows),checks=sum(len(r.get('checks',{})) for r in rows),failed=sum(not v for r in rows for v in r.get('checks',{}).values()))))
