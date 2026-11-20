from argparse import ArgumentParser
from pathlib import Path
import json
import os
import sys

TOOL = Path(__file__).resolve()
sys.path.insert(0, str(TOOL.parent))

import ProbeThroughMultiStock01 as multi


PACKET = 'ThroughAllBodies02'
SCHEMA = 'kit.sw2026.disclosed-through-all-unrestricted-scope.v1'
GUEST = multi.GUEST.with_name(PACKET)
PHASES = ('Before', 'AllBodiesAuthor', 'AllBodiesReopen', 'After')
PREVIOUS = {
    'packet': 'ThroughMultiStock03',
    'freeze_sha256': '76e4f9205867ce93230b7d35a52fbf7ddf4686ea19a8e75ef91ed7973e4d0397',
    'native_summary_sha256': 'b0e0eddd721f8beb756cf081100671631815c1fe740804369bb108c817207f77',
    'observed_source_sha256': '748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3',
}


def freeze():
    from ProbeThroughAutoScope01 import disclosed

    multi.need(os.name != 'nt', 'prepare the disclosed comparison on the host')
    prior = multi.prior_freeze(PREVIOUS)
    trial = disclosed(multi.SHARED / multi.DISCLOSED)
    values = multi.predictions()
    multi.need(prior['design'] == multi.DESIGN and prior['predictions'] == values
               and prior['disclosed_control_sha256'] == trial['files_sha256'][trial['control_file']],
               'the unrestricted comparison changed the original geometry, predictions or control')
    root = multi.SHARED / PACKET
    root.mkdir(mode=0o700, exist_ok=False)
    tools = {}
    for path in (TOOL, TOOL.with_name(Path(multi.__file__).name), TOOL.with_name(multi.CONTROL)):
        data = path.read_bytes()
        with (root / path.name).open('xb') as output:
            output.write(data)
        tools[path.name] = multi.digest(data)
    plan = {
        'schema': SCHEMA, 'guest': str(GUEST), 'phase_order': PHASES,
        'design': multi.DESIGN, 'predictions': values, 'previous_attempt': PREVIOUS,
        'disclosed_control_sha256': prior['disclosed_control_sha256'],
        'disclosed_trial_sha256': multi.TRIAL, 'tool_sha256': tools,
        'oracle_build': multi.BUILD, 'oracle_exe_sha256': multi.ORACLE,
        'use_feature_scope': False, 'use_auto_select': False,
    }
    return {'freeze_sha256': multi.publish(root / 'Freeze.json', plan),
            'tool_sha256': tools, 'native_processes_started': 0, 'sealed_payloads_read': 0}


def summary(folder, pin, metadata_sha):
    rows = {phase: multi.prior_phase(folder, phase) for phase in PHASES
            if (folder / phase / 'Record.json').is_file()}
    process_times = [row['result']['native_identity']['process_creation_filetime']
                     for row in rows.values() if 'native_identity' in row['result']]
    ordered = list(rows.values())
    serial = all(a['finished_at'] <= b['started_at'] for a, b in zip(ordered, ordered[1:]))
    healthy = (serial and len(set(process_times)) == len(process_times)
               and all(phase in rows and rows[phase]['passed'] for phase in ('Before', 'After')))
    outcome = None
    if healthy and all(phase in rows and rows[phase]['passed'] for phase in PHASES[1:3]):
        author, reopened = (rows[phase]['result'] for phase in PHASES[1:3])
        initial = (author['after_save'], reopened['cold'], reopened['before_edit'])
        edited = (author['after_edit'], reopened['after_edit'])
        source = author['saved_sha256']
        outcome = {
            'save_sha256': source,
            'fresh_reopen_matches_save': reopened['opened_sha256'] == source
                                         and multi.same_measured_model(initial[0], initial[1]),
            'initial_moving_body_cut': [row['moving_stock_cut'] for row in initial],
            'edited_moving_body_cut': [row['moving_stock_cut'] for row in edited],
            'initial_scope': [row['cut_scope'] for row in initial],
            'edited_scope': [row['cut_scope'] for row in edited],
            'initial_moving_stock': initial[-1]['bodies'][multi.MOVING],
            'edited_moving_stock': edited[-1]['bodies'][multi.MOVING],
            'edited_states_match': multi.same_measured_model(*edited),
            'numeric_checks': [len(rows[phase]['checks']) for phase in PHASES[1:3]],
        }
        outcome['passed'] = (outcome['fresh_reopen_matches_save'] and outcome['edited_states_match']
                             and not any(outcome['initial_moving_body_cut']) and all(outcome['edited_moving_body_cut'])
                             and all(row['cut_scope']['feature_scope'] is False for row in (*initial, *edited)))
    result = {
        'schema': SCHEMA, 'freeze_sha256': pin, 'api_sha256': metadata_sha,
        'passed': bool(outcome and outcome['passed']), 'healthy_bracket': healthy,
        'distinct_processes': len(set(process_times)), 'serial': serial, 'outcome': outcome,
        'phase_status': {phase: row['passed'] for phase, row in rows.items()},
        'phase_receipts': {phase: multi.digest((folder / phase / 'Record.json').read_bytes()) for phase in rows},
        'sealed_payloads_read': 0, 'production_coverage': 0, 'heldout_coverage': 0,
    }
    return result | {'result_sha256': multi.publish(folder / 'Result.json', result)}


