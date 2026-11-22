import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.rescratch/offline-corpus-full'
ENV = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT / 'Cli'), 'PYTHONDONTWRITEBYTECODE': '1'}


def run(command, directory, label):
    directory.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with (directory / (label + '.stdout')).open('wb') as stdout, (directory / (label + '.stderr')).open('wb') as stderr:
        try:
            result = subprocess.run(command, cwd=ROOT, env=ENV, stdout=stdout, stderr=stderr, timeout=600)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    return {'command': command, 'exit': code, 'seconds': time.time() - start}


def decode(asset):
    path = asset['path']
    directory = OUT / 'assets' / hashlib.sha256(path.encode()).hexdigest()
    results = []
    if asset['format'] == 'sldprt':
        tool = 'SolidworksReader.py' if asset['format'] == 'sldprt' else 'FusionReader.py'
        command = [sys.executable, '-m', 'KitCli', 'research', '--offline', '--root', str(ROOT), 'solidworks', '--manifest', str(OUT / 'Corpus.json'), '--asset', path, '--output', str(directory / 'deterministic')]
        if tool == 'FusionReader.py':
            command.append('--allow-partial')
        results.append(run(command, directory, 'reader'))
    elif asset['format'] == 'sldasm':
        results.append({'exit': 'unsupported', 'reason': 'deterministic reader supports parts and fusion archives only'})
    command = [sys.executable, '-m', 'KitCli', 'decode', path, '--partial', '-o', str(directory / 'cli.json')]
    results.append(run(command, directory, 'cli'))
    files = {str(item.relative_to(OUT)): {'sha256': hashlib.sha256(item.read_bytes()).hexdigest(), 'bytes': item.stat().st_size} for item in directory.rglob('*') if item.is_file()}
    record = {'source': asset, 'runs': results, 'artifacts': files, 'native_verification': 'pending_pc_off', 'vendor_acceptance': False}
    (directory / 'Result.json').write_text(json.dumps(record, ensure_ascii=True))
    return record


def main():
    manifest = json.loads((OUT / 'Corpus.json').read_text())
    assets = [asset for asset in manifest['assets'] if asset['kind'] == 'native']
    report = {'decoder_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'source_revision': manifest['source_revision'], 'native_verification': 'pending_pc_off', 'vendor_acceptance': False, 'assets': []}
    fusion = [asset['path'] for asset in assets if asset['format'] in ('f3d', 'f3z')]
    for index in range(0, len(fusion), 1000):
        command = [sys.executable, '-m', 'KitCli', 'research', '--offline', '--root', str(ROOT), 'fusion', '--manifest', str(OUT / 'Corpus.json'), '--allow-partial', '--output', str(OUT / ('FusionBatch' + str(index)))]
        for path in fusion[index:index + 1000]:
            command.extend(['--asset', path])
        print(json.dumps(run(command, OUT, 'FusionBatch' + str(index))), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor, (OUT / 'Results.jsonl').open('x') as journal:
        for result in executor.map(decode, assets):
            journal.write(json.dumps(result, ensure_ascii=True) + '\n')
            journal.flush()
            report['assets'].append(result)
            print(json.dumps({'completed': len(report['assets']), 'total': len(assets), 'path': result['source']['path'], 'exits': [item['exit'] for item in result['runs']]}), flush=True)
    (OUT / 'Report.json').write_text(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
