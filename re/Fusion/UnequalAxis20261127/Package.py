import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

run=Path(sys.argv[1]).resolve()
campaign=Path(sys.argv[2]).resolve()
evidence=campaign/'Evidence'
evidence.mkdir(exist_ok=True)
truth=json.loads((campaign/'Capture.json').read_text())
comp=json.loads((run/'NativeDecodesFinal/Comparison.json').read_text())
checks=[]
verifications=[]
for case in truth['cases']:
    if case['id'].startswith('control'):
        continue
    receipt=json.loads((run/('verify-'+case['id']+'-transport2')/'Receipt.json').read_text())
    native=receipt['verification']
    actual={x['stage']:x['value'] for x in native['observations']}
    stages={'initial_open':'baseline','rebuilt':'baseline','edit_first':'edit_first','restore_first':'baseline','reopen_edit_first':'edit_first','edit_second':'edit_second','restore_second':'baseline','reopen_edit_second':'edit_second','reopen_restored':'baseline'}
    checks.append(dict(case=case['id'],stage='process',matches=native['initial_documents']==native['final_documents']==0 and native['errors']==[] and native['build']=='2706.1.17' and native['source_sha256']==case['archives'][0]['sha256']))
    for stage,prior in stages.items():
        target=next(x['value'] for x in case['observations'] if x['stage']==prior)
        value=actual[stage]
        scalar=('volume_cm3','area_cm2','first','second')
        vectors=('center_cm',)
        matches=all(abs(value[k]-target[k])<1e-7 for k in scalar) and all(max(abs(a-b) for a,b in zip(value[k],target[k]))<1e-7 for k in vectors)
        matches=matches and value['body_count']==1 and value['health']==0 and value['operation']==3 and value['solid'] and not value['project_axis']
        matches=matches and max(abs(a-b) for a,b in zip(value['axis']['origin_cm'],target['axis']['origin_cm']))<1e-10 and max(abs(a-b) for a,b in zip(value['axis']['direction'],target['axis']['direction']))<1e-10
        checks.append(dict(case=case['id'],stage=stage,matches=matches))
    for side in ('before','after'):
        target=next(x for x in truth['cases'] if x['id']=='control_'+side)['observations'][0]['value']
        value=native['control_'+side]
        matches=value['body_count']==1 and value['health']==0 and abs(value['volume_cm3']-target['volume_cm3'])<1e-7 and max(abs(a-b) for a,b in zip(value['center_cm'],target['center_cm']))<1e-7
        checks.append(dict(case=case['id'],stage='control_'+side,matches=matches))
    verifications.append(dict(case=case['id'],remote_job=receipt['remote_job'],script_sha256=receipt['script_sha256'],observations=native))
