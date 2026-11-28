from __future__ import annotations

import argparse
import importlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
import BlankRewriteHeldoutCommon as common
import BlankRewriteRetry as retry


def prepare(args):
    common.require(os.name == 'nt', 'private preparation is guest only')
    root, method = common.packet()
    common.verify_source(root, method)
    legacy_job = common.guest_path(args.legacy_job)
    legacy_descriptor = {'path': str(legacy_job), 'sha256': args.legacy_job_sha256}
    context = common.custody(legacy_descriptor, root, method)
    output = common.guest_path(args.output_root)
    common.require(not output.exists() and not output.is_relative_to(Path('C:/KitBlankDrawingSource121')), 'use an unused separate guest output')
    output.mkdir(parents=True, exist_ok=False)
    value = {
        'schema': 'kit.sw2026.blank-preserved-rewrite-heldout-binding.v1',
        'method_sha256': common.fingerprint(root / 'Method.json'),
        'tools_sha256': method['tools_sha256'],
        'writer_manifest_sha256': method['writer_manifest_sha256'],
        'legacy_job': legacy_descriptor,
        'output_root': str(output),
        'python': sys.executable,
        'prior_canonical_hashes': method['prior_output_sha256'],
        'prior_metadata_verified': True,
        'canonical_payload_reads_before_binding': 0,
        'native_original_payload_reads': 0,
    }
    result = common.write_new(output / 'Binding.json', value)
    return {'schema': 'kit.sw2026.blank-rewrite-heldout-prepare-export.v1', 'passed': True, 'binding_sha256': result['sha256'], 'method_sha256': value['method_sha256'], 'private_values_exported': False}


def generation(binding, method, output, context, root):
    legacy, code, prior_job, bound, locked, predictions, canonical = context
    legacy.generation_gate(code, prior_job, bound, locked, True)
    candidates = {}
    build_rows = []
    for slot in common.SLOTS:
        target = output / 'Payloads' / slot / method['filenames'][slot]
        reports = []
        for index in (1, 2):
            report_path = output / 'Builds' / f'{slot}_{index}.json'
            command = [sys.executable, '-I', '-B', str(root / 'Tools/BuildGuestBlankRewrite01.py'), '--code', str(root / 'Sdk'), '--manifest', str(root / 'WriterManifest.json'), '--manifest-sha256', method['writer_manifest_sha256'], '--source', canonical[slot]['path'], '--source-sha256', canonical[slot]['sha256'], '--target', str(target), '--epoch', str(method['save_epochs'][slot]), '--report', str(report_path)]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
            logs = output / 'BuildLogs'
            logs.mkdir(parents=True, exist_ok=True)
            (logs / f'{slot}_{index}.stdout').write_text(completed.stdout)
            (logs / f'{slot}_{index}.stderr').write_text(completed.stderr)
            common.require(completed.returncode == 0 and report_path.is_file(), 'canonical rewrite build failed')
            reference = common.descriptor(report_path)
            report = common.load(reference)
            common.require(report['passed'] and report['writer_manifest_sha256'] == method['writer_manifest_sha256'] and Path(report['source']['path']).resolve() == Path(canonical[slot]['path']).resolve() and report['source']['sha256'] == canonical[slot]['sha256'] and report['native_flags'] == [False, False], 'rewrite build provenance differs')
            common.require(report['runtime_input_reads'] == report['native_launches'] == report['original_native_source_files_read'] == 0 and report['private_canonical_source_files_read'] == 1 and report['unchanged_layout'] and report['source_owners_preserved'], 'rewrite dropped state or used unapproved runtime')
            common.require(report['explicit_saved_at'] == method['save_epochs'][slot] and report['actual_self_path'] == str(target), 'explicit save event or self locator differs')
            common.require(report['expected_tree'] == predictions[slot]['tree'], 'source tree witness differs')
            code.same_snapshot(report['expected_initial'], predictions[slot]['initial'])
            common.require(common.fingerprint(target) == report['target']['sha256'], 'actual generated output differs')
            reports.append((reference, report))
            if index == 1:
                replay = output / 'IndependentFirstBuild' / slot
                replay.parent.mkdir(parents=True, exist_ok=True)
                target.parent.rename(replay)
                first = replay / target.name
        common.require(reports[0][1]['target']['sha256'] == reports[1][1]['target']['sha256'] and first.read_bytes() == target.read_bytes(), 'independent same-path builds differ')
        candidates[slot] = common.descriptor(target)
        build_rows.append({'slot': slot, 'reports': [row[0] for row in reports], 'first_output': common.descriptor(first), 'second_output': candidates[slot], 'identical': True})
    value = {'schema': 'kit.sw2026.blank-preserved-rewrite-heldout-generation.v1', 'binding_sha256': binding['sha256'], 'writer_manifest_sha256': method['writer_manifest_sha256'], 'prior_generation_sha256': method['prior_generation_sha256'], 'canonical_sources': canonical, 'rewritten': candidates, 'builds': build_rows, 'all_outputs_frozen_before_native': True, 'original_native_payload_reads': 0}
    return common.write_new(output / 'Generation.json', value)


