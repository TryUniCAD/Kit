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
comparison=json.loads((run/'NativeDecodesFinal/Comparison.json').read_text())
checks=[]
verifications=[]
for case in truth['cases']:
    if case['id'].startswith('control'):
        continue
    receipt=json.loads((run/('verify-'+case['id']+'-control2')/'Receipt.json').read_text())
    native=receipt['verification']
    stages={'initial_open':'baseline','rebuilt':'baseline','reopen_restored':'baseline'}
    for role in ('first','second','draft_first','draft_second'):
        stages.update({'edit_'+role:'edit_'+role,'restore_'+role:'baseline','reopen_edit_'+role:'edit_'+role})
    observations={x['stage']:x['value'] for x in native['observations']}
    checks.append(dict(case=case['id'],stage='process',matches=native['initial_documents']==native['final_documents']==0 and native['errors']==[] and native['build']=='2706.1.17' and native['source_sha256']==case['archives'][0]['sha256']))
    for stage,prior in stages.items():
        actual=observations[stage]
        target=next(x['value'] for x in case['observations'] if x['stage']==prior)
        scalar=('volume_cm3','area_cm2','first','second','draft_first','draft_second')
        residual=max([abs(actual[k]-target[k]) for k in scalar]+[abs(a-b) for a,b in zip(actual['center_cm'],target['center_cm'])]+[abs(a-b) for av,bv in zip(actual['bounds_cm'],target['bounds_cm']) for a,b in zip(av,bv)])
        profile_residual=max([abs(actual['profile']['radius_cm']-target['profile']['radius_cm'])]+[abs(a-b) for a,b in zip(actual['profile']['center_world_cm'],target['profile']['center_world_cm'])]+[abs(a-b) for a,b in zip(actual['profile']['transform'],target['profile']['transform'])])
        matches=residual<1e-7 and profile_residual<1e-10 and actual['body_count']==1 and actual['body_solid'] and actual['health']==0 and actual['operation']==3 and actual['solid'] and actual['two_sides'] and actual['start_type']==target['start_type']
        checks.append(dict(case=case['id'],stage=stage,matches=matches,max_numeric_residual=residual,profile_residual=profile_residual))
    control=next(x for x in truth['cases'] if x['id']=='control_before')
    for side in ('before','after'):
        actual=native['control_'+side]
        target=control['observations'][0]['value']
        residual=max([abs(actual[k]-target[k]) for k in ('volume_cm3','area_cm2')]+[abs(a-b) for a,b in zip(actual['center_cm'],target['center_cm'])])
        matches=residual<1e-7 and actual['body_count']==1 and actual['body_solid'] and actual['health']==0 and native['control_source_sha256']==control['archives'][0]['sha256']
        checks.append(dict(case=case['id'],stage='control_'+side,matches=matches,max_numeric_residual=residual))
    verifications.append(dict(case=case['id'],remote_job=receipt['remote_job'],script_sha256=receipt['script_sha256'],observations=native))
