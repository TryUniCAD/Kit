from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import EvaluatePerpendicularSlot as prior


def build(root, folder, preparation_record, case):
    prior.require(not (folder / 'BuildLock.json').exists(), 'preserve every previous public-registry build')
    envelope = prior.load(folder / 'NeutralRequest.json')
    fixture = envelope['registry_input']
    code = root / 'CodeRoot'
    names = {'parent': case['name'] + '.SLDASM', 'child': case['child_name'] + '.SLDPRT'}
    generated = folder / 'GeneratedInput'
    prior.require(fixture['native_parent'] == str(generated / names['parent']),
                  'the first public build must use the actual native final destination')
    outputs, workers = [], []
    for tag, directory in (('BuildA', generated), ('BuildB', folder / 'GeneratedReplica')):
        incoming = deepcopy(fixture)
        incoming.update(output=str(directory), allow_unqualified=True)
        value, worker = prior.process([sys.executable, '-I', '-B', str(root / 'RegistryTools/GuardPublicPerpBuild.py'), str(code)],
                                      prior.canonical(incoming), folder, tag)
        prior.require(value['passed'] and value['admitted'] and value['writer_output_count'] == 2
                      and value['round_trips'] == 22 and value['runtime_input_file_reads'] == value['native_processes_started'] == 0
                      and value['sdk_runtime_research_imports'] == value['cad_runtime_modules'] == 0
                      and value['vendor_loadable'] is False and value['application_usable'] is False,
                      'the actual normal-registry build crossed its frozen unqualified source-only boundary')
        outputs.append(value)
        workers.append(worker)
    prior.require(outputs[0]['artifacts'] == outputs[1]['artifacts'] and workers[0] != workers[1],
                  'normal registry output did not reproduce complete native files in separate processes')
    request = {'parent': str(generated / names['parent']), 'child': str(generated / names['child']),
               'prediction': prior.load(folder / 'Prediction.json')}
    readback, worker = prior.process([sys.executable, '-I', '-B', str(root / 'WriterTools/VerifyPerpendicularGraph.py'),
                                     '--root', str(code)], prior.canonical(request), folder, 'TypedReadback')
    prior.require(readback['passed'] and len(set([*workers, worker])) == 3,
                  'the actual complete public graph differs from its pre-observation prediction')
    sys.path[:0] = [str(code / 'src'), str(code)]
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    archive = SldprtArchive.from_bytes((generated / names['parent']).read_bytes())
    linked = ReadNativeLink(archive, 0)
    mate, = ReadMatesMut(archive.require('Contents/Config-0-MatesList'), linked.ResolvedValue).RootsValue
    prior.write(folder / 'GeneratedIdentity.json', {'mate_id': mate.FieldsValue['f08'],
                'endpoints': readback['actual_owned_endpoints']})
    prior.write(folder / 'Case.json', case)
    for name in ('ControlCase.json', 'ControlState.json'):
        (folder / name).write_bytes((root / 'Inputs' / name).read_bytes())
    files = {role: {'sha256': prior.digest(generated / name), 'bytes': (generated / name).stat().st_size}
             for role, name in names.items()}
    lock = {'schema': 'kit.sw2026.perpendicular-sealed-generated-build-lock.v1',
            'preparation_lock_sha256': prior.digest(folder / 'PreparationLock.json'),
            'request_sha256': preparation_record['request_sha256'], 'prediction_sha256': preparation_record['prediction_sha256'],
            'generated_names': names, 'generated_files': files,
            'generated_identity_sha256': prior.digest(folder / 'GeneratedIdentity.json'),
            'case_sha256': prior.digest(folder / 'Case.json'), 'runtime_input_file_reads': 0,
            'sdk_runtime_research_imports': 0, 'native_processes_started': 0,
            'native_source_files_opened': 0, 'native_source_observations_opened': 0,
            'worker_count': 3, 'actual_normal_registry': True, 'existing_public_defaults_preserved': True,
            'new_profile_native_flags': False, 'second_worker_uses_explicit_same_native_identity': True}
    lock_sha = prior.write(folder / 'BuildLock.json', lock)
    return {'passed': True, 'build_lock_sha256': lock_sha, 'generated_files': files, 'worker_count': 3,
            'runtime_input_file_reads': 0, 'sdk_runtime_research_imports': 0, 'native_processes_started': 0,
            'actual_normal_registry': True, 'public_writer_qualified': False}


prior.build = build


if __name__ == '__main__':
    prior.main()
