import gzip,hashlib,json,subprocess,sys,traceback
from pathlib import Path
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False);(out/'Documents').mkdir()
if sys.flags.optimize:raise ValueError('public integration proof requires active assertions')
sys.path[:0]=[str(root),str(root/'src'),str(root/'Cli')]
from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Fusion.RimFillet.Public.CheckRimMeasure import CheckRimMeasure
from tests.Convert.Integration.Fusion.RimFillet.Public.ReadRimApi import ReadRimApi
from tests.Convert.Integration.Fusion.RimFillet.Public.ReadPublicBads import ReadPublicBads
from tests.Convert.Integration.Fusion.RimFillet.Public.MakePublicBad import MakePublicBad
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import ReadPolicyCases

def snapshot():
 names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','src','Cli','tests/Convert/Integration/Fusion/RimFillet'],cwd=root,text=True).splitlines()
 return {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in sorted(set(names)) if (root/name).is_file()}
initial=snapshot();report=dict(base_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),binding='working tree exact source hashes; committed-file CLI replay is separate',python=sys.version,interpreter_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),models=False,native_calls=0,native_acceptance='not_established',semantic_qualification='unverified',portable_complete=False,source_inventory_sha256=hashlib.sha256((root/'re/Fusion/RimFilletPack/Qualification/Cases.json').read_bytes()).hexdigest(),positives=[],negatives=[],errors=[])
for sample in ReadPolicyCases():
 row=dict(case=sample.CaseName,source=str(sample.Source.relative_to(root)),source_sha256=sample.Digest)
 try:
  if hashlib.sha256(sample.Source.read_bytes()).hexdigest()!=sample.Digest:raise ValueError('native source hash changed')
  document=OpenDocument(sample.Source);document.AssertValid();restored=CadDocument.from_json(document.to_json());restored.AssertValid()
  if document!=restored or document.metadata.get('fusion.read_only') is not True:raise ValueError('source restoration or write restriction changed')
  CheckRimMeasure(document,ReadRimApi(sample.CaseName));p=out/'Documents'/(sample.CaseName+'.json');p.write_text(document.to_json());row.update(passed=True,document_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),parameters=len(document.parameters),features=len(document.feature_timeline),selections=len(document.selections))
 except Exception:
  row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'));report['errors'].append(row['case'])
 report['positives'].append(row);(out/'ReadReceipt.json').write_text(json.dumps(report,indent=2)+'\n')
for family,name in ReadPublicBads():
 row=dict(family=family,case=name);payload=MakePublicBad(family,name);row['sha256']=hashlib.sha256(payload).hexdigest();path=out/('Malformed-'+family+'-'+name.replace(':','_')+'.f3d');path.write_bytes(payload)
 try:
  OpenDocument(path);row.update(passed=False,error='public strict reader accepted corruption');report['errors'].append(family+':'+name)
 except ValueError as error:row.update(passed=True,refusal=str(error))
 report['negatives'].append(row)
final=snapshot()
if initial!=final:raise ValueError('source files changed during public proof')
source_raw=(json.dumps(initial,indent=2)+'\n').encode();(out/'SourceHashes.json.gz').write_bytes(gzip.compress(source_raw,mtime=0));report.update(source_files=len(initial),source_hashes_sha256=hashlib.sha256(source_raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),summary=dict(positive=len(report['positives']),accepted=sum(r['passed'] for r in report['positives']),negative=len(report['negatives']),refused=sum(r['passed'] for r in report['negatives']),errors=len(report['errors'])))
report['artifacts']={str(p.relative_to(out)):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='ReadReceipt.json'}
(out/'ReadReceipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
if report['errors']:raise ValueError('public source proof has unresolved failures')