source=json.loads((run/'Capture/RemoteJob.json').read_text())
manifest=json.loads((run/'Corpus.json').read_text())
summary=dict(task='A08h-FusionTwoSidedDraft20261127',source_revision=manifest['source_revision'],reader_revision=comparison['reader_revision'],capture_script_sha256=hashlib.sha256((campaign/'Capture.py').read_bytes()).hexdigest(),raw_capture_report_sha256=hashlib.sha256((run/'Capture/Capture.json').read_bytes()).hexdigest(),source_job=source['job'],source_process={k:v for k,v in source['result'].items() if k!='value'},native_files=len(manifest['assets']),capture_observations=sum(len(x['observations']) for x in truth['cases']),fresh_processes=len(verifications),fresh_process_ids=[x['observations']['process_id'] for x in verifications],lifecycle_comparisons=len(checks),lifecycle_failed=sum(not x['matches'] for x in checks),native_decode_checks=sum(len(r['checks']) for r in comparison['rows']),native_decode_failed=sum(not v for r in comparison['rows'] for v in r['checks'].values()),asm_members=sum(len(r['asm_initial_tables']) for r in comparison['rows']),asm_initial_table_failures=sum('error' in a for r in comparison['rows'] for a in r['asm_initial_tables']),strict=json.loads((run/'decode-strict/Decode/summary.json').read_text())['counts'],partial=json.loads((run/'decode-partial/Decode/summary.json').read_text())['counts'],models=False,conversion_acceptance='not_established')
baseline=next(x for x in truth['cases'] if x['id']=='baseline')['observations'][0]['value']
swapped=next(x for x in truth['cases'] if x['id']=='swapped')['observations'][0]['value']
counterexamples=dict(swapped_sides=dict(baseline_volume_cm3=baseline['volume_cm3'],swapped_volume_cm3=swapped['volume_cm3'],baseline_centroid_cm=baseline['center_cm'],swapped_centroid_cm=swapped['center_cm'],equal_volume=abs(baseline['volume_cm3']-swapped['volume_cm3'])<1e-7,centroid_distinguishes_sides=abs(baseline['center_cm'][2]-swapped['center_cm'][2])>1e-3),draft_is_not_cylindrical=dict(native_volume_cm3=baseline['volume_cm3'],untapered_same_distance_volume_cm3=__import__('math').pi*1.3**2*(1.7+2.9)))
unresolved=[dict(id='U1',confidence='partial',subject='Research ASM4 source-to-BODY reconstruction integration',evidence='All native fields and 136 production initial tables parse; research helper refuses unique same-asset stored-ID mapping',next_probe='Coordinate the research helper owner and integrate proven narrow framing without ordinal or geometric identity guessing'),dict(id='U2',confidence='not found',subject='Complete portable two-sided taper admission',evidence='66 drafted states retain strict refusals; all existing side-distance/draft roles match native API',next_probe='Qualify complete source semantics and strict geometry admission before promoting new supported scope'),dict(id='U3',confidence='not found',subject='Independent sketch radius and placement dimension edits',evidence='Radius/frame/placement vary during authoring; lifecycle edits independently exercise both feature distances and both taper parameters',next_probe='Capture a separately dimension-driven circle and placement scope'),dict(id='U4',confidence='not found',subject='Editable cross-format target conversion',evidence='Only native source and offline reader evidence was measured',next_probe='Qualify portable source graph and donor-free target construction before separate target acceptance')]
failures=[]
for p in sorted(run.glob('*/Receipt.json')):
    value=json.loads(p.read_text())
    if value.get('error'):
        failures.append(dict(job=p.parent.name,error=value['error'].replace(str(Path.home()),'<home>'),receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for name,data in [('Summary.json',summary),('NativeComparison.json',comparison),('NativeVerification.json',dict(checks=checks,verifications=verifications)),('Counterexamples.json',counterexamples),('Unresolved.json',unresolved),('FailedAttempts.json',dict(attempts=failures)),('Corpus.json',manifest)]:
    (evidence/name).write_text(json.dumps(data,indent=2))
with (evidence/'ReaderArtifacts.tar.gz').open('wb') as destination:
    with gzip.GzipFile(fileobj=destination,mode='wb',mtime=0) as zipped:
        with tarfile.open(fileobj=zipped,mode='w|') as archive:
            for mode in ('strict','partial'):
                for path in sorted((run/('decode-'+mode)/'Decode').rglob('*')):
                    if path.is_file():
                        raw=path.read_bytes()
                        info=tarfile.TarInfo(mode+'/'+path.relative_to(run/('decode-'+mode)/'Decode').as_posix())
                        info.size=len(raw)
                        archive.addfile(info,io.BytesIO(raw))
seals={p.relative_to(campaign).as_posix():dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in sorted(campaign.rglob('*')) if p.is_file() and p.name!='Manifest.json'}
(campaign/'Manifest.json').write_text(json.dumps(seals,indent=2))
print(json.dumps(summary,indent=2))
if summary['lifecycle_failed'] or summary['native_decode_failed'] or len(set(summary['fresh_process_ids']))!=11:
    raise SystemExit('native evidence has unresolved numerical failures')
