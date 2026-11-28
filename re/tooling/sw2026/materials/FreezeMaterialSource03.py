from argparse import ArgumentParser
from hashlib import sha256
from math import isclose
from pathlib import Path
import json
import re
from subprocess import check_output, run
import sys


ROOT = Path(__file__).resolve().parents[4]
BASE = '574b573df5f722a6882483049de93562b2215179'
VERSION = '34.5.2.0604'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
DIAGNOSTIC = 'a23e44a29967ad84e2716f66363c2898025460bd5a9dddf266e575bdac3a88d2'
OLD_RESULT = '7ba51e40c30237afd87bbd61f5de1f3f676c525e53269c632f268f11d4e2addb'
OLD_JOB = '292df06a2fd4f740c2070a32152568271eaf1c95be2675a9564e541f4c0b677f'
OLD_MANIFEST = '342283c9e952693fba073c5171a904861dbbcd25e46ed3e10d5d5fc3147fd2c1'
SOURCE_SCHEMA = 'kit.sw2026.assigned-material-native-source.v2'
DIAGNOSTIC_SCHEMA = 'kit.sw2026.assigned-material-selected-body-diagnostic.v1'
MEASUREMENT = {'physical': 'IMassProperty2.selected_solid', 'geometry_and_override_diagnostic': 'IMassProperty'}
MATERIALS = 're/tooling/sw2026/materials/'
UPDATED = ('AuthorAssignedMaterials.py', 'MaterialSourceFacts.py')
TOOLS = (*UPDATED, 'AuthorCurves.py', 'AuthorRectangleAnchors.py', 'InspectFresh.py', 'OracleIdentity.py', 'Swapp.py')
MEMBERS = {'CatalogMetadata01.json', 'Control.SLDPRT', 'Intent/D01Corner.json', 'Intent/D02Center.json',
           'Job.json', 'WrapperShape01.json'} | {'Tools/' + name for name in TOOLS}
RECEIPT = 're/solidworks/measurements/2026/AssignedMaterialDensityProbe01.json'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), 'expected an exact regular artifact: ' + path.name)
    raw = path.read_bytes()
    require(digest(raw) == expected, 'incorrect artifact hash: ' + path.name)
    return raw


def metric_facts(row, expected_density):
    modern = row['selected_mass_property2']
    legacy = row['mass']
    require(modern['use_system_units'] is True and legacy['use_system_units'] is True and not legacy['override_mass']
            and row['legacy_after'] == legacy and legacy['volume'] == modern['volume'] > 0
            and modern['density'] == modern['derived_density'] == expected_density
            and isclose(modern['mass'] / modern['volume'], expected_density, rel_tol=5e-7)
            and legacy['density'] == legacy['mass_over_volume_density'] == 1.0
            and row['body_material'] == {'material': '', 'database': ''} and not row['body_material_id_name'],
            'frozen diagnostic metric or body assignment differs')
    return {
        'selected_density_kg_m3': modern['density'], 'selected_mass_kg': modern['mass'],
        'selected_mass_over_volume_kg_m3': modern['derived_density'], 'volume_m3': modern['volume'],
        'legacy_density_kg_m3': legacy['density'], 'legacy_mass_kg': legacy['mass'],
        'legacy_override_mass': legacy['override_mass'], 'si_units': True,
        'part_material': row['part_material'], 'explicit_body_material': row['body_material'],
    }


