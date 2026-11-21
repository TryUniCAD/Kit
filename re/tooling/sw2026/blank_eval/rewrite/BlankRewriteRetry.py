from __future__ import annotations

import os
from pathlib import Path
import sys

import BlankRewriteHeldoutCommon as common


def previous(root, method):
    common.require(os.name == 'nt', 'private predecessor remains guest only')
    pins = method['predecessor']
    directory = common.guest_path(pins['output_root'])
    binding = common.load({'path': str(directory / 'Binding.json'), 'sha256': pins['binding_sha256']})
    common.require(binding['method_sha256'] == pins['method_sha256'] and binding['tools_sha256'] == pins['tools_sha256'] and binding['writer_manifest_sha256'] == method['writer_manifest_sha256'], 'predecessor writer or method differs')
    exported = common.load({'path': str(directory / 'PublicExport.json'), 'sha256': pins['public_export_sha256']})
    common.require(exported['passed'] is False and exported['raw_result_sha256'] == pins['private_result_sha256'] and exported['native_processes'] == 0 and exported['paired_builds_identical'] and exported['sdk_runtime_input_reads'] == 0 and exported['inputs_immutable'], 'predecessor setup failure differs')
    raw = common.load({'path': str(directory / 'PrivateResult.json'), 'sha256': pins['private_result_sha256']})
    common.require(raw['passed'] is False and raw['binding_sha256'] == pins['binding_sha256'] and raw['method_sha256'] == pins['method_sha256'] and raw['writer_manifest_sha256'] == method['writer_manifest_sha256'] and raw['phases'] == [], 'predecessor native absence differs')
    common.require([row['name'] for row in raw['statuses']] == ['ControlBefore/OpenEditSave', 'ControlAfter/OpenEditSave'] and all(row['passed'] is False and row['exit_code'] == 3 for row in raw['statuses']), 'predecessor failed controls differ')
    frozen = common.load(raw['generation'])
    common.require(frozen['binding_sha256'] == pins['binding_sha256'] and frozen['writer_manifest_sha256'] == method['writer_manifest_sha256'] and frozen['all_outputs_frozen_before_native'], 'predecessor generation differs')
    return binding, raw['generation'], frozen


def prepare(args):
    common.require(os.name == 'nt', 'observer retry preparation is guest only')
    root, method = common.packet()
    common.verify_source(root, method)
    binding, generation, frozen = previous(root, method)
    common.custody(binding['legacy_job'], root, method)
    output = common.guest_path(args.output_root)
    common.require(not output.exists() and not output.is_relative_to(common.guest_path(method['predecessor']['output_root'])) and not output.is_relative_to(Path('C:/KitBlankDrawingSource121')), 'use a separate unused retry output')
    output.mkdir(parents=True, exist_ok=False)
    value = {
        'schema': 'kit.sw2026.blank-preserved-rewrite-heldout-binding.v1',
        'method_sha256': common.fingerprint(root / 'Method.json'),
        'tools_sha256': method['tools_sha256'],
        'writer_manifest_sha256': method['writer_manifest_sha256'],
        'legacy_job': binding['legacy_job'],
        'output_root': str(output),
        'python': sys.executable,
        'prior_canonical_hashes': method['prior_output_sha256'],
        'predecessor': method['predecessor'],
        'predecessor_generation': generation,
        'reuses_exact_first_run_candidates': True,
        'new_sdk_builds': 0,
        'native_original_payload_reads': 0,
    }
    result = common.write_new(output / 'Binding.json', value)
    return {'schema': 'kit.sw2026.blank-rewrite-retry-prepare-export.v1', 'passed': True, 'binding_sha256': result['sha256'], 'method_sha256': value['method_sha256'], 'new_sdk_builds': 0, 'private_values_exported': False}


def adopt(args, root, method, binding, output, context):
    legacy, code, prior_job, bound, locked, predictions, canonical = context
    prior_binding, reference, frozen = previous(root, method)
    common.require(reference == binding['predecessor_generation'] and prior_binding['legacy_job'] == binding['legacy_job'], 'retry predecessor association differs')
    legacy.generation_gate(code, prior_job, bound, locked, True)
    common.require(frozen['canonical_sources'] == canonical and list(frozen['rewritten']) == list(common.SLOTS), 'canonical predecessor differs')
    common.require([row['slot'] for row in frozen['builds']] == list(common.SLOTS), 'both original build pairs required')
    for row in frozen['builds']:
        slot = row['slot']
        first, second = row['first_output'], row['second_output']
        common.guest_path(first['path'])
        common.guest_path(second['path'])
        common.require(first['sha256'] == second['sha256'] == frozen['rewritten'][slot]['sha256'], 'original paired output hashes differ')
        common.require(common.fingerprint(first['path']) == first['sha256'] and common.fingerprint(second['path']) == second['sha256'] and Path(first['path']).read_bytes() == Path(second['path']).read_bytes(), 'actual original candidate bytes differ')
        common.require(len(row['reports']) == 2 and row['identical'], 'two original build reports required')
        for report_ref in row['reports']:
            common.guest_path(report_ref['path'])
            report = common.load(report_ref)
            common.require(report['passed'] and report['writer_manifest_sha256'] == method['writer_manifest_sha256'] and report['native_flags'] == [False, False], 'original SDK build qualifier differs')
            common.require(report['runtime_input_reads'] == report['native_launches'] == report['original_native_source_files_read'] == 0 and report['private_canonical_source_files_read'] == 1 and report['source_owners_preserved'] and report['unchanged_layout'], 'original writer or ownership evidence differs')
            common.require(report['source']['sha256'] == method['prior_output_sha256'][slot] and Path(report['source']['path']).resolve() == Path(canonical[slot]['path']).resolve(), 'original input identity differs')
            common.require(report['explicit_saved_at'] == method['save_epochs'][slot] and report['target']['sha256'] == second['sha256'] and report['actual_self_path'] == second['path'], 'original destination or save event differs')
            common.require(report['expected_tree'] == predictions[slot]['tree'], 'original tree witness differs')
            code.same_snapshot(report['expected_initial'], predictions[slot]['initial'])
    value = dict(frozen)
    value.update(binding_sha256=args.binding_sha256, predecessor_generation=reference, sdk_builds_reused=True, new_sdk_builds=0, inputs_rehashed_before_retry=True)
    return common.write_new(output / 'Generation.json', value)
