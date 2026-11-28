import hashlib
import json
from pathlib import Path
import sys
import tarfile
run=Path(sys.argv[1]).resolve()
p=Path(sys.argv[2]).resolve()
groups=[json.loads((p/group/'Evidence/Summary.json').read_text()) for group in ('','Expansion')]
summary=dict(task='A08h-FusionOffsetStart20261127',reader_revision=groups[0]['reader_revision'],source_revisions=[x['source_revision'] for x in groups],models=False,conversion_acceptance='not_established',groups=groups)
for key in ('native_files','capture_observations','fresh_processes','lifecycle_comparisons','lifecycle_failed','native_decode_checks','native_decode_failed','asm_members','asm_initial_table_failures'):
    summary[key]=sum(g[key] for g in groups)
pids=[pid for g in groups for pid in g['fresh_process_ids']]
assert len(set(pids))==27
for mode in ('strict','partial'):
    summary[mode]={key:sum(g[mode][key] for g in groups) for key in groups[0][mode]}
assert summary['native_files']==139 and summary['capture_observations']==193 and summary['native_decode_checks']==2780 and summary['lifecycle_comparisons']==405
assert summary['lifecycle_failed']==summary['native_decode_failed']==summary['asm_initial_table_failures']==0
archive_members=[]
for group in ('','Expansion'):
    with tarfile.open(p/group/'Evidence/ReaderArtifacts.tar.gz') as archive:
        names=archive.getnames();assert all(n.endswith('.json') and '..' not in Path(n).parts for n in names)
        archive_members.append(dict(group=group or 'initial',json_members=len(names)))
summary['reader_archives']=archive_members
hashes={v['observations']['executable_sha256'] for group in ('','Expansion') for v in json.loads((p/group/'Evidence/NativeVerification.json').read_text())['verifications']}
assert len(hashes)==1
summary['native_executable_sha256']=next(iter(hashes))
(p/'Evidence/CampaignSummary.json').write_text(json.dumps(summary,indent=2))
status=json.loads((run/'FinalControllerStatus.json').read_text())
rows=status.get('jobs',[])
if isinstance(rows,dict):rows=list(rows.values())
curated=[]
for row in rows:
    curated.append({key:row[key] for key in ('id','job_id','kind','state','generation','attempt','attempts','fingerprint','definition_sha256','rule_version','tool_version','result','receipt','reason','last_reason') if key in row})
(p/'Evidence/ControllerOutcomes.json').write_text(json.dumps(dict(raw_status_sha256=hashlib.sha256((run/'FinalControllerStatus.json').read_bytes()).hexdigest(),jobs=curated),indent=2))
oracle=json.loads((run/'FinalOracleStatus.json').read_text())
assert not oracle['busy']['fusion'] and not oracle['recovery_required']['fusion'] and not oracle['applications']['fusion']['running']
(p/'Evidence/OracleRelease.json').write_text(json.dumps(dict(busy=False,recovery_required=False,application=oracle['applications']['fusion']),indent=2))
overlaps=[]
for group,prefix in (('', ''),('Expansion','expand-')):
    base=run/group
    native=[json.loads(f.read_text()) for f in base.glob('verify-*/Receipt.json')]
    for mode in ('strict','partial'):
        receipt=base/(prefix+'decode-'+mode+'-valid-prefix')/'Receipt.json'
        reader=json.loads(receipt.read_text())
        witnesses=[]
        for n in native:
            seconds=min(reader['ended'],n['ended'])-max(reader['started'],n['started'])
            if seconds>0:witnesses.append(dict(native_job=n['job'],worker_lifetime_overlap_seconds=seconds))
        overlaps.append(dict(group=group or 'initial',reader_job=reader['job'],reader_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),models=reader['models'],witnesses=witnesses))
assert all(x['witnesses'] and not x['models'] for x in overlaps)
(p/'Evidence/BackgroundOverlap.json').write_text(json.dumps(dict(scope='Worker lifetimes, including native transport waits; not a CPU throughput claim',readers=overlaps),indent=2))
for group in ('Expansion',''):
    q=p/group
    seals={f.relative_to(q).as_posix():dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),size=f.stat().st_size) for f in sorted(q.rglob('*')) if f.is_file() and f.name!='Manifest.json'}
    (q/'Manifest.json').write_text(json.dumps(seals,indent=2))
print(json.dumps({key:summary[key] for key in ('native_files','capture_observations','fresh_processes','lifecycle_comparisons','native_decode_checks','reader_archives')},indent=2))
