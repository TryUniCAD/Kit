from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import argparse,json,subprocess,sys

def digest(path):return sha256(path.read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():digest(p) for p in (root/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
def put(path,value):
 assert not path.exists(),path
 path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
def run(args,job):
 label,root,request=job;dest=args.output/(label+'.json');argv=[sys.executable,'-I','-B',str(Path(__file__).with_name('CircleChildBoundsProcess.py')),'--root',str(root),'--factory',str(args.factory),'--output',str(dest)];proc=subprocess.run(argv,input=json.dumps(request,sort_keys=True),text=True,capture_output=True,timeout=180);put(args.output/(label+'.Transport.json'),{'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr});assert proc.returncode==0,(label,proc.stderr[-1400:]);result=json.loads(dest.read_bytes());assert result['passed'];return label,result,{'label':label,'sha256':digest(dest),'pid':result['pid']}
def main():
 p=argparse.ArgumentParser()
 for name in ('root','baseline','factory','inputs','output'):p.add_argument('--'+name,type=Path,required=True)
 args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False);before={name:inventory(getattr(args,name)) for name in ('root','baseline')};tools={name:digest(Path(__file__).with_name(name)) for name in ('RunCircleChildBounds.py','CircleChildBoundsProcess.py')};put(args.output/'SourceBefore.json',{'sdk':before,'tools':tools,'factory_sha256':digest(args.factory),'input_sha256':digest(args.inputs)});cases=json.loads(args.inputs.read_bytes());jobs=[]
 for spec in cases['circles']:
  for role,root in (('Current',args.root),('Baseline',args.baseline)):jobs.append((spec['case']+role,root,{'spec':spec,'kind':'circle','expected_refusal':role=='Baseline'}))
 for raw in cases['rectangles']:
  for role,root in (('Current',args.root),('Baseline',args.baseline)):jobs.append((raw['spec']['case']+role,root,{**raw,'kind':'rectangle','expected_refusal':False}))
 for name in ('top','reverse','mid_plane','two_directions','stale_radius','foreign_profile','foreign_support','stale_depth','extra_arc','foreign_arc_row','cut_owner','draft','inactive_reverse','foreign_dimension','external_parameter'):jobs.append(('Negative'+name,args.root,{'spec':cases['circles'][0],'kind':'circle','expected_refusal':True,'mutation':name}))
 with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(lambda job:run(args,job),jobs))
 mapping={label:value for label,value,_ in rows}
 for prefix in ('C01','C02','R01','R02'):
  a,z=mapping[prefix+'Current'],mapping[prefix+'Baseline'];assert a['part_sha256']==z['part_sha256'] and a['streams_sha256']==z['streams_sha256']
  if prefix.startswith('R'):assert a['bounds']==z['bounds'] and a['target_aliases']==z['target_aliases']
 pids=[r[2]['pid'] for r in rows];assert len(pids)==len(set(pids))==23;assert all(inventory(getattr(args,k))==v for k,v in before.items());assert all(digest(Path(__file__).with_name(k))==v for k,v in tools.items());result={'passed':True,'sdk_processes':23,'fresh_process_ids':pids,'circle_target_positives':2,'circle_old_refusals_preserved':2,'malformed_refusals':15,'rectangle_complete_pairs_identical':2,'all_four_part_and_stream_pairs_identical':True,'source_unchanged':True,'tools_unchanged':True,'native_processes':0,'hidden_inputs_read':0,'new_assembly_files':0,'source_before_sha256':digest(args.output/'SourceBefore.json'),'records':[r[2] for r in rows]};put(args.output/'Results.json',result);print(json.dumps({'passed':True,'result_sha256':digest(args.output/'Results.json')}))
if __name__=='__main__':main()
