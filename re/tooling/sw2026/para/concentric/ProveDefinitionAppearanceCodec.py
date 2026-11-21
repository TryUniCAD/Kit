from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(REPO / 'src')]

from AuditStockChildAppearance import PART, RESULT, ROOT, ROUGHNESS, TRIAL, definition_evidence, verified
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.ObListFields import KObListFields
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyAppr import ReadEmptyAppr
from convert.adapters.solidworks.Archive.Definition.ModelDefContext import ModelDefContext
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import SldprtArchive


CLASS = 'PWMaterialProperties_c'
LAYOUTS = REPO / 'src/convert/adapters/solidworks/Archive/Definition/Fields'
FILES = ['AppearanceFields.py', 'DocHelperFields.py', 'ModelDefLayouts.py', 'ModelDefSchemas.py']


def require(value, message):
    if not value:
        raise ValueError(message)


def graph_values(value):
    return value.DocumentValue.FieldsValue


def material_row(graph):
    return graph_values(graph)['f1110']['list']['items'][0]


def read(path, pin):
    archive = SldprtArchive.from_bytes(verified(path, pin))
    raw = archive.require('Contents/Definition')
    parsed = ReadModelDef(raw, 19000)
    written = WriteModelDef(parsed.GraphValue)
    require(written.OutputValue == raw and written.MapValue == parsed.MapValue
            and parsed.UsageValue.IsComplete and written.UsageValue.IsComplete
            and not parsed.UsageValue.ByteFields and not written.UsageValue.ByteFields, 'inexact Definition replay')
    return archive, parsed.GraphValue, {'archive_sha256': pin, 'bytes': len(raw), 'typed_replay': True,
                                        'terminal_map': parsed.MapValue.CounterValue}


def refuses(message, operation, *args):
    try:
        operation(*args)
    except BodyUnsupported as error:
        require(message in str(error), f'wrong refusal: {error!s}')
        return str(error)
    raise ValueError('unexpected acceptance: ' + message)


def probe_context(version):
    context = ModelDefContext(version)
    layouts = dict(context.LayoutsValue)
    layouts[CLASS] = tuple(rule for rule in layouts[CLASS] if rule.KindValue != 'Branch')
    layouts['PWMaterialManager_c.materials'] = KObListFields
    return replace(context, LayoutsValue=layouts, SchemasValue=dict(context.SchemasValue) | {CLASS: (1, 2)})


def negative_proof(source, assembly):
    module = import_module('convert.adapters.solidworks.Archive.Definition.WriteModelDef')
    probes = {}
    for version in (0, 2):
        graph = deepcopy(source)
        material_row(graph)['o'].FieldsValue['f20'] = version
        probes[f'internal_version_{version}'] = (graph, 'unsupported Definition appearance version')

    graph = deepcopy(source)
    material_row(graph)['o'].ClassValue = RuntimeClass(CLASS, 2)
    probes['tag_schema_2'] = (graph, 'unsupported SOLIDWORKS body class PWMaterialProperties_c schema 2')

    for kind, node in [('null', None), ('wrong_class', ArchiveNode(RuntimeClass('moANSI_c', 1), {}))]:
        graph = deepcopy(source)
        material_row(graph)['o'] = node
        probes[kind] = (graph, 'invalid Definition appearance reference')

    graph = deepcopy(source)
    graph_values(graph)['has_pwmaterial'] = 2
    probes['unmeasured_presence_flag'] = (graph, 'appearance body outside part Definition manager')

    graph = deepcopy(source)
    graph_values(graph)['fac0'] = deepcopy(material_row(graph)['o'])
    probes['new_body_in_untyped_owner'] = (graph, 'appearance body outside part Definition manager')

    graph = deepcopy(assembly)
    graph_values(graph)['f1110'] = deepcopy(graph_values(source)['f1110'])
    probes['assembly_manager'] = (graph, 'appearance body outside part Definition manager')

    failures = {}
    for name, (graph, diagnostic) in probes.items():
        stored = refuses(diagnostic, WriteModelDef, graph)
        with patch.object(module, 'ModelDefContext', probe_context):
            invalid = WriteModelDef(graph).OutputValue
        failures[name] = {'read': refuses(diagnostic, ReadModelDef, invalid, 19000), 'write': stored}
    return failures


def snapshot():
    return {str((LAYOUTS / name).relative_to(REPO)): sha256((LAYOUTS / name).read_bytes()).hexdigest() for name in FILES}


def main():
    source = snapshot()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip()
    job = json.loads(verified(ROOT / 'Trial.json', TRIAL))
    result = json.loads(verified(ROOT / 'Result.json', RESULT))
    require(result['trial_sha256'] == TRIAL and result['passed'] is True and result['controls_healthy'] is True
            and result['native_processes'] == 6 and result['heldout_credit'] == 0, 'unexpected source trial')
    positives = {}
    cases = {}
    for lane, roughness in ROUGHNESS.items():
        phase = result['phases']['Author' + lane]
        target = result['phases']['Reopen' + lane]['appearance']
        native = ROOT / 'Inspection' / ('Author' + lane) / PART
        archive, cases[lane], positives[lane] = read(native, phase['saved_sha256'])
        measurement, _ = definition_evidence(archive, ReadModelDef, WriteModelDef, target['ids'], roughness, lambda values: values)
        positives[lane].update(measurement)

    controls = {'generated_absent': (ROOT / 'Frozen' / PART, job['baseline_sha256'])}
    for role, row in job['controls'].items():
        controls['original_' + role] = (Path(row['host_path']), row['sha256'])
    empty = {}
    for name, (path, pin) in controls.items():
        _, cases[name], empty[name] = read(path, pin)
        manager = graph_values(cases[name]).get('f1110')
        require(manager is None or manager['list']['n'] == 0, 'unpopulated control drifted')

    graph = cases['A']
    refusals = negative_proof(graph, cases['original_parent'])
    refusals['semantic_projection'] = refuses('requires exactly empty reference rows', ReadEmptyAppr, graph_values(graph))
    raw = WriteModelDef(graph).OutputValue
    for version in (18999, 19001):
        refusals[f'archive_version_{version}'] = {
            'read': refuses('requires archive version 19000', ReadModelDef, raw, version),
            'write': refuses('requires archive version 19000', WriteModelDef, replace(graph, VersionValue=version)),
        }

    alias = deepcopy(graph)
    graph_values(alias)['f12e8'] = material_row(alias)['o']
    parsed = ReadModelDef(WriteModelDef(alias).OutputValue, 19000).GraphValue
    require(graph_values(parsed)['f12e8'] is material_row(parsed)['o'], 'shared reference boundary changed')
    require(snapshot() == source, 'source changed while proving the codec')
    print(json.dumps({'revision': revision, 'branch': branch, 'layout_source_sha256': source, 'trial_sha256': TRIAL,
                      'native_result_sha256': RESULT, 'populated_definitions': positives, 'empty_definitions': empty,
                      'refusals': refusals, 'untyped_later_backreference': 'f12e8 retains the earlier material vertex',
                      'heldout_credit': 0, 'generative_appearance_admission': False}, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
