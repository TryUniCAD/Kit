import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback

root=Path(sys.argv[1]).resolve()
campaign=Path(sys.argv[2]).resolve()
output=Path(sys.argv[3]).resolve()
output.mkdir()
sys.path[:0]=[str(root/'re/Fusion/Study'),str(root/'src')]
from decode_basics import decode_basics
from fusion_archive import read_members
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
truth=json.loads((campaign/'Capture.json').read_text())
rows=[]
for case in truth['cases']:
    for archive in case['archives']:
        path=campaign/'Native'/archive['file']
        stage=next(('edit_'+role for role in ('offset','first','second') if '_edit_'+role+'.' in path.name),'baseline')
        actual=next(x['value'] for x in case['observations'] if x['stage']==stage)
        row=dict(file=path.name,case=case['id'],stage=stage,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        try:
            if row['sha256']!=archive['sha256']:
                raise ValueError('native input hash differs')
            document=decode_basics(path)
            (output/(path.stem+'.json')).write_text(json.dumps(document,indent=2))
            stream=document['streams'][0]
            feature=next(x for x in stream['features'] if x['kind']=='Extrude')
            sketch=next(x for x in stream['features'] if x['kind']=='Sketch')
            circle=next(g for g in sketch['geometry'] if g['kind']=='Circle')
            extent=feature['extent']
            one,two=extent['side_one'],extent['side_two']
            role_values={k:v[0]['raw_float64'] for k,v in feature['parameter_roles'].items()}
            checks=dict(first=abs(one['distance_cm']-actual['first'])<1e-10,second=abs(two['distance_cm']-actual['second'])<1e-10,draft_first=abs(one['taper_angle_radians']-actual['draft_first'])<1e-10,draft_second=abs(two['taper_angle_radians']-actual['draft_second'])<1e-10,along_role=abs(role_values['AlongDistance']-actual['first'])<1e-10,against_role=abs(role_values['AgainstDistance']-actual['second'])<1e-10,draft_one_role=abs(role_values['TaperAngle']-actual['draft_first'])<1e-10,draft_two_role=abs(role_values['Side2TaperAngle']-actual['draft_second'])<1e-10,mode=extent['mode']=='TwoSided',distance_kinds=one['condition']==two['condition']=='Distance',start=feature['start']['kind']=='Offset',operation=feature['operation']['kind']=='NewBody' and actual['operation']==3,profile_radius=abs(circle['radius_cm']-actual['profile']['radius_cm'])<1e-10,profile_center=math.dist(circle['component_center_cm'],actual['profile']['center_world_cm'])<1e-10,profile_owner=feature['profile_selection'][0]['sketch_object_id']==sketch['sketch_object_id'],component_owner=feature['component_object_id']==sketch['component_object_id'])
            checks['offset']=abs(feature['start']['offset_cm']-actual['offset'])<1e-10
            checks['offset_role']=abs(role_values['ProfileOffset']-actual['offset'])<1e-10
            api_normal=[actual['profile']['transform'][i] for i in (2,6,10)]
            checks['extrude_direction']=math.dist(extent['stored_direction_vector'],api_normal)<1e-10
            checks['profile_normal']=math.dist(circle['component_normal'],api_normal)<1e-10
            members=[]
            for name,raw in read_members(path).items():
                if not name.endswith(('.smb','.smbh')):
                    continue
                member=dict(member=name,sha256=hashlib.sha256(raw).hexdigest(),signature=raw[:15].decode('ascii'))
                try:
                    table=ReadAsmTable(raw)
                    member.update(roots=table.RootCount,records=len(table.Records))
                except Exception as error:
                    member['error']=str(error)
                members.append(member)
            row.update(checks=checks,feature=feature,profile=circle,native_geometry=actual,body_identifiers=stream['body_asm_identifiers'],reconstruction=stream['extrusion_reconstruction'],asm_initial_tables=members)
        except Exception:
            row['error']=traceback.format_exc()
        rows.append(row)
        (output/'Comparison.json').write_text(json.dumps(dict(reader_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),rows=rows),indent=2))
print(json.dumps(dict(files=len(rows),errors=sum('error' in r for r in rows),checks=sum(len(r.get('checks',{})) for r in rows),failed=sum(not v for r in rows for v in r.get('checks',{}).values()))))
