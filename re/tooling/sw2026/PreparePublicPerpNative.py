import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys


PROOF = 'dac307b3371f6102aa036684a60f9b6613c0e425bab2aa591a984aa14e360539'
PREVIOUS = '652c2ab4b79e087bf99727cc04b05ca4bae12e132a33db2d73f9173d8cc73127'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def checked(path, expected):
    require(path.is_file() and not path.is_symlink() and digest(path) == expected,
            'a declared public-registry source or proof changed')
    return path


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def system(value, assembly=False):
    folders = value.FolderNames if assembly else value.FolderValues
    return {'folders': [list(row) for row in folders], 'planes': dict(value.PlaneNames),
            'cabinet_name': value.CabinetName, 'origin_name': value.OriginName}


def tree_intent(root, fixture):
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root / 'src'), str(root)]
    from dataclasses import replace
    from interchange.serialization.Deserialize import FromData
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
    from convert.adapters.solidworks.Core.AssemblyPreparation.Children.MakeChildRecipe import MakeChildRecipe
    from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import ReadAsmPlanes
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
    from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
    from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
    document = FromData(fixture['document'])
    document.assert_valid()
    model = ReadAsmModel(document)
    root_planes, child_planes = ReadAsmPlanes(document), ReadAsmPlanes(model.ChildDocument)
    child = replace(model.ChildDocument, support_planes=(child_planes['z'],))
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, fixture['native_parent'], fixture['saved_at'])
    child_recipe = MakeChildRecipe(child, ProjectRectDims(child), child_planes, paths.ChildValue)
    root_recipe = MakeAsmRecipe(model, child_recipe, root_planes, paths.ParentValue)
    root_system = system(root_recipe.SystemValue, True)
    root_system['mate_group_name'] = root_recipe.SystemValue.MateGroupName
    return {'assembly': {'system': root_system}, 'child': {'settings': {'system': system(child_recipe.SystemValue)}},
            'occurrences': [{'name': value.name} for value in model.Occurrences],
            'mates': [{'name': value.name} for value in sorted(model.GraphValue.mates, key=lambda value: value.order)]}


