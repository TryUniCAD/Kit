from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def source_files(root):
    return {str(path.relative_to(root)):digest(path) for path in sorted((root/'src').rglob('*'))
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.pyo')}


def run(args):
    require(not args.output.exists(), 'choose an unused public process proof directory')
    require(args.packet.resolve().name=='ConcentricMateSourcePacket02', 'undeclared source packet')
    require(digest(args.kernel_audit)=='2bd548351cdcb9ac1a3a4fe533a7184d63862a7f2b5954e82a2d1e2195cce80a', 'independent kernel correlation changed')
    kernel=json.loads(args.kernel_audit.read_bytes())
    kernels={(row['case'],row['phase']):row for row in kernel['rows']}
    tools=Path(__file__).resolve().parent
    names=('ReadConcentricPublic.py','PrepareConcentricReadFaults.py','CompareConcentricRead.py','RunConcentricPublicRead.py')
    toolhashes={name:digest(tools/name) for name in names}
    spec=importlib.util.spec_from_file_location('public_cylinder_comparison',tools/'CompareConcentricRead.py')
    comparison=importlib.util.module_from_spec(spec);spec.loader.exec_module(comparison)
    sdk=source_files(args.root);baseline=source_files(args.baseline)
    inputs={str(args.kernel_audit):digest(args.kernel_audit),str(args.planar_cohort):digest(args.planar_cohort)}
    positives=[];native={}
    case_names={'D01':'ConcentricD01AlignedFree','D02':'ConcentricD02AlignedLocked','D03':'ConcentricD03AntiFree'}
    for case,name in case_names.items():
        folder=args.packet/'Disclosed'/case
        lock=json.loads((folder/'lock.json').read_bytes())
        require(lock['source_locked'] is True and lock['heldout_source_locked'] is False,'native source is not disclosed and locked')
        author=json.loads((folder/'author.json').read_bytes())
        require(author['passed'] is True and author['result']['passed'] is True,'native source author was not qualified')
        for path in (folder/'lock.json',folder/'author.json'):inputs[str(path)]=digest(path)
        for phase in ('source','edited'):
            parent=folder/'Native'/phase.title()/(name+'.SLDASM')
            child=parent.parent/('Concentric'+case+'Child.SLDPRT')
            for role,path in (('parent',parent),('child',child)):
                expected=lock['native_artifacts'][phase][role]
                require(digest(path)==expected['sha256'] and path.stat().st_size==expected['bytes'],'native source identity changed')
                inputs[str(path)]=digest(path)
            native[(case,phase)]=(author['result'][phase],lock['native_artifacts'][phase]['child']['sha256'])
            require(kernels[(case,phase)]['child_sha256']==digest(child) and kernels[(case,phase)]['parent_sha256']==digest(parent),'independent kernel input differs')
            for mode in ('default','metadata'):
                positives.append({'label':case+phase.title()+mode.title(),'path':str(parent),'sha256':digest(parent),'mode':mode,'case':case,'phase':phase})
    original=json.loads(args.planar_cohort.read_bytes())['files']
    planar=[]
    for case in ('A17PlaneCoincident','A18PlaneDistance','A19PlaneParallel'):
        rows=[row for row in original if Path(row['path']).stem==case and Path(row['path']).suffix=='.SLDASM']
        require(len(rows)==1,'planar control identity is missing or ambiguous')
        row=rows[0];path=Path(row['path']);require(digest(path)==row['sha256'],'planar control changed')
        inputs[str(path)]=digest(path)
        child=path.parent/'CohortChild.SLDPRT';inputs[str(child)]=digest(child)
        planar.append({'label':case,'path':str(path),'sha256':digest(path)})
    require(args.perpendicular.parent.name=='Source' and args.perpendicular.name=='PerpendicularFrontTop.SLDASM','undeclared perpendicular control')
    parent=args.perpendicular;folder=parent.parents[2];lock=json.loads((folder/'lock.json').read_bytes())
    require(lock['source_locked'] is True and lock['heldout_source_locked'] is False,'perpendicular control not disclosed')
    require(digest(parent)==lock['native_artifacts']['source']['parent']['sha256'],'perpendicular parent changed')
    inputs[str(parent)]=digest(parent);inputs[str(folder/'lock.json')]=digest(folder/'lock.json')
    child_files=[path for path in parent.parent.iterdir() if path.suffix=='.SLDPRT']
    require(len(child_files)==1 and digest(child_files[0])==lock['native_artifacts']['source']['child']['sha256'],'perpendicular child changed')
    inputs[str(child_files[0])]=digest(child_files[0])
    planar.append({'label':'Perpendicular','path':str(parent),'sha256':digest(parent)})
    args.output.mkdir(parents=True)
    write(args.output/'SourceBefore.json',{'sdk':sdk,'baseline':baseline,'tools':toolhashes,'inputs':inputs})
    outcomes=[]

    def execute(row):
        label=row['label'];root=row.get('root',args.root);receipt=args.output/(label+'.json')
        request={key:row[key] for key in ('path','sha256','mode')}
        if 'adapter_values' in row:request['adapter_values']=row['adapter_values']
        command=[sys.executable,'-I','-B',str(tools/'ReadConcentricPublic.py'),'--root',str(root),'--output',str(receipt)]
        result=subprocess.run(command,input=json.dumps(request),capture_output=True,text=True,timeout=90)
        (args.output/(label+'.stdout.json')).write_text(result.stdout)
        (args.output/(label+'.stderr.txt')).write_text(result.stderr)
        require(result.returncode==0 and not result.stderr,label+' real public process failed: '+result.stdout+result.stderr)
        status=json.loads(result.stdout);require(status['passed'] is True,label+' process rejected')
        value=json.loads(receipt.read_bytes());require(digest(receipt)==status['sha256'],label+' process receipt changed')
        return {'label':label,'receipt_sha256':digest(receipt),'source_sha256':row['sha256'],'process_id':value['process_id'],'mode':row['mode'],'document_sha256':value['document_sha256'],'value':value}

    with ThreadPoolExecutor(max_workers=3) as pool:positive_results=list(pool.map(execute,positives))
    measured=[]
    for row,result in zip(positives,positive_results,strict=True):
        expected,child_hash=native[(row['case'],row['phase'])]
        compared=comparison.compare(result['value'],expected,kernels[(row['case'],row['phase'])],child_hash)
        measured.append({'case':row['case'],'phase':row['phase'],'mode':row['mode'],**compared})
        outcomes.append({key:value for key,value in result.items() if key!='value'})
    write(args.output/'NativeComparisons.json',measured)
    prep=subprocess.run([sys.executable,'-I','-B',str(tools/'PrepareConcentricReadFaults.py'),'--root',str(args.root),'--packet',str(args.packet),'--output',str(args.output/'Faults')],capture_output=True,text=True,timeout=120)
    (args.output/'Faults.stdout.json').write_text(prep.stdout);(args.output/'Faults.stderr.txt').write_text(prep.stderr)
    require(prep.returncode==0 and not prep.stderr,'diagnostic source preparation failed: '+prep.stdout+prep.stderr)
    faults=json.loads((args.output/'Faults/Faults.json').read_bytes())
    negatives=[]
    for row in faults['cases']:
        for phase,root in (('Current',args.root),('Baseline',args.baseline)):
            negatives.append({**row,'label':row['case']+phase,'mode':'metadata','root':root})
    with ThreadPoolExecutor(max_workers=3) as pool:negative_results=list(pool.map(execute,negatives))
    negative_pairs=[]
    for index,row in enumerate(faults['cases']):
        current,old=negative_results[index*2:index*2+2]
        report=current['value']['typed_report']
        require(report is not None and report['status']=='unsupported' and report['full_selected_mate_graph'] is False,row['case']+' was admitted')
        require(row['expected_error'] in report['diagnostic'],row['case']+' failed for a different reason: '+report['diagnostic'])
        require(current['value']['legacy_semantics_sha256']==old['value']['legacy_semantics_sha256'],row['case']+' altered legacy fallback')
        negative_pairs.append({'case':row['case'],'status':'unsupported','diagnostic':report['diagnostic'],'legacy_fallback_exact_except_diagnostic_and_derived_seal':True})
    outcomes.extend({key:value for key,value in row.items() if key!='value'} for row in negative_results)
    regressions=[]
    for row in planar:
        for mode in ('default','metadata'):
            for phase,root in (('Current',args.root),('Baseline',args.baseline)):
                regressions.append({**row,'label':row['label']+mode.title()+phase,'mode':mode,'root':root})
    with ThreadPoolExecutor(max_workers=3) as pool:regression_results=list(pool.map(execute,regressions))
    for index in range(0,len(regression_results),2):
        current,old=regression_results[index:index+2]
        require(current['document_sha256']==old['document_sha256'],current['label']+' existing planar public document changed')
    outcomes.extend({key:value for key,value in row.items() if key!='value'} for row in regression_results)
    disabled=[]
    for row in (positives[0],next(value for value in positives if value['case']=='D03' and value['phase']=='source')):
        for phase,root in (('Current',args.root),('Baseline',args.baseline)):
            disabled.append({**row,'label':row['case']+'Disabled'+phase,'mode':'metadata','root':root,'adapter_values':{'resolve_components':False}})
    with ThreadPoolExecutor(max_workers=3) as pool:disabled_results=list(pool.map(execute,disabled))
    for index in range(0,len(disabled_results),2):
        current,old=disabled_results[index:index+2]
        require(current['document_sha256']==old['document_sha256'] and current['value']['typed_report'] is None and not current['value']['children'],current['label']+' disabled resolution changed')
    outcomes.extend({key:value for key,value in row.items() if key!='value'} for row in disabled_results)
    require(len({row['process_id'] for row in outcomes})==len(outcomes),'fresh SDK process identities were reused')
    require(sdk==source_files(args.root) and baseline==source_files(args.baseline),'frozen SDK changed')
    require(toolhashes=={name:digest(tools/name) for name in names},'frozen process tools changed')
    require(inputs=={name:digest(Path(name)) for name in inputs},'immutable disclosed source changed')
    result={'schema':'kit.sw2026.concentric-public-reader-proof.v1','passed':True,'records':outcomes,
        'sdk_processes':len(outcomes),'host_processes':len(outcomes)+1,'positive_public_processes':len(positive_results),
        'native_endpoint_observations_per_mode':12,'native_comparison_checks':sum(len(row['checks']) for row in measured),
        'native_numeric_checks':sum(len(row['numeric_checks']) for row in measured),'negative_cases':negative_pairs,
        'negative_public_processes':len(negative_results),'planar_public_processes':len(regression_results),
        'planar_complete_document_pairs':len(regression_results)//2,'disabled_resolution_pairs':len(disabled_results)//2,
        'source_before_sha256':digest(args.output/'SourceBefore.json'),'native_comparisons_sha256':digest(args.output/'NativeComparisons.json'),
        'diagnostic_manifest_sha256':digest(args.output/'Faults/Faults.json'),'source_unchanged':True,
        'native_processes_started':0,'hidden_inputs_read':0,'writer_output_count':0,'diagnostic_output_count':faults['diagnostic_output_count'],
        'public_writer_qualified':False,'heldout_read_qualification':False}
    write(args.output/'Results.json',result)
    return {'passed':True,'sha256':digest(args.output/'Results.json'),'sdk_processes':len(outcomes),'negative_cases':len(negative_pairs)}


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','baseline','packet','kernel-audit','planar-cohort','perpendicular','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(run(parser.parse_args()),sort_keys=True))


if __name__=='__main__':
    main()
