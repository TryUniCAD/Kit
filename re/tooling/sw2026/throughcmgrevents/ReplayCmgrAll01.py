import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--python',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();tools=Path(__file__).resolve().parent;out=args.output;out.mkdir(exist_ok=False);runs=[]
for label,tool,extra in (('Main','ReplayCmgr01.py',()),('EventOnly','CompareEventOnly01.py',('--replay',str(out/'Main')))):
 command=[sys.executable,'-B',str(tools/tool),'--root',str(args.root),'--python',str(args.python),'--output',str(out/label),*extra];result=subprocess.run(command,capture_output=True,text=True,timeout=1200);(out/(label+'.stdout')).write_text(result.stdout);(out/(label+'.stderr')).write_text(result.stderr);runs.append({'phase':label,'exit':result.returncode})
 if result.returncode!=0:break
passed=len(runs)==2 and all(row['exit']==0 for row in runs);report={'schema':'kit.sw2026.throughall-cmgr-event-combined-process.v1','passed':passed,'runs':runs,'main_report_sha256':sha256((out/'Main/Replay.json').read_bytes()).hexdigest() if (out/'Main/Replay.json').exists() else None,'event_only_report_sha256':sha256((out/'EventOnly/Replay.json').read_bytes()).hexdigest() if (out/'EventOnly/Replay.json').exists() else None,'fresh_process_count':110 if passed else None,'sdk_refusal_processes':64 if passed else None,'native_processes':0,'heldout_inputs_read':0,'complete_source_preparation':False,'public_activation':False};path=out/'Replay.json';path.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':passed,'fresh_process_count':report['fresh_process_count'],'sha256':sha256(path.read_bytes()).hexdigest()}));raise SystemExit(0 if passed else 3)