def main():
    parser = argparse.ArgumentParser()
    for key in ('candidate', 'previous-native', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--guest-root', required=True)
    args = parser.parse_args()
    base, previous = (value.resolve(strict=True) for value in (args.candidate, args.previous_native))
    proof = load(checked(base / 'Proof01/RegistryProof.json', PROOF))
    require(proof['passed'] and proof['distinct_process_count'] == 27 and proof['runtime_input_file_reads'] == 0
            and proof['public_native_qualification'] is False and proof['shared_registry_changed'] is False,
            'the isolated real-registry proof is not complete')
    closure = load(checked(base / 'Proof01/SourceManifest.json', proof['source_manifest_sha256']))
    for label, directory in (('candidate', 'CodeRoot01'), ('baseline', 'BaselineRoot01'), ('tools', 'Tools01'), ('fixtures', 'Fixtures01')):
        for name, expected in closure[label].items():
            checked(base / directory / name, expected)
    prior = load(checked(previous / 'Job.json', PREVIOUS))
    for name, expected in prior['tools_sha256'].items():
        checked(previous / 'Tools' / name, expected)
    require(load(previous / 'Inspection/Result.json')['passed'] is True,
            'the disclosed reused observer has no healthy completed native lifecycle')
    fixture = load(base / 'Fixtures01/G01.json')
    guest = PureWindowsPath(args.guest_root)
    require(guest.is_absolute() and fixture['native_parent'] == str(guest / 'GeneratedInput/NeutralPerpPair.SLDASM'),
            'this packet must retain the exact final destination used by the registry writer')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    tools = output / 'Tools'
    tools.mkdir()
    for name in prior['tools_sha256']:
        copyfile(previous / 'Tools' / name, tools / name)
    for path in Path(__file__).parent.glob('*.py'):
        copyfile(path, tools / path.name)
    sys.path.insert(0, str(tools))
    from PerpendicularNativePlan import case_from_spec, check_predictions, native_trees
    from PredictPublicPerp import intent, predict
    edit = {key: load(previous / 'Spec.json')[key] for key in ('edit_depth_m', 'edit_rotation_deg')}
    independent_intent = intent(fixture, edit)
    predicted = predict(fixture, edit)
    spec = deepcopy(load(previous / 'Spec.json'))
    spec['size_m'] = [independent_intent[key] for key in ('width_m', 'height_m', 'depth_m')]
    for index, value in enumerate(spec['placements']):
        value['translation_m'] = independent_intent['matrices'][index][9:12]
    case = case_from_spec(spec)
    check_predictions(case, predicted)
    roles = tree_intent(base / 'CodeRoot01', fixture)
    trees = native_trees(roles)
    require('Lights and Cameras' in [row[0] for row in trees['child']],
            'the ordinary existing public child role was unexpectedly changed')
    names = {'parent': spec['name'] + '.SLDASM', 'child': spec['child_name'] + '.SLDPRT'}
    recorded = next(value['result'] for value in proof['registry_cases'] if value['tag'] == 'G01Default')
    generated = {}
    for directory in ('FrozenGenerated', 'GeneratedInput'):
        (output / directory).mkdir()
        for role, name in names.items():
            source = checked(base / 'Proof01/G01Default' / name, recorded['artifacts'][role]['sha256'])
            copyfile(source, output / directory / name)
            generated[name] = {'sha256': digest(source), 'bytes': source.stat().st_size,
                               'encoded_path': str(guest / 'GeneratedInput' / name)}
    for source, target in ((base / 'Fixtures01/G01.json', 'RegistryInput.json'),
                           (base / 'Proof01/RegistryProof.json', 'RegistryProof.json'),
                           (base / 'Proof01/SourceManifest.json', 'SourceManifest.json'),
                           (previous / 'PreWriterSourceLock.json', 'PreWriterSourceLock.json'),
                           (previous / 'ControlCase.json', 'ControlCase.json'),
                           (previous / 'ControlState.json', 'ControlState.json')):
        copyfile(source, output / target)
    for name, value in (('EditIntent.json', edit), ('PortableIntent.json', independent_intent), ('Spec.json', spec),
                        ('Case.json', case), ('Prediction.json', predicted), ('TreeIntent.json', roles), ('Trees.json', trees)):
        write(output / name, value)
    read_request = {'parent': str(output / 'FrozenGenerated' / names['parent']),
                    'child': str(output / 'FrozenGenerated' / names['child']), 'prediction': predicted}
    read = subprocess.run([sys.executable, '-I', '-B', str(base / 'CodeRoot01/re/tooling/sw2026/VerifyPerpendicularGraph.py'),
                           '--root', str(base / 'CodeRoot01')], input=json.dumps(read_request, allow_nan=False).encode(),
                          capture_output=True, timeout=180)
    (output / 'TypedReadback.stdout.json').write_bytes(read.stdout)
    (output / 'TypedReadback.stderr.txt').write_bytes(read.stderr)
    require(read.returncode == 0 and load(output / 'TypedReadback.stdout.json')['passed'],
            'the actual registry bundle does not match the independent typed geometry: ' + read.stderr.decode()[-1600:])
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    archive = SldprtArchive.from_bytes((output / 'FrozenGenerated' / names['parent']).read_bytes())
    linked = ReadNativeLink(archive, 0)
    mate, = ReadMatesMut(archive.require('Contents/Config-0-MatesList'), linked.ResolvedValue).RootsValue
    write(output / 'GeneratedIdentity.json', {'mate_id': mate.FieldsValue['f08'],
          'endpoints': load(output / 'TypedReadback.stdout.json')['actual_owned_endpoints'],
          'basis': 'actual public-registry bytes independently decoded with shared linked MatesList and child datum owners'})
    source_receipt = {'registry_proof_sha256': PROOF, 'source_manifest_sha256': proof['source_manifest_sha256'],
                     'actual_registry_result': recorded, 'public_defaults_preserved': True,
                     'qualification_flags_before_native': False, 'actual_carrier_capabilities': [],
                     'research_unqualified_publication_opt_in': True, 'strict_policy_rejects_before_publication': True,
                     'hidden_values_used': False, 'source_only_generated_pair': True,
                     'prediction_from_actual_portable_input': True, 'native_acceptance': False}
    write(output / 'GenerationReceipt.json', source_receipt)
    job = {'schema': 'kit.sw2026.private-public-perpendicular-native-packet.v1', 'guest_root': str(guest),
           'oracle_sha256': prior['oracle_sha256'], 'source_manifest_sha256': proof['source_manifest_sha256'],
           'registry_result_sha256': PROOF, 'prewriter_source_lock_sha256': prior['prewriter_source_lock_sha256'],
           'tools_sha256': {path.name: digest(path) for path in sorted(tools.glob('*.py'))},
           'inputs_sha256': {path.name: digest(path) for path in sorted(output.glob('*.json'))},
           'generated_names': names, 'generated_files': generated, 'control_files': prior['control_files'],
           'phase_order': ['control-before', 'generated', 'reopen', 'control-after'],
           'trailing_control_independent': True, 'source_controls_read_only': True, 'save_order': ['child', 'parent'],
           'immutable_input_pair': True, 'native_acceptance': False, 'public_writer_qualified': False,
           'heldout_inputs_read': 0, 'native_processes_started': 0, 'shared_registry_changed': False,
           'active_angular_correction_proven': False,
           'scope': 'actual normal-registry output with existing public defaults and one ordinary principal-plane perpendicular mate'}
    job_sha = write(output / 'Job.json', job)
    entry = ['py', '-3.12', '-B', str(guest / 'Tools/InspectPublicPerpNative.py')]
    common = [str(guest / 'Job.json'), '--packet-sha256', job_sha]
    recipe = {'packet_sha256': job_sha, 'verify': entry + ['verify', *common],
              'phases': {phase: entry + ['run', *common, '--phase', phase] for phase in job['phase_order']},
              'summary': entry + ['summary', *common], 'phase_timeout_seconds': 900,
              'always_run_trailing_control_independently': True, 'no_automatic_process_termination': True,
              'progress': str(guest / 'Inspection'), 'heldout_inputs_read': 0, 'native_processes_started': 0}
    recipe_sha = write(output / 'Recipe.json', recipe)
    print(json.dumps({'packet_sha256': job_sha, 'recipe_sha256': recipe_sha, 'files': generated,
                      'observer_sha256': job['tools_sha256']['InspectPublicPerpNative.py'],
                      'reused_native_observer_sha256': job['tools_sha256']['InspectGeneratedPerpendicular.py'],
                      'native_processes_started': 0, 'heldout_inputs_read': 0}, indent=2))


if __name__ == '__main__':
    main()