source=json.loads((run/'Capture/RemoteJob.json').read_text())
source={k:v for k,v in source['result'].items() if k!='value'}
summary=dict(task='A08h-FusionUnequalAxis20261127',source_revision='fb4afa1aaad538c402ca67f27a0a565d7e32f1e2',reader_revision=comp['reader_root_revision'],capture_script_sha256=hashlib.sha256((campaign/'Capture.py').read_bytes()).hexdigest(),raw_capture_report_sha256=hashlib.sha256((run/'Capture/Capture.json').read_bytes()).hexdigest(),source_job='ce9d27182f07b063c541f3d0847fce89',source_process=source,native_files=46,native_capture_observations=sum(len(x['observations']) for x in truth['cases']),fresh_processes=len(verifications),fresh_process_ids=[x['observations']['process_id'] for x in verifications],native_verification_checks=len(checks),native_verification_failed=sum(not x['matches'] for x in checks),native_decode_checks=sum(len(r.get('checks',{})) for r in comp['rows']),native_decode_unresolved=sum(not v for r in comp['rows'] for v in r.get('checks',{}).values()),strict=json.loads((run/'decode-strict-manifest2/Decode/summary.json').read_text())['counts'],partial=json.loads((run/'decode-partial-manifest2/Decode/summary.json').read_text())['counts'],models=False,conversion_acceptance='not_established',remaining=['point-provider nonzero-prefix semantics','research ASM4 complete reconstruction integration','independently driven axis and profile edits','general profiles, contexts and operations','portable semantics and editable cross-format conversion'])
baseline=next(x for x in truth['cases'] if x['id']=='baseline')['observations'][0]['value']
swapped=next(x for x in truth['cases'] if x['id']=='swapped')['observations'][0]['value']
reversed_axis=next(x for x in truth['cases'] if x['id']=='reversed')['observations'][0]['value']
counterexamples=dict(swapped_angles=dict(baseline_volume_cm3=baseline['volume_cm3'],swapped_volume_cm3=swapped['volume_cm3'],baseline_centroid_cm=baseline['center_cm'],swapped_centroid_cm=swapped['center_cm'],equal_volume=abs(baseline['volume_cm3']-swapped['volume_cm3'])<1e-7,centroid_distinguishes_roles=abs(baseline['center_cm'][2]-swapped['center_cm'][2])>1e-3),axis_reversal=dict(baseline_axis=baseline['axis'],reversed_axis=reversed_axis['axis'],baseline_centroid_cm=baseline['center_cm'],reversed_centroid_cm=reversed_axis['center_cm']))
unresolved=[dict(id='U1',confidence='not found',subject='Construction-mode point provider first 23 bytes',evidence='Framing.json; eight NativeComparison.json axis_supports refusals',next_probe='Independently repeat identical axis inputs in fresh sessions; identify each prefix owner before changing the zero-prefix guard'),dict(id='U2',confidence='partial',subject='Research helper ASM4 reconstruction integration',evidence='All 92 production initial-table parses pass; research helper rejects BinaryFile4 signature',next_probe='Coordinate research helper ownership and reuse proven four-byte framing with complete body-ID/topology guards; initial framing alone is insufficient'),dict(id='U3',confidence='not found',subject='Complete portable semantic admission and target conversion',evidence='All 46 strict outcomes reject; explicit partial documents remain unqualified',next_probe='Qualify required source graph semantics independently before writer or target acceptance'),dict(id='U4',confidence='not found',subject='Independent axis/profile driving edits',evidence='Authoring offsets vary; only both angle model parameters receive independent edit/restore witnesses',next_probe='Create a separate dimension-driven axis/profile campaign with independent lifecycle and holdouts')]
for name,data in [('Unresolved.json',unresolved),('Counterexamples.json',counterexamples),('Summary.json',summary),('NativeVerification.json',dict(checks=checks,verifications=verifications)),('NativeComparison.json',comp),('Framing.json',json.loads((run/'Framing.json').read_text())),('Corpus.json',json.loads((run/'Corpus.json').read_text()))]:
    (evidence/name).write_text(json.dumps(data,indent=2))
with (evidence/'ReaderArtifacts.tar.gz').open('wb') as destination:
    with gzip.GzipFile(fileobj=destination,mode='wb',mtime=0) as zipped:
        with tarfile.open(fileobj=zipped,mode='w|') as archive:
            for name in ('decode-strict-manifest2','decode-partial-manifest2'):
                for path in sorted((run/name/'Decode').rglob('*')):
                    if path.is_file():
                        raw=path.read_bytes()
                        info=tarfile.TarInfo(name+'/'+path.relative_to(run/name/'Decode').as_posix())
                        info.size=len(raw)
                        archive.addfile(info,io.BytesIO(raw))
failures=[]
for path in sorted(run.glob('*/Receipt.json')):
    value=json.loads(path.read_text())
    if not value.get('error'):
        continue
    failures.append(dict(job=path.parent.name,error=value['error'].replace(str(Path.home()),'<home>'),receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(evidence/'FailedAttempts.json').write_text(json.dumps(dict(failures=failures,raw_retained_at='private campaign runtime directory',invocation_failures=['isolated uv cache access refused','isolated CLI build dependency DNS refused before approved network install','supervisor --offline refused because that flag selects native readers only']),indent=2))
manifest={p.relative_to(campaign).as_posix():dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in sorted(campaign.rglob('*')) if p.is_file() and p.name!='Manifest.json'}
(campaign/'Manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(summary,indent=2))
if summary['native_verification_failed'] or len(set(summary['fresh_process_ids']))!=11:
    raise SystemExit('native acceptance evidence is incomplete')
