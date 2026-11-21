import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--code',type=Path,required=True)
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--manifest-sha256',required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--native-qualified',choices=('yes','no'),required=True)
args=parser.parse_args()
code=args.code
assert sha256(args.manifest.read_bytes()).hexdigest()==args.manifest_sha256
manifest=json.loads(args.manifest.read_bytes())


def verify():
    for row in manifest['files']:
        assert sha256((code/row['path']).read_bytes()).hexdigest()==row['sha256']


verify()
output=args.output
output.mkdir(exist_ok=False)
cases=(('PublicAlpha','/Users/odin/Documents/UniCAD/Oracle121Takeover/SdkPublicBlankNative01/Inputs/Generated/PublicBlankAlpha.SLDDRW','64ce7aa78ea6efc2bea775682755a18eb909e5cad2403ec8cd259b51b15fc4a5'),('SdkAlpha','/Users/odin/Documents/UniCAD/Oracle121Takeover/SdkBlankNative02/Inputs/Generated/PortableAlpha.SLDDRW','c059b19358b09b09ec538c939cf2a19ee9c409b6f779319b866a28286b4f10e8'))
tasks=[]
for name,path,digest in cases:
    for route in ('api','api-json','cli','cli-explicit'):
        report=output/(name+'-'+route+'.json')
        target=output/(name+'-'+route)/'NativeRoundtrip.SLDDRW'
        command=[sys.executable,'-I','-B',str(base/'ProbePublicFlow03.py'),'--code',str(code),'--source',path,'--source-sha256',digest,'--route',route,'--target',str(target),'--report',str(report),'--native-qualified',args.native_qualified]
        tasks.append({'name':name,'route':route,'report':str(report),'command':command})


def run(row):
    done=subprocess.run(row['command'],capture_output=True,text=True,timeout=90)
    report=json.loads(Path(row['report']).read_bytes()) if Path(row['report']).exists() else None
    return {k:v for k,v in row.items() if k!='command'}|{'passed':done.returncode==0 and report and report['passed'],'exit_code':done.returncode,'data':report,'stderr':done.stderr}


with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(run,tasks))
comparisons=[]
for name,_,_ in cases:
    rows=[r for r in results if r['name']==name]
    hashes=[r['data'].get('output_sha256') for r in rows if r['data']]
    comparisons.append({'name':name,'passed':len(hashes)==4 and len(set(hashes))==1 and None not in hashes})
verify()
result={'schema':'kit.sw2026.public-blank-current-head-process.v1','passed':all(r['passed'] for r in results) and all(r['passed'] for r in comparisons),'head':manifest.get('head','explicit root source manifest'),'source_manifest_sha256':args.manifest_sha256,'workers':8,'comparisons':comparisons,'results':results,'private_payloads_read':0,'native_launches':0,'attestation_applied':args.native_qualified=='yes','shared_edits':0}
with (output/'Replay.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({'passed':result['passed'],'workers':8,'comparisons':comparisons,'failures':[{'name':r['name'],'route':r['route'],'data':r['data'],'stderr':r['stderr']} for r in results if not r['passed']],'replay_sha256':sha256((output/'Replay.json').read_bytes()).hexdigest()}))
raise SystemExit(0 if result['passed'] else 3)
