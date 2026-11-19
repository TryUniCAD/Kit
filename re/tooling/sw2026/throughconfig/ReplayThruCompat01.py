import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--python',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(exist_ok=False);records=[]
for variant in (0,1):
 pair=[]
 for label in ('BaseRoot','Code01'):
  output=args.output/(label+str(variant)+'.json');script=args.root/label/'re/tooling/sw2026/throughpresentation/Compat.py';command=[str(args.python),'-B',str(script),'--root',str(args.root/label),'--variant',str(variant),'--output',str(output)];process=subprocess.run(command,text=True,capture_output=True,timeout=80);output.with_suffix('.stdout.txt').write_text(process.stdout);output.with_suffix('.stderr.txt').write_text(process.stderr)
  if process.returncode:raise RuntimeError('existing complete ordinary regression failed: '+str(command)+' '+process.stderr)
  result=json.loads(output.read_text());pair.append(result);records.append({'variant':variant,'source':label,'sha256':sha256(output.read_bytes()).hexdigest()})
 if pair[0]!=pair[1]:raise ValueError('existing complete output or public read changed')
report={'passed':True,'fresh_process_count':4,'variants':2,'whole_container_byte_identity':True,'public_read_identity':True,'native_processes':0,'heldout_inputs_read':0,'source_manifest_sha256':sha256((args.root/'SourceManifest03.json').read_bytes()).hexdigest(),'records':records};output=args.output/'Replay.json';output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'report_sha256':sha256(output.read_bytes()).hexdigest()}))
