import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args])


def clean(value,roots):
    for root,label in roots:
        value=value.replace(str(root),label)
    return re.sub(r'/Users/[^/\s]+','<home>',value)


def worker(args):
    root=args.root.resolve();output=args.output.resolve();source=root/args.asset
    sys.path.insert(0,str(root/'src'))
    report=dict(role=args.role,asset=args.asset,source_sha256=args.expected,revision=args.revision,models=False,native_calls=0,pid=os.getpid(),strict=True,source_kind='BytesIO',python_version=sys.version,python_executable_sha256=digest(Path(sys.executable).resolve().read_bytes()),script_sha256=digest(Path(__file__).read_bytes()))
    try:
        assert git(root,'rev-parse','HEAD').decode().strip()==args.revision
        payload=source.read_bytes();assert digest(payload)==args.expected
        from convert import open_document
        import convert
        assert Path(convert.__file__).resolve().is_relative_to(root/'src')
        document=open_document(BytesIO(payload),strict=True)
        assert document.source.path in (None, "")
        document.AssertValid()
        encoded=document.to_json().encode('utf-8')
        assert b'/Users/' not in encoded and b'/home/' not in encoded
        target=output/'Documents'/args.role/(Path(args.asset).stem+'.json');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded)
        report.update(status='strict_accepted',document=str(target.relative_to(output)),document_sha256=digest(encoded),document_bytes=len(encoded),source_path=document.source.path,read_only=document.metadata.get('fusion.read_only'),bodies=len(document.bodies),features=len(document.feature_timeline),parameters=len(document.parameters))
    except Exception as error:
        report.update(status='strict_refused' if isinstance(error,ValueError) else 'error',error=clean(traceback.format_exc(),[(root,'<pinned-checkout>'),(Path(__file__).resolve().parents[4],'<task-checkout>')]))
    target=output/'Receipts'/args.role/(Path(args.asset).stem+'.json');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return 0 if report['status']=='strict_accepted' else 3


def run(args):
    output=args.output.resolve();output.mkdir(exist_ok=False)
    roots={'old':args.old.resolve(),'new':args.new.resolve()};versions={}
    for role,root in roots.items():
        revision=git(root,'rev-parse','HEAD').decode().strip()
        assert revision==args.old_revision if role=='old' else revision==args.new_revision
        status=git(root,'status','--porcelain','--untracked-files=no').decode();assert not status
        versions[role]=dict(revision=revision,tracked_clean_before=True,src_tree=git(root,'rev-parse',revision+':src').decode().strip(),untracked_files_preserved=True)
    capture_path='re/Fusion/TwoSidedDraft20261127/Capture.json'
    capture_raw=git(roots['new'],'show',versions['new']['revision']+':'+capture_path);capture=json.loads(capture_raw)
    assets=sorted(({'asset':'re/Fusion/TwoSidedDraft20261127/Native/'+a['file'],'sha256':a['sha256']} for c in capture['cases'] for a in c['archives']),key=lambda v:v['asset'])
    assert len(assets)==68 and len({r['asset'] for r in assets})==68
    for row in assets:
        blobs={}
        for role,root in roots.items():
            committed=git(root,'show',versions[role]['revision']+':'+row['asset']);working=(root/row['asset']).read_bytes()
            assert committed==working and digest(committed)==row['sha256']
            blobs[role]=git(root,'rev-parse',versions[role]['revision']+':'+row['asset']).decode().strip()
        assert blobs['old']==blobs['new'];row.update(git_blobs=blobs,committed_bytes_equal=True)
    (output/'Inputs.json').write_text(json.dumps(dict(capture=capture_path,capture_sha256=digest(capture_raw),versions=versions,assets=assets),indent=2,sort_keys=True)+'\n')
    script=Path(__file__).resolve();started=time.monotonic();jobs=[]
    for row in assets:
        for role,root in roots.items():
            command=[sys.executable,str(script),'--worker','--root',str(root),'--role',role,'--asset',row['asset'],'--expected',row['sha256'],'--revision',versions[role]['revision'],'--output',str(output)]
            jobs.append((role,row,root,command))
    def execute(job):
        role,row,root,command=job;env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1');result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=120)
        if result.stdout or result.stderr:
            target=output/'Logs'/role/(Path(row['asset']).stem+'.json');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(dict(returncode=result.returncode,stdout=clean(result.stdout,[(root,'<pinned-checkout>')]),stderr=clean(result.stderr,[(root,'<pinned-checkout>')])),indent=2,sort_keys=True)+'\n')
        return dict(role=role,asset=row['asset'],returncode=result.returncode)
    outcomes=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(execute,job) for job in jobs]
        for completed,future in enumerate(as_completed(futures),1):
            outcomes.append(future.result())
            if completed%20==0:print(json.dumps(dict(completed=completed,total=len(jobs))),flush=True)
    comparisons=[];pids=[]
    for row in assets:
        receipts={role:json.loads((output/'Receipts'/role/(Path(row['asset']).stem+'.json')).read_text()) for role in roots}
        pids.extend(r['pid'] for r in receipts.values())
        accepted=all(r['status']=='strict_accepted' for r in receipts.values());equal=False
        if accepted:
            encoded={role:(output/receipt['document']).read_bytes() for role,receipt in receipts.items()};equal=encoded['old']==encoded['new']
        comparisons.append(dict(asset=row['asset'],source_sha256=row['sha256'],old_status=receipts['old']['status'],new_status=receipts['new']['status'],old_document_sha256=receipts['old'].get('document_sha256'),new_document_sha256=receipts['new'].get('document_sha256'),both_strict_accepted=accepted,document_bytes_equal=equal,old_source_path=receipts['old'].get('source_path'),new_source_path=receipts['new'].get('source_path')))
    for role,root in roots.items():
        versions[role]['tracked_clean_after']=not bool(git(root,'status','--porcelain','--untracked-files=no'))
        assert versions[role]['tracked_clean_after'] and git(root,'rev-parse','HEAD').decode().strip()==versions[role]['revision']
    report=dict(models=False,native_calls=0,native_acceptance=False,conversion_claim=False,script_sha256=digest(script.read_bytes()),python_version=sys.version,python_executable_sha256=digest(Path(sys.executable).resolve().read_bytes()),versions=versions,comparisons=comparisons,processes=outcomes,summary=dict(sources=len(assets),fresh_processes=len(outcomes),unique_process_ids=len(set(pids)),strict_reads=sum(r['both_strict_accepted'] for r in comparisons)*2,identical_documents=sum(r['document_bytes_equal'] for r in comparisons),refused_or_errors=sum(not r['both_strict_accepted'] for r in comparisons),changed_documents=sum(r['both_strict_accepted'] and not r['document_bytes_equal'] for r in comparisons),seconds=time.monotonic()-started))
    (output/'Comparison.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']),flush=True)
    return 0 if report['summary']['identical_documents']==68 else 3


parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true');parser.add_argument('--root',type=Path);parser.add_argument('--role');parser.add_argument('--asset');parser.add_argument('--expected');parser.add_argument('--revision');parser.add_argument('--old',type=Path);parser.add_argument('--new',type=Path);parser.add_argument('--old-revision',default='f34820a9d87ac34ca01bd2c5f59cbf6af37f93df');parser.add_argument('--new-revision',default='bcabfa069ab3dd0547e031341ec547aefe255b68');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
raise SystemExit(worker(args) if args.worker else run(args))
