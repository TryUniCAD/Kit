"""Re-derive KernelEvidence routine addresses and calls from an arm64 ASM kernel slice.

Usage: python3 KernelRoutines.py <thin arm64 libASMkern232.dylib>
The slice is produced with `lipo -thin arm64`. The script records the slice
SHA-256, each routine's current address range and its ordered direct calls, and
whether the previously recorded call sequence is still a subsequence.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTRA = (
    ('ATTRIB_STITCH_HINT::save_common(ENTITY_LIST&) const', ['write_id_level', 'ATTRIB_SYS::save_common', 'write_real', 'write_real', 'write_real'], 'ATTRIB_SYS d d d'),
    ('ATTRIB_VERTEDGE::save_common(ENTITY_LIST&) const', ['write_id_level', 'ATTRIB_SYS::save_common', 'write_int', 'write_ptr', 'write_int'], 'ATTRIB_SYS i (@ i)*count; the trailing int is gated on the save version'),
    ('ATTRIB_SYS::save_common(ENTITY_LIST&) const', ['write_id_level', 'ATTRIB::save_common'], 'ATTRIB head only'),
)


def symbols(path):
    output = subprocess.run(['nm', '-n', path], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in output.splitlines():
        match = re.match(r'^([0-9a-f]{16}) [tT] (.+)$', line)
        if match:
            rows.append((int(match.group(1), 16), match.group(2)))
    names = subprocess.run(['c++filt'], input='\n'.join(name for _, name in rows), capture_output=True, text=True, check=True).stdout.splitlines()
    return [(address, name) for (address, _), name in zip(rows, names)]


def calls(path, start, stop):
    output = subprocess.run(['xcrun', 'llvm-objdump', '--disassemble', '--demangle', f'--start-address={start:#x}', f'--stop-address={stop:#x}', path], capture_output=True, text=True, check=True).stdout
    found = []
    for line in output.splitlines():
        match = re.search(r'\tb(?:l)?\s+0x[0-9a-f]+ <([^>+]+)>', line)
        if match:
            found.append(match.group(1))
    return found


def is_subsequence(recorded, current):
    position = 0
    for name in current:
        if position < len(recorded) and recorded[position] in name:
            position += 1
    return position == len(recorded)


def main():
    slice_path = sys.argv[1]
    evidence = json.loads((HERE / 'KernelEvidence.json').read_text())
    table = symbols(slice_path)
    index = {name.split('(')[0]: position for position, (_, name) in enumerate(table)}
    routines = evidence['routines'] + [dict(symbol=symbol, calls=recorded, stream=stream) for symbol, recorded, stream in EXTRA if all(item['symbol'] != symbol for item in evidence['routines'])]
    for routine in routines:
        position = index.get(routine['symbol'].split('(')[0])
        if position is None:
            routine['current'] = dict(found=False)
            continue
        start, stop = table[position][0], table[position + 1][0]
        current = calls(slice_path, start, stop)
        routine['current'] = dict(found=True, range=f'{start:#x}-{stop:#x}', calls=current, recordedCallsAreSubsequence=is_subsequence(routine['calls'], current))
    evidence['routines'] = routines
    evidence['kernel']['currentSlice'] = dict(path='Autodesk Fusion.app/Contents/Frameworks/ASM/libASMkern232.dylib (lipo -thin arm64)', sha256=hashlib.sha256(Path(slice_path).read_bytes()).hexdigest(), note='Recorded ranges above came from an earlier extraction whose SHA-256 no longer reproduces; current ranges and calls are re-derived here')
    (HERE / 'KernelEvidence.json').write_text(json.dumps(evidence, indent=1) + '\n')
    for routine in routines:
        print(routine['symbol'], routine['current'].get('range'), routine['current'].get('recordedCallsAreSubsequence'))


if __name__ == '__main__':
    main()
