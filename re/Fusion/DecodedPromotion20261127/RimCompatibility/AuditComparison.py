import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def require(condition,message):
    if not condition:raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args])


parser=argparse.ArgumentParser();parser.add_argument('--old',type=Path,required=True);parser.add_argument('--new',type=Path,required=True);parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
run=args.run.resolve();folder=Path(__file__).parent;roots={'old':args.old.resolve(),'new':args.new.resolve()}
report=json.loads((run/'Comparison.json').read_text());inputs=json.loads((run/'Inputs.json').read_text());rows=[];pids=[]
require(report['summary']['sources']==68,'wrong source cohort size')
require(len(inputs['assets'])==68,'wrong input count')
require(report['script_sha256']==digest((folder/'CompareDraftsFinal.py').read_bytes()),'worker source differs from retained exact build')
for role,root in roots.items():
    version=report['versions'][role]
    require(git(root,'rev-parse','HEAD').decode().strip()==version['revision'],'pinned revision changed')
    require(git(root,'rev-parse',version['revision']+':src').decode().strip()==version['src_tree'],'pinned source tree changed')
    require(not git(root,'status','--porcelain','--untracked-files=no'),'tracked checkout is dirty')
for source in inputs['assets']:
    receipts={};documents={};raws={}
    for role,root in roots.items():
        committed=git(root,'show',report['versions'][role]['revision']+':'+source['asset']);working=(root/source['asset']).read_bytes();raws[role]=committed
        require(committed==working,'working archive differs from committed blob')
        require(digest(committed)==source['sha256'],'source hash differs from manifest')
        receipt=json.loads((run/'Receipts'/role/(Path(source['asset']).stem+'.json')).read_text());receipts[role]=receipt;pids.append(receipt['pid'])
        require(receipt['status']=='strict_accepted','strict SDK read failed')
        require(receipt['source_sha256']==source['sha256'],'worker source binding differs')
        require(receipt['revision']==report['versions'][role]['revision'],'worker code binding differs')
        require(receipt['script_sha256']==report['script_sha256'],'worker script binding differs')
        require(receipt['python_executable_sha256']==report['python_executable_sha256'],'worker interpreter differs')
        require(receipt['strict'] is True and receipt['source_kind']=='BytesIO','reader invocation changed')
        encoded=(run/receipt['document']).read_bytes();documents[role]=encoded
        require(digest(encoded)==receipt['document_sha256'],'document digest mismatch')
        require(len(encoded)==receipt['document_bytes'],'document length mismatch')
        require(isinstance(json.loads(encoded),dict),'invalid document JSON')
        require(b'/Users/' not in encoded and b'/home/' not in encoded,'document contains a private home path')
    require(raws['old']==raws['new'],'original source archives differ between revisions')
    require(documents['old']==documents['new'],'SDK document bytes changed')
    rows.append(dict(asset=source['asset'],source_sha256=source['sha256'],old_document_sha256=digest(documents['old']),new_document_sha256=digest(documents['new']),document_bytes=len(documents['old']),source_path_old=receipts['old']['source_path'],source_path_new=receipts['new']['source_path'],exact_bytes_equal=True))
require(len(set(pids))==136,'process IDs do not prove distinct workers')
result=dict(models=False,native_calls=0,conversion_claim=False,native_acceptance=False,comparison_sha256=digest((run/'Comparison.json').read_bytes()),inputs_sha256=digest((run/'Inputs.json').read_bytes()),audit_script_sha256=digest(Path(__file__).read_bytes()),rows=rows,summary=dict(committed_source_archives_equal=68,strict_sdk_reads=136,distinct_fresh_processes=136,unchanged_sdk_document_bytes=68,errors=0))
(folder/'Audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary']))
