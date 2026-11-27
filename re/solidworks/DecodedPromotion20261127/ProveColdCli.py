import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); output.mkdir(exist_ok=False)
sys.path[:0]=[str(root),str(root/'src'),str(root/'Cli')]
from convert.api.ApiConvert import ConvertFile
from convert.Commands.WriteReport import WriteReport
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import KPartMeasureOpt
from tests.Convert.Solidworks.PlainWriting.MakeColdSource import MakeColdSource
from tests.Convert.Solidworks.PlainWriting.LeaseMeasPath import LeaseMeasPath

env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join([str(root/'src'),str(root/'Cli')])
report=dict(base_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=False,native_calls=0,new_native_acceptance=False,cases=[],python=sys.version,source_hashes={})
for name in ['src/convert/Commands/CheckPortable.py','src/convert/Commands/ConvertFile.py','src/convert/adapters/solidworks/Core/Preparation/Readback/CheckColdRead.py','src/convert/adapters/solidworks/Core/Writing/Measured/MatchPartMeas.py','tests/Convert/Solidworks/PlainWriting/MakeColdSource.py','re/solidworks/DecodedPromotion20261127/ProveColdCli.py']:
 report['source_hashes'][name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
for role in ('Skew','Step'):
 folder=output/role;folder.mkdir(); source,envelope,digest,name=MakeColdSource(folder,role)
 receipt=folder/'Measurement.json';receipt.write_text(json.dumps(envelope,indent=2)+'\n')
 sdk_folder=folder/'Sdk';sdk_folder.mkdir();sdk_target=sdk_folder/name
 sdk=ConvertFile(source,sdk_target,DestFormat=KPartFormatId,AllowCarrier=False,WriteValues={KPartMeasureOpt:envelope})
 (folder/'SdkReport.json').write_text(json.dumps(WriteReport(sdk.output),indent=2)+'\n')
 with LeaseMeasPath(folder,name) as target:
  args=[sys.executable,'-m','KitCli','convert',str(source),str(target),'--json','--native-measurement',str(receipt)]
  process=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True,timeout=120)
  (folder/'Cli.log').write_text(process.stdout+process.stderr)
  if process.returncode!=0:raise ValueError(role+' CLI refused: '+process.stderr)
  cli=json.loads(process.stdout)
  if target.read_bytes()!=sdk_target.read_bytes() or target.read_bytes()!=source.read_bytes() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('SDK/CLI/source bytes disagree')
  if not cli['vendor_loadable'] or not cli['application_usable'] or cli['dropped']:raise ValueError('CLI lost exact measured acceptance')
  if not sdk.vendor_loadable or not sdk.application_usable or sdk.dropped:raise ValueError('SDK lost exact measured acceptance')
  shutil.copyfile(target,folder/'CliResult.SLDPRT')
  (folder/'CliReport.json').write_text(json.dumps(cli,indent=2)+'\n')
 report['cases'].append(dict(role=role,source_sha256=digest,sdk_sha256=digest,cli_sha256=digest,cli_exit=process.returncode,existing_measurement_only=True))
 (output/'Proof.json').write_text(json.dumps(report,indent=2)+'\n')
report['artifacts']={str(p.relative_to(output)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='Proof.json'}
(output/'Proof.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(cases=len(report['cases']),sdk_cli_equal=True,native_calls=0)))
