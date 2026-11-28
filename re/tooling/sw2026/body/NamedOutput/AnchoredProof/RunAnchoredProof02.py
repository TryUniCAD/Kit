from argparse import ArgumentParser
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from subprocess import run
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(root):
    for name in ('WriterSource01', 'BaselineSource01'):
        directory = root / ('Code01' if name == 'WriterSource01' else 'Baseline01')
        for path, expected in loads((root/(name+'.json')).read_bytes())['files'].items():
            if digest(directory/path) != expected:
                raise ValueError('frozen construction source changed: ' + path)
    for path, expected in loads((root/'WriterTools02.json').read_bytes())['files'].items():
        if digest(root/path) != expected:
            raise ValueError('frozen construction tools changed: ' + path)


def main():
    parser = ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    verify(root)
    cases = loads((root/'NeutralCases01.json').read_bytes())['cases']
    if args.verify_only:
        print(dumps({'verified':True,'processes_started':0,'heldout_inputs_read':0}))
        return
    args.output.mkdir(parents=True,exist_ok=False)
    variants = ('EmptyName','OuterWhitespace','OverlongName','WideUnitOverflow','UnpairedSurrogate',
        'EmbeddedNull','ControlCharacter','UnownedBody','SecondBody','BodyAttributes','ExtraMetadata',
        'ExtraFeature','ReversedEnd','CircleProfile','WrongDriverOwner','DuplicateDriverName',
        'GraphRepeatedOutput','GraphOldManager','GraphCounterOverflow','GraphExistingOutput',
        'GraphGhostBody','GraphPresentPartition','GraphForeignHistory')
    anchor_variants = ('NullAnchorInput','NullDimensions','InvalidAnchorKind','WrongAnchorFamily',
        'DroppedAxis','SuppressedAxis','WrongAnchorPlacement','ExtraConstruction')
    jobs = [(case,mode,None) for case in cases for mode in ('Named','Repeat','Default','Reference')]
    jobs += [(cases[0],'Reject',variant) for variant in variants]
    jobs += [(case,'Reject',variant) for case in (cases[0],cases[-1]) for variant in anchor_variants]

    def execute(job):
        case,mode,variant = job
        script = {'Reference':'BuildAnchorBaseline02.py','Reject':'RejectAnchoredNamed01.py'}.get(mode,'BuildAnchoredNamed01.py')
        source = root/('Baseline01' if mode=='Reference' else 'Code01')
        command = [sys.executable,'-I','-B',str(root/script),'--sdk',str(source)]
        if mode=='Default':
            command.append('--default-body')
        if mode=='Reject':
            command += ['--variant',variant]
        name = case['name']+mode+(variant or '')
        process = run(command,input=dumps(case),text=True,capture_output=True,timeout=180)
        report_path = args.output/(name+'.json')
        error_path = args.output/(name+'.stderr')
        report_path.write_text(process.stdout,encoding='utf-8',newline='\n')
        error_path.write_text(process.stderr,encoding='utf-8',newline='\n')
        value = loads(process.stdout) if process.returncode==0 else None
        if value and mode!='Reject':
            data = b64decode(value['blob'],validate=True)
            if sha256(data).hexdigest()!=value['artifact_sha256']:
                raise ValueError('generated native transport differs')
            (args.output/(name+'.SLDPRT')).write_bytes(data)
        return {'case':case['name'],'mode':mode,'variant':variant,'returncode':process.returncode,
            'passed':bool(value and value['passed']),'report_sha256':digest(report_path),
            'stderr_sha256':digest(error_path),'result':value}

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(execute,jobs))
    comparisons = []
    for case in cases:
        group = {row['mode']:row for row in rows if row['case']==case['name'] and row['mode']!='Reject'}
        passed = all(row['passed'] for row in group.values())
        if passed:
            named,repeat,default,reference = (group[mode]['result'] for mode in ('Named','Repeat','Default','Reference'))
            passed = named['artifact_sha256']==repeat['artifact_sha256'] and named['streams']==repeat['streams']
            passed = passed and named['plain_artifact_sha256']==default['artifact_sha256']==reference['artifact_sha256']
            passed = passed and default['streams']==reference['streams']
            passed = passed and named['anchor_graph']==default['anchor_graph']==reference['anchor_graph']
        comparisons.append({'case':case['name'],'kind':case['anchor_kind'],'passed':passed,
            'deterministic_native_bytes':passed,'frozen_baseline_default_bytes_exact':passed,
            'actual_anchor_and_driver_graph_exact':passed})
    verify(root)
    passed = all(row['passed'] for row in rows) and all(row['passed'] for row in comparisons)
    for row in rows:
        row.pop('result')
    report = {'schema':'kit.sw2026.anchored-named-construction-process.v1','passed':passed,
        'source_manifest_sha256':digest(root/'WriterSource01.json'),
        'baseline_manifest_sha256':digest(root/'BaselineSource01.json'),
        'tools_manifest_sha256':digest(root/'WriterTools02.json'),
        'cases_sha256':digest(root/'NeutralCases01.json'),'source_unchanged':True,
        'process_count':len(rows),'positive_processes':16,'negative_processes':39,
        'processes':rows,'comparisons':comparisons,'heldout_inputs_read':0,
        'native_acceptance':False,'original_source_qualification':False,
        'public_writer_registration_changed':False,'predecessor_false_report_sha256':'d41be3949e0c0acb2e2ad9e9f57eb35231ddeb97c8a530f32dce6aa120fe7be7','observer_only_baseline_preload_repair':True}
    path=args.output/'ProcessProof.json'
    path.write_text(dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(dumps({'passed':passed,'process_count':len(rows),'failed':[(row['case'],row['mode'],row['variant']) for row in rows if not row['passed']],
        'failed_comparisons':[row['case'] for row in comparisons if not row['passed']],
        'report_sha256':digest(path),'report':str(path)}))
    raise SystemExit(0 if passed else 3)


if __name__=='__main__':
    main()
