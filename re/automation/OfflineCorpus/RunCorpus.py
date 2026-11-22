import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import signal
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.rescratch/offline-corpus-bounded'
ENV = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT / 'Cli'), 'PYTHONDONTWRITEBYTECODE': '1'}


def run(command, directory, label):
    directory.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with (directory / (label + '.stdout')).open('wb') as stdout, (directory / (label + '.stderr')).open('wb') as stderr:
        try:
            with subprocess.Popen(command, cwd=ROOT, env=ENV, stdout=stdout, stderr=stderr, start_new_session=True) as process:
                try:
                    code = process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    code = "timeout"
        except subprocess.TimeoutExpired:
            code = 'timeout'
    return {'command': command, 'exit': code, 'seconds': time.time() - start}


def decode(asset):
    path = asset['path']
    directory = OUT / 'assets' / hashlib.sha256(path.encode()).hexdigest()
    results = []
    if asset['format'] in ('sldprt', 'f3d', 'f3z'):
        tool = 'SolidworksReader.py' if asset['format'] == 'sldprt' else 'FusionReader.py'
        command = [sys.executable, '-m', 'KitCli', 'research', '--offline', '--root', str(ROOT), 'solidworks' if asset['format'] == 'sldprt' else 'fusion', '--manifest', str(OUT / 'Corpus.json'), '--asset', path, '--output', str(directory / 'deterministic')]
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor, (OUT / 'Results.jsonl').open('x') as journal:
        for future in concurrent.futures.as_completed([executor.submit(decode, asset) for asset in assets]):
            result = future.result()
            journal.write(json.dumps(result, ensure_ascii=True) + '\n')
            journal.flush()
            report['assets'].append(result)
            print(json.dumps({'completed': len(report['assets']), 'total': len(assets), 'path': result['source']['path'], 'exits': [item['exit'] for item in result['runs']]}), flush=True)
    (OUT / 'Report.json').write_text(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
