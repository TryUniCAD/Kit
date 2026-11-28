from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
CHILD='4f752c0093f04a3a383b68bfaeaad8b0fc05285d064989d818c3dc92d990a1ce'
CASES=(('H01SheetA','*Right','8fca05f17d7a331da70daf83a189be6dacc6f2cfc946d452b0c246a8ddab0b6b'),
       ('H02SheetB','*Top','b21216652ce759bc6e4912b0116eeb7bd78de4ba456f19f83449e56010663b77'))
MUTATIONS=('none','acquisition_counter','configuration_name','configuration_id','ordinary_sketch_id','negative_feature_id',
           'creation_epoch','chain_mode','chain_entries','chain_owner','chain_target','display_folder','display_view',
           'display_auxflag','component_transform','manager_alias','self_selector','resolver_wrong_path',
           'resolver_relative','resolver_suffix','resolver_hash','substituted_payload','missing_origin','duplicate_origin')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def closure(root):
    return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)}
            for p in sorted((root/'src').rglob('*')) if p.is_file() and p.suffix in ('.py','.json')]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--code',type=Path,default=ROOT/'Code02')
    parser.add_argument('--disclosed-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(exist_ok=False)
    sources=closure(args.root);candidate=closure(args.code)
    if len(candidate)!=5:raise ValueError('candidate must contain exactly five new typed modules')
    source_manifest={'schema':'kit.sw2026.drawing-origin-explicit-child-source.v1','files':sources,'file_count':len(sources)}
    candidate_manifest={'schema':'kit.sw2026.drawing-origin-explicit-child-code.v1','files':candidate,'file_count':len(candidate)}
    (args.output/'SourceManifest.json').write_text(json.dumps(source_manifest,sort_keys=True,indent=2)+'\n')
    (args.output/'CodeManifest.json').write_text(json.dumps(candidate_manifest,sort_keys=True,indent=2)+'\n')
    inputs=[]
    for name,orientation,pin in CASES:
        drawing=args.disclosed_root/name/(name+'.SLDDRW')
        child=args.disclosed_root/name/'GeneratedChildFile.SLDPRT'
        if digest(drawing)!=pin or digest(child)!=CHILD:raise ValueError('disclosed source hash differs')
        inputs.append({'case':name,'orientation':orientation,'drawing':str(drawing),'drawing_sha256':pin,'child':str(child),'child_sha256':CHILD})
    (args.output/'Inputs.json').write_text(json.dumps(inputs,sort_keys=True,indent=2)+'\n')
    def run(job):
        row,mutation=job;name=row['case']+'-'+mutation;output=args.output/(name+'.json')
        command=[sys.executable,'-I','-B',str(ROOT/'RunOriginWorker01.py'),'--root',str(args.root),'--code',str(args.code),
                 '--drawing',row['drawing'],'--drawing-sha256',row['drawing_sha256'],'--child',row['child'],
                 '--child-sha256',row['child_sha256'],'--orientation',row['orientation'],'--mutation',mutation,'--output',str(output)]
        result=subprocess.run(command,text=True,capture_output=True)
        (args.output/(name+'.stdout')).write_text(result.stdout)
        (args.output/(name+'.stderr')).write_text(result.stderr)
        return {'case':row['case'],'mutation':mutation,'exit_code':result.returncode,'report_sha256':digest(output) if output.exists() else None,
                'report':json.loads(output.read_bytes()) if output.exists() else None}
    jobs=[(row,mutation) for row in inputs for mutation in MUTATIONS]
    rows=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,job) for job in jobs]
        for done in as_completed(futures):rows.append(done.result())
    rows.sort(key=lambda row:(row['case'],row['mutation']))
    unchanged=closure(args.root)==sources and closure(args.code)==candidate
    unchanged=unchanged and all(digest(Path(row['drawing']))==row['drawing_sha256'] and digest(Path(row['child']))==CHILD for row in inputs)
    passed=len(rows)==48 and unchanged and all(row['exit_code']==0 and row['report'] and row['report']['passed'] for row in rows)
    result={'schema':'kit.sw2026.drawing-origin-explicit-child-process.v1','passed':passed,'fresh_processes':len(rows),
            'positive_original_states':2,'benign_counter_variants':2,'negative_workers':44,'negative_variants':22,
            'independent_child_payloads':1,'source_and_input_unchanged':unchanged,'shared_source_writes':0,'native_runs':0,
            'still_sealed_inputs_read':0,'new_heldout_credit':0,'public_strict_admission':False,'full_source_admission':False,
            'source_manifest_sha256':digest(args.output/'SourceManifest.json'),'code_manifest_sha256':digest(args.output/'CodeManifest.json'),
            'inputs_sha256':digest(args.output/'Inputs.json'),'worker_sha256':digest(ROOT/'RunOriginWorker01.py'),
            'controller_sha256':digest(Path(__file__)),'rows':rows}
    path=args.output/'Result.json';path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':passed,'fresh_processes':len(rows),'result_sha256':digest(path),
                      'failed_workers':[{'case':row['case'],'mutation':row['mutation']} for row in rows if row['exit_code']!=0]}))
    raise SystemExit(0 if passed else 3)


if __name__=='__main__':
    main()
