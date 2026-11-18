from hashlib import sha256
import json
import os
from pathlib import Path
import sys


def check(root, method_sha, label):
    from PreparePerpendicularSlot import fixed_root
    from VerifyPerpendicularFreeze import canonical, digest, load, require

    require(os.name == 'nt', 'the disclosed primary-destination build probe runs only in the root-owned guest')
    folder = Path(r'C:\KitPublicPerpRuntimeProbe121') / method_sha / label / 'Prepared'
    fixed_root(folder)
    folder.mkdir(parents=True, exist_ok=False)
    fixture = load(root / 'Inputs/G01RegistryInput.json')
    child = fixture['document']['assembly']['documents']['$tuple'][0]['document']['metadata']['name']
    case = {'id': 'G01', 'name': fixture['document']['metadata']['name'], 'child_name': child}
    fixture['native_parent'] = str(folder / 'GeneratedInput' / (case['name'] + '.SLDASM'))
    request = canonical({'registry_input': fixture})
    prediction = (root / 'Inputs/G01Prediction.json').read_bytes()
    (folder / 'NeutralRequest.json').write_bytes(request)
    (folder / 'Prediction.json').write_bytes(prediction)
    preparation = {'schema': 'kit.sw2026.public-perpendicular-disclosed-guest-build-preparation.v1',
                   'method_sha256': method_sha, 'case': 'public_G01',
                   'request_sha256': sha256(request).hexdigest(), 'prediction_sha256': sha256(prediction).hexdigest(),
                   'heldout_inputs_read': 0, 'native_source_files_opened': 0, 'native_processes_started': 0}
    (folder / 'PreparationLock.json').write_bytes(canonical(preparation))
    from EvaluatePublicPerpSlot import build

    result = build(root, folder, preparation, case)
    require(result['passed'] and result['actual_normal_registry'] and result['worker_count'] == 3
            and result['runtime_input_file_reads'] == result['native_processes_started'] == 0,
            'the disclosed primary native destination build did not pass before hidden release')
    return {'passed': True, 'case': 'public_G01', 'worker_count': 3,
            'build_lock_sha256': digest(folder / 'BuildLock.json'), 'generated_files': result['generated_files'],
            'actual_guest_primary_destination': True, 'separate_exact_reproduction_and_linked_graph_readback': True,
            'heldout_inputs_read': 0, 'native_source_files_opened': 0, 'native_processes_started': 0,
            'runtime_input_file_reads': 0}