def diagnostic_facts(path):
    observation = json.loads(checked(path, DIAGNOSTIC))
    rows = observation['rows']
    require(observation['schema'] == 'kit.sw2026.named-material-density-diagnostic.v1'
            and observation['complete_observations'] and observation['controls_healthy']
            and observation['distinct_native_processes'] == 4 and set(rows) == {'Before', 'Author', 'Reopen', 'After'}
            and all(row['passed'] for row in rows.values())
            and observation['previous_result_sha256'] == OLD_RESULT
            and observation['packet_sha256'] == OLD_JOB
            and not observation['observed_density_hypothesis']
            and not observation['source_lifecycle_qualified'] and not observation['sealed_originals_locked'],
            'diagnostic observation is outside the disclosed healthy bracket')
    identities = [row.get('identity', row.get('oracle_identity')) for row in rows.values()]
    require(all(row['version_matches'] and row['file_version'] == VERSION and row['sha256'] == ORACLE
                for row in identities)
            and len({(row['process_id'], row['process_creation_filetime']) for row in identities}) == 4,
            'native diagnostic process identity differs')
    author = rows['Author']['states']
    reopened = rows['Reopen']['states']
    states = {
        'unassigned': metric_facts(author['unassigned'], 1000.0),
        'assigned': metric_facts(author['assigned'], 2700.0),
        'saved': metric_facts(author['saved'], 2700.0),
        'read_only_reopened': metric_facts(reopened['reopened'], 2700.0),
        'read_only_rebuilt': metric_facts(reopened['assigned'], 2700.0),
    }
    require(states['unassigned']['part_material'] == {'material': '', 'database': ''}
            and all(states[key] == states['assigned'] for key in ('saved', 'read_only_reopened', 'read_only_rebuilt')),
            'frozen diagnostic assignment or persistence differs')
    saved = rows['Author']['file']
    require(saved['diagnostics'] == [True, 0, 0] and saved['bytes'] > 0
            and saved['sha256'] == '04ddbe3934185b0c484ca60579312aac6dc0d2412317cda58d8c518f8d214583',
            'frozen diagnostic save identity differs')
    return {
        'schema': DIAGNOSTIC_SCHEMA, 'build': VERSION, 'native_executable_sha256': ORACLE,
        'native_result_sha256': DIAGNOSTIC, 'packet_02_job_sha256': OLD_JOB,
        'previous_failed_source_result_sha256': OLD_RESULT, 'native_observer_sha256': observation['tool_sha256'],
        'fresh_native_processes': 4, 'healthy_controls': 2,
        'phase_record_sha256': {name: row['record_sha256'] for name, row in rows.items()},
        'prior_combined_legacy_and_modern_predicate': False, 'states': states,
        'diagnostic_save': {key: saved[key] for key in ('sha256', 'bytes', 'diagnostics')},
        'diagnostic_points_to_selected_body_observer': True,
        'source_lifecycle_qualified': False, 'heldout_credit': 0, 'writer_qualified': False,
    }


def git(*args):
    return check_output(('git', *args), cwd=ROOT)


def load_prior(manifest_path):
    require(manifest_path.name == 'NativeSourcePacket02.json', 'expected the frozen packet 02 manifest')
    declared = json.loads(checked(manifest_path, OLD_MANIFEST))
    rows = declared['files']
    root = manifest_path.with_suffix('')
    require(not root.is_symlink() and root.is_dir() and len(rows) == len(MEMBERS)
            and {row['path'] for row in rows} == MEMBERS and declared['job_sha256'] == OLD_JOB,
            'prior disclosed source packet inventory differs')
    raw = {}
    for row in rows:
        name = row['path']
        path = root / name
        require(path.resolve().is_relative_to(root.resolve()), 'prior packet member escaped: ' + name)
        data = checked(path, row['sha256'])
        require(len(data) == row['bytes'], 'prior disclosed artifact length differs: ' + name)
        raw[name] = data
    require(digest(raw['Job.json']) == OLD_JOB and json.loads(raw['Job.json'])['cohort_role'] == 'discovery',
            'only the exact disclosed packet 02 job is allowed')
    return raw