def worker(args):
    root, method, binding, output = common.binding(args.binding, args.binding_sha256)
    context = common.custody(binding['legacy_job'], root, method)
    legacy, code, prior_job, bound, locked, predictions, canonical = context
    frozen = common.load({'path': str(output / 'Generation.json'), 'sha256': args.generation_sha256})
    common.require(frozen['binding_sha256'] == args.binding_sha256 and frozen['all_outputs_frozen_before_native'], 'native generation gate differs')
    base, stage = args.phase.rsplit('/', 1)
    common.require(base in common.BASES and stage in common.STAGES, 'native phase differs')
    slot = base.split('/')[0]
    wanted = predictions[slot] if slot in common.SLOTS else legacy.expected_for(code, base, predictions)
    native = canonical[slot] if slot in common.SLOTS and base.endswith('/Source') else frozen['rewritten'][slot] if slot in common.SLOTS else prior_job['control']
    if stage == 'FreshReopen':
        previous = common.load({'path': str(output / 'Workers' / (base.replace('/', '_') + '_OpenEditSave.json')), 'sha256': args.prior_sha256})
        common.require(previous['passed'] and previous['name'] == base + '/OpenEditSave', 'fresh reopen prerequisite failed')
        raw = common.load(previous['record'])['result']
        native = {'path': str(output / 'Native' / base / 'OpenEditSave' / 'EditedDrawing.SLDDRW'), 'sha256': raw['derivative_sha256']}
    import Swapp
    from OracleIdentity import application_identity
    from InspectDrawingCache import phase
    result = phase(Swapp, application_identity, directory=output / 'Native' / args.phase, native=Path(native['path']), expected_hash=native['sha256'], expected=wanted['initial'] if stage == 'OpenEditSave' else wanted['edited'], tree=wanted['tree'], oracle_sha=code.ORACLE, edit=stage == 'OpenEditSave', edited_ratio=wanted['edited']['sheet_properties'][2:4])
    return {'schema': 'kit.sw2026.blank-rewrite-heldout-worker.v1', 'name': args.phase, 'passed': result['passed'], 'input_sha256': native['sha256'], 'record': common.descriptor(output / 'Native' / args.phase / 'Record.json')}


