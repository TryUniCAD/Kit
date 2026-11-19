from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,json,subprocess,sys

ROOT=Path(__file__).resolve().parent
CASES=(('H01SheetA','*Right','8fca05f17d7a331da70daf83a189be6dacc6f2cfc946d452b0c246a8ddab0b6b'),('H02SheetB','*Top','b21216652ce759bc6e4912b0116eeb7bd78de4ba456f19f83449e56010663b77'))
CHILD='4f752c0093f04a3a383b68bfaeaad8b0fc05285d064989d818c3dc92d990a1ce'
MODES=('none','swap_sides','swap_boundaries','model_key','feature','epoch','file_handle','configuration','role_count','missing_marker','nonadjacent_sides','cap_contour','same_caps','finite_range','body_owner')


def digest(path):return sha256(path.read_bytes()).hexdigest()


def closure(root):
    paths=[p for p in (root/'src').rglob('*') if p.is_file() and p.suffix in ('.py','.json')]
    paths+=[p for p in (root/'re/tooling/sw2026/drawing_origins/Code02/src').rglob('*.py')]
    return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(paths)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--disclosed-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    sources=closure(args.root);tools=[{'path':name,'sha256':digest(ROOT/name)} for name in ('RailJoin01.py','CheckRail01.py','CheckAnalyticPrisms01.py','RunRails01.py')]
    (args.output/'SourceManifest.json').write_text(json.dumps({'files':sources,'file_count':len(sources)},sort_keys=True,indent=2)+'\n')
    (args.output/'Tools.json').write_text(json.dumps(tools,sort_keys=True,indent=2)+'\n')
    inputs=[]
    for name,orientation,pin in CASES:
        directory=args.disclosed_root/name;drawing=directory/(name+'.SLDDRW');child=directory/'GeneratedChildFile.SLDPRT'
        if digest(drawing)!=pin or digest(child)!=CHILD:raise ValueError('exact disclosed source differs')
        inputs.append({'case':name,'orientation':orientation,'drawing':str(drawing),'drawing_sha256':pin,'child':str(child),'child_sha256':CHILD})
    (args.output/'Inputs.json').write_text(json.dumps(inputs,sort_keys=True,indent=2)+'\n')
    def run(job):
        row,mutation=job;name=row['case']+'-'+mutation;output=args.output/(name+'.json')
        command=[sys.executable,'-I','-B',str(ROOT/'CheckRail01.py'),'--root',str(args.root),'--drawing',row['drawing'],'--drawing-sha256',row['drawing_sha256'],'--child',row['child'],'--child-sha256',CHILD,'--orientation',row['orientation'],'--mutation',mutation,'--output',str(output)]
        done=subprocess.run(command,text=True,capture_output=True)
        (args.output/(name+'.stdout')).write_text(done.stdout);(args.output/(name+'.stderr')).write_text(done.stderr)
        return {'case':row['case'],'mutation':mutation,'exit_code':done.returncode,'report_sha256':digest(output) if output.exists() else None,'report':json.loads(output.read_bytes()) if output.exists() else None}
    rows=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,(row,mode)) for row in inputs for mode in MODES]
        for done in as_completed(futures):rows.append(done.result())
    rows.sort(key=lambda row:(row['case'],row['mutation']))
    synthetic=args.output/'AnalyticPrisms.json'
    finished=subprocess.run([sys.executable,'-I','-B',str(ROOT/'CheckAnalyticPrisms01.py'),'--root',str(args.root),'--output',str(synthetic)],text=True,capture_output=True)
    (args.output/'AnalyticPrisms.stdout').write_text(finished.stdout);(args.output/'AnalyticPrisms.stderr').write_text(finished.stderr)
    geometry=json.loads(synthetic.read_bytes()) if synthetic.exists() else None
    unchanged=closure(args.root)==sources and all(digest(ROOT/row['path'])==row['sha256'] for row in tools)
    unchanged=unchanged and all(digest(Path(row['drawing']))==row['drawing_sha256'] and digest(Path(row['child']))==CHILD for row in inputs)
    passed=unchanged and len(rows)==30 and all(row['exit_code']==0 and row['report']['passed'] for row in rows) and finished.returncode==0 and geometry['passed']
    report={'schema':'kit.sw2026.detailing-rail-feature-correlation.v1','passed':passed,'fresh_sdk_processes':31,'source_processes':30,'source_cases':2,'independent_child_payloads':1,'negative_variants':12,'negative_processes':24,'benign_orientation_processes':4,'baseline_processes':2,'source_and_input_immutable':unchanged,'source_manifest_sha256':digest(args.output/'SourceManifest.json'),'tools_manifest_sha256':digest(args.output/'Tools.json'),'input_manifest_sha256':digest(args.output/'Inputs.json'),'rows':rows,'analytic_controls':geometry,'analytic_control_sha256':digest(synthetic) if synthetic.exists() else None,'native_runs':0,'native_endpoint_measurements':0,'native_kernel_identity':False,'generated_native_files':0,'still_sealed_inputs_read':0,'new_heldout_credit':0}
    out=args.output/'Result.json';out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':passed,'fresh_sdk_processes':31,'sha256':digest(out),'failed_workers':[(row['case'],row['mutation']) for row in rows if row['exit_code']!=0],'analytic_exit':finished.returncode}))
    raise SystemExit(0 if passed else 3)


if __name__=='__main__':main()