def freeze(previous, revision):
    require(re.fullmatch('[0-9a-f]{40}', revision) and git('rev-parse', revision + '^').decode().strip() == BASE
            and git('rev-parse', revision + ':src') == git('rev-parse', BASE + ':src'),
            'freeze requires the exact independent research commit and unchanged production tree')
    receipt = git('cat-file', 'blob', revision + ':' + RECEIPT)
    summary = json.loads(receipt)
    require(summary['schema'] == DIAGNOSTIC_SCHEMA and summary['native_result_sha256'] == DIAGNOSTIC,
            'commit lacks the exact sanitized evidence')
    freezer = git('cat-file', 'blob', revision + ':' + MATERIALS + Path(__file__).name)
    require(freezer == Path(__file__).read_bytes(), 'running freezer does not match the committed script')
    raw = load_prior(previous)
    old_job = json.loads(raw['Job.json'])
    changed = {name: git('cat-file', 'blob', revision + ':' + MATERIALS + name) for name in UPDATED}
    require(all(data != raw['Tools/' + name] for name, data in changed.items()),
            'the committed source observer/author correction is absent')
    raw.update({'Tools/' + name: data for name, data in changed.items()})
    new_job = {
        **old_job, 'schema': SOURCE_SCHEMA, 'mass_measurement': MEASUREMENT,
        'tools_sha256': {name: digest(raw['Tools/' + name]) for name in TOOLS},
    }
    raw['Job.json'] = encode(new_job)
    job_pin = digest(raw['Job.json'])
    manifest = previous.with_name('NativeSourcePacket03.json')
    root = manifest.with_suffix('')
    require(not manifest.exists() and not manifest.is_symlink(), 'packet 03 manifest already exists')
    root.mkdir(exist_ok=False)
    for name, data in sorted(raw.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(data)
    command = (sys.executable, '-I', '-B', str(root / 'Tools/AuthorAssignedMaterials.py'),
               'verify', str(root / 'Job.json'), '--packet-sha256', job_pin)
    hosted = run(command, capture_output=True, timeout=60, check=False)
    require(hosted.returncode == 0 and not hosted.stderr, 'host packet verifier failed\n' + hosted.stderr.decode())
    verified = json.loads(hosted.stdout)
    require(verified == {'passed': True, 'native_processes': 0, 'writer_outputs': 0}
            and {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()} == MEMBERS
            and all(checked(root / name, digest(data)) == data for name, data in raw.items()),
            'new file inventory or host verifier result differs')
    result = {
        'schema': 'kit.sw2026.assigned-material-source-packet.v2', 'source_revision': revision,
        'predecessor_manifest_sha256': OLD_MANIFEST, 'predecessor_job_sha256': OLD_JOB,
        'diagnostic_receipt_sha256': digest(receipt), 'job_sha256': job_pin, 'source_author_verified_host_only': True,
        'host_verify_stdout': verified, 'writer_outputs': 0, 'heldout_inputs_read': 0, 'native_runs_by_preparer': 0,
        'files': [{'bytes': len(data), 'path': name, 'sha256': digest(data)} for name, data in sorted(raw.items())],
    }
    payload = encode(result)
    with manifest.open('xb') as output:
        output.write(payload)
    require(digest(manifest.read_bytes()) == digest(payload) and digest(previous.read_bytes()) == OLD_MANIFEST,
            'packet publication changed a pinned manifest')
    return {'manifest_sha256': digest(payload), 'job_sha256': job_pin, 'source_revision': revision,
            'verified_files': len(raw), 'native_author_sha256': digest(changed[UPDATED[0]]),
            'material_observer_sha256': digest(changed[UPDATED[1]])}


def main():
    parser = ArgumentParser()
    actions = parser.add_subparsers(dest='action', required=True)
    audit = actions.add_parser('diagnostic')
    audit.add_argument('result', type=Path)
    stage = actions.add_parser('freeze')
    stage.add_argument('prior', type=Path)
    stage.add_argument('--revision', required=True)
    args = parser.parse_args()
    facts = diagnostic_facts(args.result) if args.action == 'diagnostic' else freeze(args.prior.absolute(), args.revision)
    sys.stdout.buffer.write(encode(facts))


if __name__ == '__main__':
    main()