def guest(args):
    from ProbeThroughAutoScope01 import disclosed, measure

    multi.need(os.name == 'nt', 'registered API and native phases require the Windows guest')
    plan = json.loads(multi.checked(args.manifest, args.pin))
    root = args.manifest.parent
    multi.need(root == Path(GUEST) and plan['guest'] == str(GUEST) and TOOL == root / TOOL.name
               and plan['schema'] == SCHEMA and plan['phase_order'] == list(PHASES)
               and plan['disclosed_trial_sha256'] == multi.TRIAL and plan['previous_attempt'] == PREVIOUS
               and plan['oracle_exe_sha256'] == multi.ORACLE and plan['oracle_build'] == multi.BUILD
               and plan['design'] == multi.DESIGN
               and plan['use_feature_scope'] is False and plan['use_auto_select'] is False,
               'the frozen unrestricted comparison changed')
    for name in (TOOL.name, Path(multi.__file__).name, multi.CONTROL):
        multi.checked(root / name, plan['tool_sha256'][name])
    trial_root = root.with_name(multi.DISCLOSED)
    trial = disclosed(trial_root)
    multi.need(plan['disclosed_control_sha256'] == trial['files_sha256'][trial['control_file']],
               'disclosed control changed')
    sys.path.insert(0, str(trial_root / 'Tools'))
    folder = Path('C:/KitSdkCandidates') / PACKET
    multi.need(folder.resolve() == folder and not folder.is_symlink(), 'owned work folder is redirected')
    metadata = folder / 'ApiMetadata.json'
    if args.mode == 'metadata':
        api = multi.installed_api()
        folder.mkdir(exist_ok=False)
        return {'metadata_sha256': multi.publish(metadata, {'freeze_sha256': args.pin, 'api': api}),
                'native_processes_started': 0}
    raw = metadata.read_bytes()
    multi.need(json.loads(raw)['freeze_sha256'] == args.pin, 'metadata is not bound to this packet')
    metadata_sha = multi.digest(raw)
    if args.mode == 'summary':
        return summary(folder, args.pin, metadata_sha)
    if args.phase in ('Before', 'After'):
        return measure(folder, args.phase, trial_root, trial)
    multi.need(multi.prior_phase(folder, 'Before')['passed'], 'the leading healthy control is absent')
    if args.phase == 'AllBodiesReopen':
        multi.need(multi.prior_phase(folder, 'AllBodiesAuthor')['passed'], 'no qualified original save')
    return multi.candidate(folder, args.phase, plan, metadata_sha)


def main():
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest='mode', required=True)
    modes.add_parser('freeze')
    for mode in ('metadata', 'phase', 'summary'):
        command = modes.add_parser(mode)
        command.add_argument('manifest', type=Path)
        command.add_argument('pin')
        if mode == 'phase':
            command.add_argument('phase', choices=PHASES)
    args = parser.parse_args()
    result = freeze() if args.mode == 'freeze' else guest(args)
    sys.stdout.buffer.write(multi.wire(result))
    return int(result.get('passed') is False)


if __name__ == '__main__':
    sys.exit(main())
