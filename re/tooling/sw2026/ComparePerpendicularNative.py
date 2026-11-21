from hashlib import sha256
import json
from math import isclose
import os
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def near(first, second, absolute=1e-12):
    return len(first) == len(second) and all(isclose(a, b, rel_tol=2e-7, abs_tol=absolute)
                                              for a, b in zip(first, second, strict=True))


def tree(value):
    require(all(item['error'] == 0 and item['warning'] is False and item['suppressed'] is False for item in value),
            'a paired native tree has an error warning or suppressed feature')
    return [[item[key] for key in ('name', 'type', 'parent')] for item in value]


def own_endpoints(value):
    rows = value['occurrences']
    require(len(rows) == 2 and len({row['native_id'] for row in rows}) == 2, 'native occurrence identities are not unique')
    by_name = {row['name']: row for row in rows}
    require(len(by_name) == 2 and sum(row['fixed'] is True for row in rows) == 1, 'native occurrence ownership or fixed anchor is ambiguous')
    mate = value['mate']
    require(mate['type'] == 2 and mate['alignment_observed'] == 2 and len(mate['ordered_endpoints']) == 2,
            'the ordinary native perpendicular mate state differs')
    require(abs(mate['normal_dot']) <= 1e-10, 'the measured native perpendicular residual is too large')
    result = []
    for endpoint in mate['ordered_endpoints']:
        owner = by_name[endpoint['occurrence']]
        require(endpoint['occurrence_native_id'] == owner['native_id'] and endpoint['reference_type'] == 4
                and endpoint['plane_native_id'] >= 0, 'the native endpoint does not belong to its declared actual occurrence datum')
        require(all(endpoint['object_comparison'][key] == 1 for key in ('repeated_reference', 'repeated_specific')),
                'the native repeated-object control is not stable')
        result.append({key: endpoint[key] for key in ('occurrence', 'plane', 'reference_type')})
    return result


def compare(case, first, second, prediction, edited):
    require(not case['id'].startswith('H') or os.name == 'nt', 'sealed native comparison is guest-only')
    expected = prediction['edited' if edited else 'source']
    require(first['body_count'] == second['body_count'] == 2, 'the paired native body counts differ')
    require(tree(first['tree']) == tree(second['tree']) and tree(first['child_tree']) == tree(second['child_tree']),
            'the complete ordered source and generated native trees differ')
    require(first['mate']['name'] == second['mate']['name'] == case['mate']['name']
            and own_endpoints(first) == own_endpoints(second), 'the paired ordered native mate semantics differ')
    for left, right, desired in zip(first['occurrences'], second['occurrences'], expected['native_transforms'], strict=True):
        require(all(left[key] == right[key] for key in ('name', 'configuration', 'fixed', 'visible_child_bodies'))
                and left['configuration'] == case['configuration'] and left['visible_child_bodies'] == 1
                and near(left['transform'], right['transform']) and near(left['transform'], desired),
                'the paired native occurrence name configuration anchor body or transform differs')
    wanted_names = [case['child_name'] + '-' + str(index) for index in (1, 2)]
    require([row['name'] for row in first['occurrences']] == wanted_names and
            [row['fixed'] for row in first['occurrences']] == [index == case['fixed_occurrence'] for index in range(2)],
            'the paired native occurrences differ from authored identity and fixed input')
    for left, right, target in zip(first['mate']['ordered_endpoints'], second['mate']['ordered_endpoints'], expected['ordered_endpoints'], strict=True):
        require(left['occurrence'] == wanted_names[target['occurrence']] and
                left['plane'] == {'x': 'Right Plane', 'y': 'Top Plane', 'z': 'Front Plane'}[target['axis']]
                and near(left['normal'], right['normal']) and near(left['normal'], target['normal'])
                and near(left['point'], right['point']) and near(left['point'], target['point_m']),
                'the paired endpoint does not preserve the authored actual datum point or normal')
    drivers = ('D1@Sketch1', 'D2@Sketch1', 'D1@Boss-Extrude1')
    require(set(first['dimensions_m']) == set(second['dimensions_m']) == set(drivers) and
            near([first['dimensions_m'][key] for key in drivers], expected['child_driver_values_m']) and
            near([first['dimensions_m'][key] for key in drivers], [second['dimensions_m'][key] for key in drivers]),
            'the paired three actual native driving dimensions differ')
    densities = {}
    for role in ('child', 'assembly'):
        left, right, target = first['mass'][role], second['mass'][role], expected[role]
        require(near([left['volume'], left['area']], [right['volume'], right['area']], 1e-15) and
                near([left['volume'], left['area']], [target['volume_m3'], target['area_m2']], 1e-15) and
                near(left['com'], right['com']) and near(left['com'], target['com_m'])
                and isclose(left['mass'], right['mass'], rel_tol=2e-7, abs_tol=1e-15) and left['mass'] > 0 and right['mass'] > 0,
                'the paired native mass or independently predicted geometry differs')
        densities[role] = {'source': left['mass'] / left['volume'], 'generated': right['mass'] / right['volume']}
    return {'passed': True, 'ordered_full_trees_equal': True, 'exact_semantic_owner_names_equal': True,
            'ordered_mate_endpoints_equal': True, 'actual_native_owner_ids_compared_within_each_file': True,
            'child_drivers_equal': 3, 'independent_poses_and_geometry_equal': True, 'measured_paired_mass_equal': True,
            'recorded_effective_densities': densities, 'active_angular_correction_proven': False,
            'public_writer_qualified': False, 'new_writer_output_count': 0, 'native_processes_started': 0}


def main():
    incoming = sys.stdin.buffer.read()
    value = json.loads(incoming)
    require(set(value) == {'case', 'source', 'generated', 'prediction', 'edited'} and type(value['edited']) is bool,
            'the paired comparator requires its exact declared separate prediction and observations')
    result = compare(value['case'], value['source'], value['generated'], value['prediction'], value['edited'])
    result['comparison_input_sha256'] = sha256(incoming).hexdigest()
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
