import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import tarfile

run=Path(sys.argv[1]).resolve()
campaign=Path(sys.argv[2]).resolve()
truthroot=Path(sys.argv[3]).resolve()
output=campaign/'Evidence'
output.mkdir(exist_ok=True)
rows=[]
summaries=[]
for group,source in [('initial',truthroot),('expanded',truthroot/'Expansion')]:
    truth=json.loads((source/'Capture/Capture.json').read_text())
    byname={a['file']:(c,a) for c in truth['cases'] for a in c['archives']}
    directory=run/(group+'-strict-final-owned-process')/'Decode'
    summary=json.loads((directory/'summary.json').read_text())
    summaries.append(summary)
    for item in summary['assets']:
        case,archive=byname[Path(item['path']).name]
        row=dict(path=item['path'],sha256=archive['sha256'],outcome=item['outcome'],holdout=case['id'].startswith('holdout'),checks={})
        expected=case['spec']['basis']=='XY'
        row['checks']['scope']=expected==(item['outcome']=='decoded')
        if expected:
            stem=archive['file'][:-4]
            stage=next(('edit_'+r for r in ('first','second','offset') if stem.endswith('_edit_'+r)),'baseline')
            measured=next(v['value'] for v in case['observations'] if v['stage']==stage)
            docraw=(directory/item['directory']/'document.json').read_bytes()
            receipt=json.loads((directory/item['directory']/'receipt.json').read_text())
            document=json.loads(docraw)
            assert hashlib.sha256(docraw).hexdigest()==item['neutral_sha256']
            params={p['id']:p for p in document['parameters']['$tuple']}
            feature=document['feature_timeline']['$tuple'][-1]
            definition=feature['definition']
            checks=row['checks']
            checks['five_owned_parameters']=len(params)==5 and set(params)==set(feature['parameter_ids']['$tuple']) and all(p['owner_id']==feature['id'] for p in params.values())
            roles=[('along_parameter_id','AlongDistance','first',10),('against_parameter_id','AgainstDistance','second',10),('start_offset_id','ProfileOffset','offset',10),('taper_parameter_id','TaperAngle','draft_first',1),('second_taper_id','Side2TaperAngle','draft_second',1)]
            for field,name,actual,scale in roles:
                param=params[definition[field]]
                checks[field]=param['attributes']['native_name']==name and abs(param['value']['value']-measured[actual]*scale)<1e-9
            topology=document['bodies']['$tuple'][0]['topology']
            checks['volume']=math.isclose(topology['volume'],measured['volume_cm3']*1000,rel_tol=1e-9)
            checks['area']=math.isclose(topology['surface_area'],measured['area_cm2']*100,rel_tol=1e-9)
            checks['bounds']=all(abs(topology['bounding_box'][side][axis]-measured['bounds_cm'][i][j]*10)<1e-8 for i,side in enumerate(('minimum','maximum')) for j,axis in enumerate(('x','y','z')))
            checks['definition']=definition['$type']=='DistanceExtrude' and definition['side_mode']=='two_sided' and definition['direction']=={'$type':'Vector3','x':0.0,'y':0.0,'z':1.0}
            checks['read_only']=document['metadata']=={'fusion.read_only':True,'kit.research_read_status':'unqualified'}
            checks['receipt']=receipt['source']['sha256']==archive['sha256'] and receipt['neutral_sha256']==item['neutral_sha256'] and receipt['sdk_revision']==summary['sdk_revision'] and receipt['manifest_sha256']==summary['manifest_sha256']
            row['document_sha256']=hashlib.sha256(docraw).hexdigest()
        else:
            row['reason']=item['reason']
        rows.append(row)
    for mode in ('strict','partial'):
        record=run/(group+'-'+mode+'-final-owned-process')/'Receipt.json'
        assert not json.loads(record.read_text())['models']
report=dict(task='A05c-FusionOffsetReader20261127',reader_revision=summaries[0]['sdk_revision'],models=False,source_files=len(rows),strict=sum(r['outcome']=='decoded' for r in rows),rejected=sum(r['outcome']=='rejected' for r in rows),comparisons=sum(len(r['checks']) for r in rows),failed=sum(not v for r in rows for v in r['checks'].values()),rows=rows,conversion_acceptance='not_established')
(output/'Admission.json').write_text(json.dumps(report,indent=2))
with (output/'Readers.tar.gz').open('wb') as destination:
    with gzip.GzipFile(fileobj=destination,mode='wb',mtime=0) as zipped:
        with tarfile.open(fileobj=zipped,mode='w|') as archive:
            for job in sorted(run.glob('*-owned-process')):
                for f in sorted((job/'Decode').rglob('*.json')):
                    raw=f.read_bytes();info=tarfile.TarInfo(job.name+'/'+f.relative_to(job/'Decode').as_posix());info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
assert report['strict']==109 and report['rejected']==30 and report['failed']==0
