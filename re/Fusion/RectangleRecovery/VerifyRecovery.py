import argparse
from dataclasses import replace
import hashlib
from io import BytesIO
from os import environ
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 're/automation')]

from convert import open_document, write_document
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from FusionRadialMutation import mutation_archive

PACKAGE = Path(__file__).resolve().parent


def verify():
    inventory = json.loads((PACKAGE / 'Controls.json').read_text())
    for entry in inventory['artifacts']:
        raw = (PACKAGE / entry['file']).read_bytes()
        assert len(raw) == entry['size_bytes']
        assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    truth = {'cases': [{**case, 'folder': folder} for folder, name in [('Unconstrained', 'UnconstrainedNative.json'), ('Decimal', 'DecimalNative.json')] for case in json.loads((PACKAGE / name).read_text())['cases']]}
    positives = []
    negatives = []
    drafted = []
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        for case in truth['cases']:
            source = PACKAGE / 'Controls' / case['folder'] / (case['case'] + '.f3d')
            label = ('decimal-' if case['folder'] == 'Decimal' else '') + case['case']
            assert hashlib.sha256(source.read_bytes()).hexdigest() == case['sha256']
            target = work / (label + '.json')
            run = subprocess.run([sys.executable, '-m', 'convert', 'decode', str(source), '-o', str(target)], capture_output=True, timeout=180, env={**environ, 'PYTHONPATH': str(ROOT / 'src')})
            assert run.returncode == 0, run.stderr.decode(errors='replace')
            decoded = json.loads(target.read_text())
            assert decoded['partial'] is False and decoded['layer'] == 'neutral'
            document = open_document(source, source_format='fusion.f3d', strict=True)
            payload = json.loads(document.to_json())
            assert payload == decoded['document']
            bodies = payload['bodies']['$tuple']
            assert len(bodies) == case['body_count'] == 1
            topology = bodies[0]['topology']
            assert math.isclose(topology['volume'], case['volume_cm3'] * 1000, rel_tol=1e-8)
            assert math.isclose(topology['surface_area'], case['area_cm2'] * 100, rel_tol=1e-8)
            bounds = topology['bounding_box']
            center = [(bounds['minimum'][axis] + bounds['maximum'][axis]) / 2 for axis in ('x', 'y', 'z')]
            assert all(math.isclose(a, b * 10, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(center, case['centroid_cm'], strict=True))
            assert len(payload['feature_timeline']['$tuple']) == case['timeline_count'] == 2
            assert all(not sketch['constraints']['$tuple'] and not sketch['parameter_ids']['$tuple'] for sketch in payload['sketches']['$tuple'])
            if case['case'] in ('reverse-xy', 'datum-yz'):
                assert document.metadata['fusion.read_only'] is True
                for label, candidate in [('marked', document), ('stripped', replace(document, metadata={'fusion.native_state': document.metadata['fusion.native_state']}))]:
                    sink = BytesIO()
                    try:
                        write_document(candidate, sink, destination_format='fusion.f3d', allow_carrier=False)
                    except (ValueError, AdapterNotFoundError) as error:
                        assert 'qualified authoring' in str(error) or 'read-only' in str(error) or 'does not support the destination' in str(error)
                    else:
                        raise AssertionError('unqualified reader extension became writable')
                    assert not sink.getvalue()
                    try:
                        EncodeDocument(candidate)
                    except ValueError as error:
                        assert 'qualified authoring' in str(error) or 'read-only' in str(error)
                    else:
                        raise AssertionError('native-state bridge accepted unqualified profile')
                    negatives.append(('decimal-' if case['folder'] == 'Decimal' else '') + case['case'] + '-writer-' + label)
            positives.append({'case': ('decimal-' if case['folder'] == 'Decimal' else '') + case['case'], 'volume_mm3': topology['volume'], 'surface_area_mm2': topology['surface_area'], 'centroid_mm': center, 'strict_sdk_and_cli_equal': True})
        for name in ('forward-xz', 'reverse-xz', 'reverse-yz'):
            source = PACKAGE / 'Controls/Constrained' / (name + '.f3d')
            target = work / (name + '-refused.json')
            run = subprocess.run([sys.executable, '-m', 'convert', 'decode', str(source), '-o', str(target)], capture_output=True, timeout=180, env={**environ, 'PYTHONPATH': str(ROOT / 'src')})
            assert run.returncode != 0 and not target.exists()
            negatives.append(name)
        source = (PACKAGE / 'Controls/Unconstrained/reverse-xy.f3d').read_bytes()
        model = ReadDocument(source)
        graph = BuildGraph(model)
        context = SelectExtrusion(graph)
        parameter = ResolveField(graph, context.Along, 'parameter', 'Parameter')
        settings = graph.OneClass('CommonDataAssetSettings')
        units = ResolveField(graph, settings, 'activeUnitSystem', 'UnitSystem')
        choice, = [n for n in LinkedNodes(graph, units, 'children') if n.ClassName == 'UnitSystemChoiceById' and n.Fields['id'] == 'ModelingLength']
        for name, node, field, value in [('wrong-distance', parameter, 'expression', '-13 mm'), ('unsupported-display-unit', choice, 'unitString', 'inch'), ('named-reverse-distance', parameter, 'expression', parameter.Fields['userName'])]:
            changed = mutation_archive(model, node, field, value)
            path = work / (name + '.f3d')
            path.write_bytes(changed)
            target = work / (name + '.json')
            run = subprocess.run([sys.executable, '-m', 'convert', 'decode', str(path), '-o', str(target)], capture_output=True, timeout=180, env={**environ, 'PYTHONPATH': str(ROOT / 'src')})
            assert run.returncode != 0 and not target.exists()
            expected = {'wrong-distance': 'saved geometry or parameter values disagree', 'unsupported-display-unit': 'require millimeter display units', 'named-reverse-distance': 'unconstrained reverse distance requires a literal'}[name]
            assert expected in run.stderr.decode(errors='replace')
            negatives.append(name)
    for source in sorted((ROOT / 're/Fusion/Reconstruction/NativeEditedPrisms').glob('Draft*.f3d')):
        document = open_document(source, source_format='fusion.f3d', strict=True)
        assert len(document.bodies) == 1 and document.metadata['fusion.read_only'] is True
        drafted.append({'source': str(source.relative_to(ROOT)), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'strict_decoded': True})
    return {'drafted_controls': drafted, 'status': 'passed', 'source_revision': inventory['source_revision'], 'positives': positives, 'negative_cases': negatives, 'full_semantics_verified': False, 'native_conversion_acceptance': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise ValueError('choose an unused output report')
    result = verify()
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