def run(args):
    root, method, bound_data, output = common.binding(args.binding, args.binding_sha256)
    common.verify_source(root, method)
    context = common.custody(bound_data['legacy_job'], root, method)
    legacy, code, prior_job, bound, locked, predictions, canonical = context
    report = {'schema': 'kit.sw2026.blank-preserved-rewrite-heldout-private-result.v1', 'passed': False, 'method_sha256': common.fingerprint(root / 'Method.json'), 'writer_manifest_sha256': method['writer_manifest_sha256'], 'binding_sha256': args.binding_sha256, 'phases': [], 'statuses': []}
    generation_ref = None
    if 'predecessor' in bound_data:
        report['new_sdk_builds'] = 0
        report['predecessor_private_result_sha256'] = method['predecessor']['private_result_sha256']

    def perform(name, prior=None):
        path = output / 'Workers' / (name.replace('/', '_') + '.json')
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'worker', '--method-sha256', args.method_sha256, '--binding', args.binding, '--binding-sha256', args.binding_sha256, '--generation-sha256', generation_ref['sha256'], '--phase', name]
        if prior is not None:
            command += ['--prior-sha256', prior['sha256']]
        status = {'name': name, 'passed': False}
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=prior_job['phase_timeout_seconds'], check=False)
            logs = output / 'WorkerLogs'
            logs.mkdir(parents=True, exist_ok=True)
            (logs / (name.replace('/', '_') + '.stdout')).write_text(completed.stdout)
            (logs / (name.replace('/', '_') + '.stderr')).write_text(completed.stderr)
            status['exit_code'] = completed.returncode
            if path.is_file():
                reference = common.descriptor(path)
                value = common.load(reference)
                status['worker'] = reference
                status['passed'] = completed.returncode == 0 and value['passed'] is True and value['name'] == name
                if 'record' in value:
                    report['phases'].append({key: value[key] for key in ('name', 'input_sha256', 'record')})
        except subprocess.TimeoutExpired:
            status['error_type'] = 'TimeoutExpired'
        report['statuses'].append(status)
        common.write_new(output / 'Progress' / f'{len(report["statuses"]):02}.json', status)
        return status

    def lifecycle(base):
        first = perform(base + '/OpenEditSave')
        return bool(first['passed'] and perform(base + '/FreshReopen', first['worker'])['passed'])

    try:
        if 'predecessor' in bound_data:
            generation_ref = retry.adopt(args, root, method, bound_data, output, context)
            report['sdk_builds_reused'] = True
            report['new_sdk_builds'] = 0
            report['predecessor_private_result_sha256'] = method['predecessor']['private_result_sha256']
        else:
            generation_ref = generation({'sha256': args.binding_sha256}, method, output, context, root)
        report['generation'] = generation_ref
        report['paired_builds_identical'] = True
        report['sdk_runtime_input_reads'] = 0
        if lifecycle('ControlBefore'):
            for base in common.BASES[1:-1]:
                if not lifecycle(base):
                    break
    except Exception as error:
        report['error_type'] = type(error).__name__
        report['guest_only_error'] = traceback.format_exc()
    finally:
        if generation_ref is not None:
            try:
                report['trailing_control_passed'] = lifecycle('ControlAfter')
            except Exception as error:
                report['trailing_control_error_type'] = type(error).__name__
        report['controls_passed'] = [
            all(any(row['name'] == base + '/' + stage and row['passed'] for row in report['statuses']) for stage in common.STAGES)
            for base in ('ControlBefore', 'ControlAfter')
        ]
        observed_births = set()
        for row in report['phases']:
            recorded = common.load(row['record']).get('result', {})
            birth = recorded.get('oracle_identity', {}).get('process_creation_filetime')
            if type(birth) is int:
                observed_births.add(birth)
        report['native_processes'] = len(observed_births)
        try:
            legacy.generation_gate(code, prior_job, bound, locked, True)
            frozen = common.load(generation_ref)
            for value in frozen['rewritten'].values():
                common.require(common.fingerprint(value['path']) == value['sha256'], 'generated input changed')
            common.require(common.fingerprint(prior_job['control']['path']) == code.CONTROL, 'control changed')
            report['inputs_immutable'] = True
            births, intervals = set(), []
            rows = report['phases']
            common.require([row['name'] for row in rows] == [base + '/' + stage for base in common.BASES for stage in common.STAGES], 'complete native sequence required')
            for index, base in enumerate(common.BASES):
                slot = base.split('/')[0]
                wanted = predictions[slot] if slot in common.SLOTS else legacy.expected_for(code, base, predictions)
                initial = canonical[slot]['sha256'] if slot in common.SLOTS and base.endswith('/Source') else frozen['rewritten'][slot]['sha256'] if slot in common.SLOTS else code.CONTROL
                first, second = rows[index * 2:index * 2 + 2]
                common.require(first['input_sha256'] == initial, 'native input association differs')
                saved = code.phase(first, wanted['initial'], wanted['tree'], wanted['edited'], births, intervals)
                common.require(second['input_sha256'] == saved['derivative_sha256'], 'fresh reopen derivative differs')
                code.phase(second, wanted['edited'], wanted['tree'], None, births, intervals)
            report.update(native_processes=len(births), controls_passed=[True, True], sheet_states=30, ordered_tree_rows=120)
            report['passed'] = len(births) == 12 and len(report['statuses']) == 12 and all(row['passed'] for row in report['statuses']) and 'error_type' not in report and 'trailing_control_error_type' not in report
        except Exception as error:
            report['comparison_error_type'] = type(error).__name__
            report['comparison_guest_only_error'] = traceback.format_exc()
        try:
            common.verify_source(root, method)
        except Exception as error:
            report['passed'] = False
            report['final_source_error_type'] = type(error).__name__
        raw = common.write_new(output / 'PrivateResult.json', report)
        public = common.export_report(report, raw['sha256'])
        common.write_new(output / 'PublicExport.json', public)
    return public


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('verify-source', 'verify-observer', 'prepare', 'prepare-retry', 'run', 'worker'))
    parser.add_argument('--method-sha256', required=True)
    parser.add_argument('--legacy-job')
    parser.add_argument('--legacy-job-sha256')
    parser.add_argument('--output-root')
    parser.add_argument('--binding')
    parser.add_argument('--binding-sha256')
    parser.add_argument('--generation-sha256')
    parser.add_argument('--phase')
    parser.add_argument('--prior-sha256')
    args = parser.parse_args()
    try:
        common.require(re.fullmatch('[0-9a-f]{64}', args.method_sha256) is not None and common.fingerprint(Path(__file__).resolve().parents[1] / 'Method.json') == args.method_sha256, 'external method freeze differs')
        if args.mode == 'verify-source':
            root, method = common.packet()
            common.verify_source(root, method)
            value = {'passed': True, 'writer_manifest_sha256': method['writer_manifest_sha256'], 'native_launches': 0, 'private_payload_reads': 0}
        elif args.mode == 'verify-observer':
            common.require(os.name == 'nt', 'observer import verification is guest only')
            common.packet()
            for name in ('Swapp', 'InspectDrawingCache', 'OracleIdentity'):
                importlib.import_module(name)
            value = {'passed': True, 'native_launches': 0, 'private_payload_reads': 0}
        elif args.mode == 'prepare':
            _, method = common.packet()
            common.require('predecessor' not in method, 'retry requires prepare-retry')
            value = prepare(args)
        elif args.mode == 'prepare-retry':
            value = retry.prepare(args)
        elif args.mode == 'worker':
            value = worker(args)
            _, _, _, output = common.binding(args.binding, args.binding_sha256)
            common.write_new(output / 'Workers' / (args.phase.replace('/', '_') + '.json'), value)
            value = {'passed': value['passed']}
        else:
            value = run(args)
        print(json.dumps(value, allow_nan=False))
        return 0 if value['passed'] else 3
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'private_values_exported': False}))
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
