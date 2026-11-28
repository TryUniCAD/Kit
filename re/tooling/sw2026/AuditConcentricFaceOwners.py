from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, expected):
    require(not path.is_symlink(), 'disclosed source cannot be a symlink')
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, 'declared source digest changed')
    return raw


def graph_node(graph, reference, name):
    require(isinstance(reference, dict) and reference.get('class') == name,
            'concentric identity has a different concrete owner')
    node = graph[str(reference['index'])]
    require(node['class'] == name, 'concentric reference class does not resolve')
    return node['fields']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--mate-graph', type=Path, required=True)
    parser.add_argument('--mate-graph-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutation', choices=('marker', 'feature', 'creation', 'atom', 'text'))
    args = parser.parse_args()
    require(not args.output.exists(), 'choose an unused audit receipt')
    packet = args.packet.resolve(strict=True)
    require(packet.name == 'ConcentricMateSourcePacket02', 'only the declared disclosed source packet is admitted')
    source = json.loads(checked(args.mate_graph, args.mate_graph_sha256))
    require(set(source) == {'D01', 'D02', 'D03'}, 'source graph contains undeclared cases')
    sys.path.insert(0, str(args.root.resolve(strict=True) / 'src'))
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    def node(value, name):
        require(isinstance(value, ArchiveNode) and value.ClassValue.NameValue == name,
                'actual child native owner has another concrete class')
        return value

    def one(values, name):
        matches = tuple(value for value in values if value.ClassValue.NameValue == name)
        require(len(matches) == 1, 'actual child feature owner is absent or ambiguous')
        return matches[0]

    rows = []
    for case in ('D01', 'D02', 'D03'):
        case_root = packet / 'Disclosed' / case
        lockraw = (case_root / 'lock.json').read_bytes()
        lock = json.loads(lockraw)
        require(lock['source_locked'] is True and lock['heldout_source_locked'] is False,
                'native source is not the admitted disclosed lock')
        for phase in ('source', 'edited'):
            childpath = case_root / 'Native' / phase.title() / ('Concentric' + case + 'Child.SLDPRT')
            require(childpath.resolve(strict=True).is_relative_to(case_root), 'child escaped the disclosed subtree')
            expected = lock['native_artifacts'][phase]['child']
            raw = checked(childpath, expected['sha256'])
            require(len(raw) == expected['bytes'], 'disclosed child size changed')
            link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
            boss = one(link.ResolvedValue.RootsValue, 'moExtrusion_c')
            parents = boss.FieldsValue['f60']['list']['items']
            require(len(parents) == 1, 'disclosed extrusion has an ambiguous profile parent')
            profile = node(parents[0]['o'], 'moProfileFeature_c')
            require(any(profile is candidate for candidate in link.ResolvedValue.RootsValue),
                    'disclosed profile is not the actual model root')
            sketch = node(profile.FieldsValue['pd_f80'], 'sgSketch')
            arcs = sketch.FieldsValue['arcs']
            require(len(arcs) == 1 and arcs[0]['flags'] == 0,
                    'disclosed profile is not one ordinary live circle')
            arc = arcs[0]['arc']
            marker, creation_id = arc['f08'], arc['f0c']
            require(type(marker) is int and marker > 0 and type(creation_id) is int,
                    'disclosed circle does not have an actual positive permanent marker')
            atoms = boss.FieldsValue['f528']['items']
            require(len(atoms) == 1, 'disclosed extrusion has an ambiguous actual atom')
            atom = node(atoms[0]['o'], 'moAtom_c')
            body_id = atom.FieldsValue['f140']
            feature_id = boss.FieldsValue['f08']
            feature_time = DatumTime(link.ConfigValue.HeaderValue, feature_id)
            model_file = link.ConfigValue.HeaderValue.FieldsValue['f38'].FieldsValue
            copied = deepcopy(source[case][phase])
            require(copied['archive_sha256'] == lock['native_artifacts'][phase]['parent']['sha256'],
                    'parent graph does not bind the exact disclosed source archive')
            graph = copied['graph']
            mate = graph_node(graph, copied['root'], 'moMateConcentric')
            require(len(mate['f410']) == 2 and len(mate['f3c8']) == 2,
                    'disclosed concentric graph is not an ordinary ordered pair')
            for ordinal, (active_row, snapshot_row) in enumerate(zip(mate['f410'], mate['f3c8'], strict=True)):
                active = graph_node(graph, active_row['o'], 'moCylinderRef_w')
                face = graph_node(graph, active['f58'], 'moCompFace_c')
                face_ref = graph_node(graph, face['fe8'], 'moFaceRef_c')
                surfaces = [item['f08'] for item in face_ref['f10'] if item['f08'] is not None]
                base = graph_node(graph, surfaces[0], 'moFromSktEntSurfIdRep_c')
                feature = graph_node(graph, base['f10']['f10'], 'moFR_c')
                snapshot = graph_node(graph, snapshot_row['o'], 'moCylinderRef_w')
                component = graph_node(graph, snapshot['f58'], 'moCompRefCylinder_c')
                facet = graph_node(graph, component['fb0'], 'moFacetedData_c')
                if args.mutation and case == 'D01' and phase == 'source' and ordinal == 0:
                    if args.mutation == 'marker': base['f38'] += 1
                    elif args.mutation == 'feature': feature['f10']['f00'] = profile.FieldsValue['f08']
                    elif args.mutation == 'creation': feature['f10']['f08'] = DatumTime(link.ConfigValue.HeaderValue, profile.FieldsValue['f08'])
                    elif args.mutation == 'atom': facet['f50'] += 1
                    else: facet['f58'] = facet['f58'].rstrip()
                require(base['f38'] == marker, 'surface entity id differs from the actual generating arc permanent marker')
                require(feature['f10']['f00'] == feature_id, 'surface reference does not select the actual extrusion owner')
                require(feature['f10']['f08'] == feature_time, 'surface reference does not select the actual first extrusion creation event')
                external = graph_node(graph, feature['f08'], 'moExtObject_c')
                require(external['shared']['f20'] == model_file['shared']['f20']
                        and external['shared']['f28'] == model_file['shared']['f28'],
                        'surface reference does not retain the actual child file origin')
                require(facet['f50'] == body_id, 'faceted body id differs from the actual generated body atom owner')
                text = 'moFromSktEntSurfIdRep_c,' + str(feature_id) + ',' + str(marker) + ', \n'
                require(facet['f58'] == text and facet['f58_empty'] == 0,
                        'faceted face text differs from the source-mapped ordinary surface format')
                require(facet['has_points'] == 0, 'populated faceted points are outside this identity-only audit')
                for representation in surfaces[1:]:
                    end = graph_node(graph, representation, 'moEndFaceSurfIdRep_c')
                    end_feature = graph_node(graph, end['f10']['f10'], 'moFR_c')
                    require(end_feature['f10'] == feature['f10'], 'end face identity selects a different feature epoch')
                rows.append({
                    'case': case, 'phase': phase, 'endpoint': ordinal,
                    'child_sha256': expected['sha256'], 'parent_sha256': copied['archive_sha256'],
                    'lock_sha256': sha256(lockraw).hexdigest(),
                    'actual_profile_id': profile.FieldsValue['f08'], 'actual_extrusion_id': feature_id,
                    'actual_extrusion_creation': feature_time,
                    'actual_arc_permanent_marker_f08': marker, 'separate_arc_creation_id_f0c': creation_id,
                    'actual_atom_id_f140': body_id,
                    'facet_face_node_id_f40_observed_only': facet['f40'],
                    'facet_body_id_f50_matches_atom': True, 'facet_text_computed_from_owners': True,
                    'active_face_matches_actual_owners': True,
                    'kernel_face_node_identity_generated': False,
                })
    require(len(rows) == 12, 'disclosed endpoint inventory changed')
    result = {
        'schema': 'kit.sw2026.concentric-face-owner-correlation.v1', 'passed': True,
        'mate_graph_sha256': args.mate_graph_sha256, 'rows': rows,
        'disclosed_parent_states': 6, 'independent_child_reads': 6, 'correlated_endpoints': 12,
        'native_processes_started': 0, 'hidden_inputs_read': 0, 'writer_outputs': 0,
        'kernel_face_node_identity_generated': False,
        'native_constructor_upstream_edge_attribute_binding_complete': False,
        'tool_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'passed': True, 'sha256': sha256(args.output.read_bytes()).hexdigest(),
                      'child_reads': 6, 'endpoints': len(rows)}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError) as error:
        print(json.dumps({'passed': False, 'error': str(error)}, sort_keys=True))
        raise SystemExit(3)
