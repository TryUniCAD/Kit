from codecs import lookup
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
root=Path(sys.argv[1]).resolve()
phase=sys.argv[2]
sys.path.insert(0,str(root/"src"))

from OwnerGuard import OwnerGuard

guard=OwnerGuard()
sys.addaudithook(guard.inspect)
sys.setprofile(guard.profile)
if phase=="source":
    sys.path.insert(0,str(root/"re/tooling/sw2026/throughsource"))
    from OwnerSource import main
else:
    from OwnerBuild import main as build_main

for name in ("utf-16-le","utf-8","latin-1","ascii"):
    lookup(name)
request=json.load(sys.stdin)
try:
    if phase=="source":
        result=main(request)
    else:
        guard.active=True
        result=build_main(request,phase,guard,root)
except Exception as error:
    trace=[]
    current=error.__traceback__
    while current is not None:
        trace.append({"function":current.tb_frame.f_code.co_name,"line":current.tb_lineno,"file":current.tb_frame.f_code.co_filename.rsplit("/",1)[-1]})
        current=current.tb_next
    result={"trace":trace,"passed":False,"phase":phase,"error_type":type(error).__name__,"error":str(error),"denied_events":list(guard.denied),"full_writer_outputs":0,"native_acceptance":False}
    status=3
else:
    status=0
finally:
    guard.active=False
    sys.setprofile(None)
print(json.dumps(result,sort_keys=True,allow_nan=False))
raise SystemExit(status)
