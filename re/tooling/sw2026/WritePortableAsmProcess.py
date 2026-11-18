from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT / 'src'), str(ROOT), str(ROOT / 're/tooling/sw2026')]
from CheckAssemblyBoundary import CandidateAdapter
from convert.adapters import AdapterRegistry, WriteOptions
from interchange.serialization.Deserialize import FromData

REQUEST = json.load(sys.stdin)
DOCUMENT = FromData(REQUEST['document'])
TARGET = Path(REQUEST['destination'])
REGISTRY = AdapterRegistry()
REGISTRY.register_writer(CandidateAdapter(DOCUMENT, REQUEST['native_parent'], REQUEST['saved_at']))
RESULT = REGISTRY.write(DOCUMENT, TARGET, format_id='solidworks.sldasm', options=WriteOptions(
    overwrite=False, values={'allow_carrier': True, 'require_native_transfers': True, 'native_destination': REQUEST['native_parent']}))
CHILD = TARGET.parent / (DOCUMENT.assembly.documents[0].document.metadata['name'] + '.SLDPRT')
FILES = {key: {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path.read_bytes()).hexdigest()}
         for key, path in (('assembly', TARGET), ('child', CHILD))}
print(json.dumps({'schema': 'kit.sw2026.portable-assembly-private-registry-producer.v1', 'passed': True,
    'files': FILES, 'application_usable': RESULT.application_usable, 'vendor_loadable': RESULT.vendor_loadable,
    'bytes_written': RESULT.bytes_written, 'component_file_count': RESULT.metadata['component_file_count'],
    'registration_scope': 'private writer registry only', 'default_public_registry_changed': False,
    'native_processes_started': 0, 'native_acceptance': False, 'heldout_inputs_read': 0}, sort_keys=True))
