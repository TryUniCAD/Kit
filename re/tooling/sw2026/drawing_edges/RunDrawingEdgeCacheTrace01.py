from __future__ import annotations

import argparse
from functools import partial
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'Tools'))
import InspectDrawingEdgeQualification01 as baseline
sys.path.insert(0, str(Path(__file__).resolve().parent))


BASE_TRIAL = '36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872'
SCHEMA = 'kit.sw2026.drawing-edge-cache-two-stop.v1'
TRACE_TOOLS = {'DrawingSaveAggregateDbgEng.py', 'DrawingSavePreviewGateDbgEng.py', 'DrawingSavePropertiesGateDbgEng.py',
               'DrawingEdgeCacheTrace01.py', 'ObserveDrawingEdgeCache01.py', 'RunDrawingEdgeCacheTrace01.py'}


def verify(path, expected):
    baseline.require(baseline.digest(path) == expected, 'two-stop trace packet changed')
    config = json.loads(path.read_bytes())
    baseline.require(config['schema'] == SCHEMA and config['base_trial_sha256'] == BASE_TRIAL
                     and config['heldout_inputs_read'] == 0 and config['native_acceptance'] is False,
                     'unexpected cache-source trace')
    baseline.require(set(config['trace_tools_sha256']) == TRACE_TOOLS, 'complete two-stop observer closure is required')
    root = path.parent.resolve(strict=True)
    baseline.require(Path(__file__).resolve().parent == root / 'TraceTools', 'trace must run from its own exact packet')
    for name, value in config['trace_tools_sha256'].items():
        baseline.checked(root, 'TraceTools/' + name, value)
    request = baseline.verify(root / 'Trial.json', BASE_TRIAL)
    prior = json.loads(baseline.checked(root, 'RequiredBaseline.json', config['required_baseline_sha256']).read_bytes())
    baseline.require(prior.get('passed') is True and prior.get('packet_sha256') == BASE_TRIAL
                     and prior.get('controls_healthy') is True and prior.get('distinct_processes') == 6
                     and len(prior.get('phases') or {}) == 6 and all(value['passed'] for value in prior['phases'].values()),
                     'the exact ordinary native annotation lifecycle must pass before this optional trace')
    return config, request


def dispatch(config_path, config_sha, packet, packet_sha, output, role, case, *, source, source_sha, prior=None, tree=None):
    directory = output / role
    job = {'packet': str(packet), 'packet_sha256': packet_sha, 'case': case, 'directory': str(directory),
           'source': str(source), 'source_sha256': source_sha, 'prior': prior, 'tree': tree,
           'trace_config': str(config_path), 'trace_config_sha256': config_sha}
    job_path = output / (role + '.job.json')
    baseline.write_json(job_path, job)
    try:
        process = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), 'worker', str(job_path)], capture_output=True, text=True, timeout=240, check=False)
        captured = {'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr, 'timed_out': False}
    except subprocess.TimeoutExpired as error:
        captured = {'exit_code': None, 'stdout': str(error.stdout or ''), 'stderr': str(error.stderr or ''), 'timed_out': True}
    baseline.write_json(output / (role + '.transport.json'), captured)
    result = json.loads((directory / 'Result.json').read_bytes()) if (directory / 'Result.json').is_file() else {'passed': False}
    result['worker_exit_code'] = captured['exit_code']
    result['worker_timed_out'] = captured['timed_out']
    result['passed'] = bool(result['passed'] and captured['exit_code'] == 0 and not captured['timed_out'])
    return result


def worker(job):
    config, request = verify(Path(job['trace_config']), job['trace_config_sha256'])
    baseline.require(os.name == 'nt' and job['case'] in request['cases'] and job['packet_sha256'] == BASE_TRIAL, 'trace worker requires the exact owned disclosed input')
    import AuthorCurves as curves
    import Swapp
    from ObserveDrawingEdgeCache01 import save_with_edge_trace

    active = {}
    original_author = curves.CurveAuthor
    original_save = Swapp.Sw.save_as

    class TraceAuthor(original_author):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            active['author'] = self

    def observed_save(controller, model, target):
        author = active.get('author')
        baseline.require(author is not None and author.model is model, 'cache trace lacks the exact active oracle document')
        drawing = author.typed(model, 'DrawingDoc')
        status, trace, evaluation = save_with_edge_trace(controller, author, drawing, target, Path(config['debugger_directory']),
                                                         save_operation=partial(original_save, controller))
        active['trace'], active['evaluation'] = trace, evaluation
        return status

    curves.CurveAuthor, Swapp.Sw.save_as = TraceAuthor, observed_save
    try:
        result = baseline.phase(Path(job['packet']), job['packet_sha256'], job['case'], Path(job['directory']), Path(job['source']),
                                job['source_sha256'], prior=job['prior'], expected_tree=job['tree'])
    finally:
        curves.CurveAuthor, Swapp.Sw.save_as = original_author, original_save
    result['annotation_geometry_lifecycle_passed'] = result['passed']
    if job['prior'] is None:
        trace, evaluation = active.get('trace') or {}, active.get('evaluation') or {}
        events = [ordinal for ordinal, offset in trace.get('save_events', ()) if offset <= trace.get('save_returned_offset_ns', -1)]
        source_gate = bool(evaluation.get('paired_cache_lookup_observed') and evaluation.get('nonnull_cache_reference_observed')
                           and events == [7, 9, 28])
        result.update(cache_source_observer=trace, cache_source_evaluation=evaluation, pre_event7_source_gate_passed=source_gate)
        result['passed'] = bool(result['passed'] and source_gate)
    else:
        result['pre_event7_source_gate_passed'] = job['prior'].get('pre_event7_source_gate_passed') is True
        result['passed'] = bool(result['passed'] and result['pre_event7_source_gate_passed'])
    result['selected_annotation_edge_joined_to_sampled_id'] = False
    result['generated_downstream_writer_qualified'] = False
    baseline.write_json(Path(job['directory']) / 'Result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('verify', 'run', 'worker'))
    parser.add_argument('path', type=Path)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.command == 'worker':
        result = worker(json.loads(args.path.read_bytes()))
        return 0 if result['passed'] else 3
    baseline.require(args.sha256 is not None, 'frozen two-stop manifest hash is required')
    config_path = args.path.resolve(strict=True)
    config, request = verify(config_path, args.sha256)
    if args.command == 'verify':
        print(json.dumps({'passed': True, 'cad_processes_started': 0, 'native_acceptance': False}))
        return 0
    baseline.require(os.name == 'nt', 'only the root may run the reserved Windows oracle')
    baseline.dispatch = partial(dispatch, config_path, args.sha256)
    result = baseline.run(config_path.parent / 'Trial.json', BASE_TRIAL)
    result.update(trace_config_sha256=args.sha256, selected_annotation_edge_joined_to_sampled_id=False,
                  generated_downstream_writer_qualified=False, native_acceptance=False)
    baseline.write_json(config_path.parent / 'Inspection/Result.json', result)
    print(json.dumps({key: result[key] for key in ('passed', 'controls_healthy', 'distinct_processes', 'generated_downstream_writer_qualified')}))
    return 0 if result['passed'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
