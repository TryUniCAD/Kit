from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

KRepoRoot = FilePath(__file__).resolve().parents[4]
KProgram = """
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
count = int(sys.argv[2])
density = float(sys.argv[3])
prefix = sys.argv[4]
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / 'src'))
sys.path.insert(0, str(root / 're' / 'tooling' / 'sw2026'))
sys.path.insert(0, str(root / 're' / 'tooling' / 'sw2026' / 'serial'))

from Core import Obj
from Classes import registry
from Streams import StreamDoc, store_rooted, load_rooted
from defs.Definition import load_definition, store_definition
from builders.Model import configuration_manager
from builders.Definition import part_definition, definition_stream
from convert.adapters.solidworks.container.Container import build_sldprt, SldprtArchive

reg = registry()
reads = []

def audit(event, args):
    if event != 'open':
        return
    path, mode, flags = args
    if not isinstance(path, (str, bytes)):
        return
    suffix = Path(path.decode() if isinstance(path, bytes) else path).suffix
    if suffix in {'.py', '.pyc', '.so', '.dylib'}:
        return
    reads.append(str(path))
    raise RuntimeError('runtime file access during fresh construction: ' + str(path))

sys.addaudithook(audit)
names = [prefix + str(index) for index in range(count)]
manager = configuration_manager(
    owner=Obj('moPart_c'), names=names, date_code=2026001,
    parasolid_version=380, updated_at=1700000000,
)
definition = part_definition(
    density_kg_m3=density, drafting_standard='moISO_c', detail_flags=(0, 3, 48),
    tessellation=(20, 15, 3, False), system_preference_7a=False,
    journal_name=prefix + ' journal',
)
streams = {
    'Contents/CMgr': store_rooted(StreamDoc('rooted', {'base': 1}, [manager]), reg, 19000),
    'Contents/Definition': definition_stream(registry=reg, document=definition),
}
blob = build_sldprt(streams)
archive = SldprtArchive.from_bytes(blob)
cmgr, ar = load_rooted(archive.require('Contents/CMgr'), reg, 1, 19000)
doc, dar = load_definition(archive.require('Contents/Definition'), reg, 19000)
decoded = cmgr.roots[0]
configs = [entry['o'] for entry in decoded['f370']['items']]
if cmgr.tail or doc.tail:
    raise RuntimeError('fresh graph has unread bytes')
if store_rooted(cmgr, reg, 19000) != streams['Contents/CMgr']:
    raise RuntimeError('configuration graph changed after decoding')
if store_definition(doc, reg, 19000) != streams['Contents/Definition']:
    raise RuntimeError('document graph changed after decoding')
if decoded['f360'] is not configs[0] or decoded['f368'] is not configs[0]:
    raise RuntimeError('current configuration aliases were not preserved')
report = {
    'configuration_names': [config['f18']['f08'] for config in configs],
    'configuration_ids': [config['f08'] for config in configs],
    'next_configuration_id': decoded['f40c'],
    'density_kg_m3': doc.head['f1688'],
    'journal_name': doc.head['ffd8']['f18']['f08'],
    'stream_bytes': {name: len(data) for name, data in streams.items()},
    'container_bytes': len(blob),
    'runtime_reads': reads,
    'vendor_loadable': False,
    'application_usable': False,
}
print(json.dumps(report, ensure_ascii=True))
"""


def RunBuilders(
    Directory: FilePath, Count: int, Density: float, Prefix: str
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-c",
            KProgram,
            str(KRepoRoot),
            str(Count),
            str(Density),
            Prefix,
        ],
        cwd=Directory,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
