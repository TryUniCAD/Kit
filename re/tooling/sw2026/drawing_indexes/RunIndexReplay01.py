from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
B = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover')
CASES = (
    ('H01SheetA', 'SdkDrawingOriginalGeometryTrial01/Originals/H01SheetA/H01SheetA.SLDDRW', '*Right', '8fca05f17d7a331da70daf83a189be6dacc6f2cfc946d452b0c246a8ddab0b6b'),
    ('H02SheetB', 'SdkDrawingOriginalGeometryTrial01/Originals/H02SheetB/H02SheetB.SLDDRW', '*Top', 'b21216652ce759bc6e4912b0116eeb7bd78de4ba456f19f83449e56010663b77'),
    ('NativeFront', 'SdkLinkedNative01/Control/D01FrontView.SLDDRW', '*Front', '2fd1d31f7f957def7fd2c73b3b88295aecb56c41d29dc208445b711c3d50c525'),
    ('GeneratedFront', 'SdkLinkedNative01/Generated/LinkedFrontAlpha.SLDDRW', '*Front', '306c6a7aaced9957780bda65a5dc87a47f3de4f50d0fe008d8461dd53c6b4dee'),
    ('SavedGeneratedFront', 'SdkLinkedNative01/Inspection/Generated/OpenEditSave/EditedDrawing.SLDDRW', '*Front', '1c6953d1e4c8f321012689ff1700978c6b8d69417bede3ed1bdd9ca47459a767'),
    ('SavedNativeFront', 'SdkLinkedNative01/Inspection/ControlBefore/OpenEditSave/EditedDrawing.SLDDRW', '*Front', '77713dfab03b4166994cc8e4c79f43e08088c797459ec86e556f60d28b239633'),
)
MUTATIONS = ('config_bool', 'config_empty', 'config_separator', 'config_nul', 'config_wrapped_empty',
             'config_id_negative', 'config_id_bool', 'path_relative', 'path_suffix', 'file_kind', 'title_mismatch')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def closure(root):
    return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)}
            for p in sorted((root/'src').rglob('*')) if p.is_file() and p.suffix in ('.py','.json')]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(exist_ok=False)
    source_closure=closure(args.root)
    data={'schema':'kit.sw2026.drawing-index-text-source-closure.v1','files':source_closure,'file_count':len(source_closure)}
    (args.output/'SourceManifest.json').write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    inputs=[]
    for name,relative,orientation,expected in CASES:
        p=B/relative;actual=digest(p)
        if expected is not None and expected!=actual:raise ValueError('disclosed source hash differs '+name)
        inputs.append({'name':name,'path':str(p),'sha256':actual,'orientation':orientation})
    (args.output/'Inputs.json').write_text(json.dumps(inputs,sort_keys=True,indent=2)+'\n')
    jobs=[]
    for row in inputs:
        for variant in ('baseline','candidate'):
            jobs.append((row,variant,'none'))
    for row in (inputs[0],inputs[3]):
        for mutation in MUTATIONS:
            for variant in ('baseline','candidate'):
                jobs.append((row,variant,mutation))
    def execute(job):
        row,variant,mutation=job;name=row['name']+'-'+variant+'-'+mutation
        output=args.output/(name+'.json')
        command=[sys.executable,'-I','-B',str(ROOT/'RunIndexWorker01.py'),'--root',str(args.root),
                 '--source',row['path'],'--source-sha256',row['sha256'],'--orientation',row['orientation'],
                 '--variant',variant,'--mutation',mutation,'--output',str(output)]
        run=subprocess.run(command,text=True,capture_output=True)
        (args.output/(name+'.stdout')).write_text(run.stdout)
        (args.output/(name+'.stderr')).write_text(run.stderr)
        return {'case':row['name'],'variant':variant,'mutation':mutation,'exit_code':run.returncode,
                'report_sha256':digest(output) if output.exists() else None,
                'report':json.loads(output.read_bytes()) if output.exists() else None}
    rows=[]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[executor.submit(execute,job) for job in jobs]
        for done in as_completed(futures):rows.append(done.result())
    rows.sort(key=lambda x:(x['case'],x['mutation'],x['variant']))
    if closure(args.root)!=source_closure:raise ValueError('actual SDK closure changed during replay')
    if any(digest(Path(row['path']))!=row['sha256'] for row in inputs):raise ValueError('disclosed inputs changed')
    pairs=[]
    for source in inputs:
        matched=[row for row in rows if row['case']==source['name'] and row['mutation']=='none']
        if len(matched)!=2 or any(row['exit_code']!=0 or not row['report']['passed'] for row in matched):
            pairs.append({'case':source['name'],'passed':False});continue
        old=next(row['report'] for row in matched if row['variant']=='baseline')
        new=next(row['report'] for row in matched if row['variant']=='candidate')
        passed=(old['index'] is None and new['index']==old['constructed_text_representation']==new['constructed_text_representation']
                and old['partial_drawing_sha256']==new['partial_drawing_sha256']
                and old['strict_refusal']==new['strict_refusal']
                and old['unprojected']==new['unprojected']
                and old['profile_counts']==new['profile_counts'])
        pairs.append({'case':source['name'],'passed':passed,'source_sha256':source['sha256'],
                      'public_partial_sha256':new['partial_drawing_sha256'],
                      'profile_counts':new['profile_counts'],'unprojected':new['unprojected']})
    result={'schema':'kit.sw2026.drawing-index-text-process-proof.v1','passed':len(rows)==56
            and all(row['exit_code']==0 and row['report'] and row['report']['passed'] for row in rows)
            and all(row['passed'] for row in pairs),
            'fresh_processes':len(rows),'actual_source_drawings':len(inputs),
            'paired_source_cases':pairs,'negative_processes':len(rows)-12,'negative_variants':len(MUTATIONS),
            'runtime_unexpected_file_attempts':sum(len(row['report']['runtime_extra_file_accesses']) for row in rows if row['report']),
            'source_manifest_sha256':digest(args.output/'SourceManifest.json'),
            'input_manifest_sha256':digest(args.output/'Inputs.json'),
            'worker_sha256':digest(ROOT/'RunIndexWorker01.py'),'controller_sha256':digest(Path(__file__)),
            'source_and_input_custody_passed':True,'shared_checkout_mutations':0,'native_runs':0,
            'generated_cad_files':0,'still_sealed_inputs_read':0,'original_heldout_credit':0,'rows':rows}
    p=args.output/'Result.json';p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'fresh_processes':len(rows),'sha256':digest(p),
                      'failed_workers':[{'case':r['case'],'variant':r['variant'],'mutation':r['mutation']} for r in rows if r['exit_code']!=0]}))
    raise SystemExit(0 if result['passed'] else 3)


if __name__=='__main__':main()
