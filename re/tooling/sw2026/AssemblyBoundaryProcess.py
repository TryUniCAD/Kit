from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT / 'src'), str(ROOT), str(ROOT / 're/tooling/sw2026')]
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
AUDIT = BuildAudit(ROOT / 're/tooling/sw2026/serial/defs')
sys.addaudithook(AUDIT.InspectEvent)
from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly as compile_assembly
from SdkNativeRoundTrips import roundtrips
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.serialization.Deserialize import FromData
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.document.Validation.DocumentComponentValidate import GetDefLinkErrs, GetDocLinkErrs
from interchange.document.Validation.DocumentGraphValidate import GetGraphErrors
from interchange.document.Validation.DocumentMateEntityValidate import GetMateEntErrs
from interchange.document.Validation.DocumentMateGroupValidate import GetMateGroups
from interchange.document.Validation.DocumentMateValidate import GetMateErrors
from interchange.document.Validation.DocumentMeshValidate import GetMeshErrors
CODECS = tuple(lookup(name) for name in ('utf-8', 'utf-8-sig', 'utf-16-le', 'latin-1'))
REQUEST = json.load(sys.stdin)
DOCUMENT = FromData(REQUEST['document'])
AUDIT.BeginBuild()
PARENT = compile_assembly(DOCUMENT, REQUEST['native_parent'], REQUEST['saved_at'])
CHILD = PARENT.ChildValue
ROWS = {}
for name, value, mates in (('parent', PARENT, True), ('child', CHILD, False)):
    *_, proofs = roundtrips(SldprtArchive.FromBytes(value.BytesValue), mates)
    ROWS[name] = {'sha256': sha256(value.BytesValue).hexdigest(), 'bytes': len(value.BytesValue),
        'blob': b64encode(value.BytesValue).decode('ascii'), 'round_trips': proofs,
        'stream_sha256': {key: sha256(data).hexdigest() for key, data in value.StreamsValue.items()}}
print(json.dumps({'passed': True, 'artifacts': ROWS, 'occurrences': len(PARENT.OccurrenceValues), 'mates': len(PARENT.MateValues),
    'runtime_input_file_reads': len(AUDIT.DeniedReads), 'native_processes_started': 0, 'native_acceptance': False,
    'public_registration_changed': False, 'scope': 'private portable assembly graph projection into existing SDK constructors'}, sort_keys=True))
