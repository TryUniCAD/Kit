from codecs import lookup
from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT / 'src'), str(ROOT), str(ROOT / 're/tooling/sw2026')]
from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly as compile_assembly
from MakeAssemblyBoundaryCase import make_case
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.Records.RecordParameter import Expression
from interchange.geometry.Models.VectorSpace import SpaceVector

DOCUMENT = make_case(3)
GRAPH = DOCUMENT.assembly
CODECS = tuple(lookup(name) for name in ('utf-8', 'utf-8-sig', 'utf-16-le', 'latin-1'))


def altered_graph(**changes):
    return replace(DOCUMENT, assembly=replace(GRAPH, **changes))


def altered_instance(**changes):
    return altered_graph(instances=(replace(GRAPH.instances[0], **changes), *GRAPH.instances[1:]))


def altered_child(document):
    return altered_graph(documents=(replace(GRAPH.documents[0], document=document),))


def faults():
    child = GRAPH.documents[0].document
    scale = list(GRAPH.instances[0].transform.values)
    scale[0] *= 1.1
    mismatch = replace(GRAPH.mates[-1].value, value=43.)
    shifted = replace(child.support_planes[0], transform=replace(child.support_planes[0].transform, origin=SpaceVector(0., 1., 0.)))
    cases = {
        'missing_owned_child': altered_graph(documents=()),
        'external_source_reference': altered_graph(definitions=(GRAPH.definitions[0], replace(GRAPH.definitions[1], source_path='C:\\unread-source.SLDPRT'))),
        'nested_definition_kind': altered_graph(definitions=(GRAPH.definitions[0], replace(GRAPH.definitions[1], kind='assembly'))),
        'suppressed_occurrence': altered_instance(suppressed=True),
        'hidden_occurrence': altered_instance(hidden=True),
        'flexible_occurrence': altered_instance(flexible=True),
        'ambiguous_order': altered_instance(order=1),
        'wrong_configuration': altered_instance(configuration_name='different'),
        'scaled_placement': altered_instance(transform=TransformMatrix(tuple(scale))),
        'non_boolean_fixed': altered_instance(fixed=1),
        'no_anchor': altered_instance(fixed=False),
        'multiple_anchors': altered_graph(instances=(GRAPH.instances[0], replace(GRAPH.instances[1], fixed=True), GRAPH.instances[2])),
        'missing_datum_owner': altered_graph(mate_entities=(replace(GRAPH.mate_entities[0], source_entity_id='missing'), *GRAPH.mate_entities[1:])),
        'unsupported_entity_frame': altered_graph(mate_entities=(replace(GRAPH.mate_entities[0], frame=TransformMatrix()), *GRAPH.mate_entities[1:])),
        'unaligned_mate': altered_graph(mates=(replace(GRAPH.mates[0], alignment='anti_aligned'), *GRAPH.mates[1:])),
        'distance_parameter_disagreement': altered_graph(mates=(*GRAPH.mates[:-1], replace(GRAPH.mates[-1], value=mismatch))),
        'expressed_distance': replace(DOCUMENT, parameters=(replace(DOCUMENT.parameters[0], expression=Expression('42')),)),
        'unconsumed_entity': altered_graph(mate_entities=(*GRAPH.mate_entities, replace(GRAPH.mate_entities[0], id='extra'))),
        'unqualified_group_member': altered_graph(mate_groups=(replace(GRAPH.mate_groups[0], mate_ids=GRAPH.mate_groups[0].mate_ids[:-1]),)),
        'translated_child_datum': altered_child(replace(child, support_planes=(shifted, *child.support_planes[1:]))),
        'unprojected_child_property': altered_child(replace(child, metadata={**child.metadata, 'custom_properties': {'Unqualified': 'text'}})),
        'unprojected_assembly_metadata': replace(DOCUMENT, metadata={**DOCUMENT.metadata, 'extra': 'unprojected'}),
    }
    native = 'C:\\KitAssemblyBoundary\\' + DOCUMENT.metadata['name'] + '.SLDASM'
    return [(name, document, native) for name, document in cases.items()] + [
        ('relative_native_path', DOCUMENT, DOCUMENT.metadata['name'] + '.SLDASM'),
        ('native_device_directory', DOCUMENT, 'C:\\CON\\' + DOCUMENT.metadata['name'] + '.SLDASM'),
    ]


CASES = faults()
AUDIT = BuildAudit(ROOT / 're/tooling/sw2026/serial/defs')
sys.addaudithook(AUDIT.InspectEvent)
AUDIT.BeginBuild()
ROWS = []
for name, document, path in CASES:
    try:
        compile_assembly(document, path, 1794001000)
    except (ValueError, TypeError, KeyError) as error:
        ROWS.append({'case': name, 'rejected': True, 'exception': type(error).__name__, 'message': str(error)})
    else:
        raise ValueError('unqualified public assembly graph was accepted: ' + name)
print(json.dumps({'passed': True, 'negative_cases': len(ROWS), 'rows': ROWS, 'runtime_input_file_reads': len(AUDIT.DeniedReads),
                  'native_processes_started': 0, 'writer_output_count': 0, 'native_acceptance': False}, sort_keys=True))
