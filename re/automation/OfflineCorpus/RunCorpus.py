import argparse
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
    start = time.perf_counter_ns()
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
    elapsed_ns = time.perf_counter_ns() - start
    return {'command': command, 'exit': code, 'seconds': elapsed_ns / 1e9, 'elapsed_ns': elapsed_ns}


def decode(asset, manifest, output):
    path = asset['path']
    directory = output / 'assets' / hashlib.sha256(path.encode()).hexdigest()
    results = []
    if asset['format'] in ('sldprt', 'f3d', 'f3z'):
        reader = 'solidworks' if asset['format'] == 'sldprt' else 'fusion'
        command = [sys.executable, '-m', 'KitCli', 'research', '--offline', '--root', str(ROOT), reader, '--manifest', str(manifest), '--asset', path, '--output', str(directory / 'deterministic')]
        if reader == 'fusion':
            command.append('--allow-partial')
        results.append(run(command, directory, 'reader'))
    elif asset['format'] == 'sldasm':
        results.append({'exit': 'unsupported', 'reason': 'deterministic reader supports parts and fusion archives only'})
    command = [sys.executable, '-m', 'KitCli', 'decode', path, '--partial', '-o', str(directory / 'cli.json')]
    results.append(run(command, directory, 'cli'))
    files = {str(item.relative_to(output)): {'sha256': hashlib.sha256(item.read_bytes()).hexdigest(), 'bytes': item.stat().st_size} for item in directory.rglob('*') if item.is_file()}
    record = {'elapsed_ns': sum(item.get('elapsed_ns', 0) for item in results), 'source': asset, 'runs': results, 'artifacts': files, 'native_verification': 'pending_pc_off', 'vendor_acceptance': False}
    (directory / 'Result.json').write_text(json.dumps(record, ensure_ascii=True))
    return record


def main():
    parser = argparse.ArgumentParser(description="Decode a pinned corpus without CAD applications")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    output = args.output.resolve()
    manifest_path = (args.manifest or output / "Corpus.json").resolve()
    manifest = json.loads(manifest_path.read_text())
    assets = [asset for asset in manifest["assets"] if asset["kind"] == "native"]
    if len({asset["path"] for asset in assets}) != len(assets):
        parser.error("duplicate native paths in the corpus manifest")
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "decoder_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_revision": manifest["source_revision"],
        "native_verification": "pending_pc_off",
        "vendor_acceptance": False,
        "workers": args.workers,
    }
    rows = {}
    started = time.perf_counter_ns()
    with (output / "Results.jsonl").open("x") as journal, concurrent.futures.ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:
        futures = {
            executor.submit(decode, asset, manifest_path, output): index
            for index, asset in enumerate(assets)
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            rows[futures[future]] = result
            journal.write(json.dumps(result, ensure_ascii=True) + "\n")
            journal.flush()
            print(json.dumps({"completed": len(rows), "total": len(assets),
                              "path": result["source"]["path"],
                              "exits": [item["exit"] for item in result["runs"]]}), flush=True)
    report["assets"] = [rows[index] for index in range(len(assets))]
    report["timings"] = {
        "elapsed_ns": time.perf_counter_ns() - started,
        "decode_ns": sum(row["elapsed_ns"] for row in report["assets"]),
    }
    (output / "Report.json").write_text(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
