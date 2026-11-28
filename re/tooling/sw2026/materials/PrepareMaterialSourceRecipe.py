from argparse import ArgumentParser
from hashlib import sha256
from math import isfinite, prod
from pathlib import Path
import json

SCHEMA = 'kit.sw2026.assigned-material-source-plan.v1'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
CONTROL = 'c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57'
CASES = (
    {'id': 'D01Corner', 'anchor': 'corner', 'width_m': 0.017125,
     'height_m': 0.02375, 'depth_m': 0.008625, 'edited_depth_m': 0.011375,
     'first_material_key': 'A', 'second_material_key': 'B'},
    {'id': 'D02Center', 'anchor': 'center', 'width_m': 0.028375,
     'height_m': 0.013625, 'depth_m': 0.01175, 'edited_depth_m': 0.007625,
     'first_material_key': 'B', 'second_material_key': 'A'},
)
METHODS = (
    'SldWorks.GetMaterialDatabases', 'SldWorks.GetMaterialSchemaPathName',
    'PartDoc.SetMaterialPropertyName2', 'PartDoc.GetMaterialPropertyName2',
    'PartDoc.MaterialPropertyValues', 'Body2.GetMaterialPropertyName',
    'Body2.GetMaterialIdName2', 'Body2.GetMaterialUserName2',
    'PartDoc.GetBodies2', 'Body2.GetType', 'Dimension.SetSystemValue3',
)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def hex_digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def geometry(case, depth):
    width, height = case['width_m'], case['height_m']
    volume = prod((width, height, depth))
    return {'volume_m3': volume, 'area_m2': 2 * (width * height + width * depth + height * depth),
            'center_of_mass_m': [width / 2 if case['anchor'] == 'corner' else 0.0,
                                 height / 2 if case['anchor'] == 'corner' else 0.0, depth / 2],
            'solid_body_count': 1}


def validate_catalog(value):
    require(type(value) is dict and value.get('schema') == 'kit.sw2026.assigned-material-catalog.v1', 'catalog schema differs')
    require(value.get('oracle_sha256') == ORACLE and value.get('oracle_revision') == '34.5.2', 'catalog oracle differs')
    require(value.get('read_only_inventory') is True and value.get('heldout_inputs_read') == 0,
            'catalog must be a read-only installed-database inventory without hidden inputs')
    require(value.get('origin') in ('registered-2026-read-only-capture', 'synthetic-host-smoke'),
            'catalog origin must distinguish native capture from host smoke data')
    library = value.get('type_library', {})
    require(type(library) is dict, 'type-library metadata must be an object')
    require(library.get('guid') == '{83A33D31-27C5-11CE-BFD4-00400513BB57}'
            and library.get('major') == 34 and library.get('minor') == 0
            and hex_digest(library.get('wrapper_sha256')), 'exact type-library metadata missing')
    signatures = library.get('method_signatures', {})
    require(type(signatures) is dict, 'method signatures must be an object')
    require(all(type(signatures.get(name)) is str and signatures[name] for name in METHODS),
            'new COM method/property shape must be captured before the source trial')
    database = value.get('database', {})
    require(type(database) is dict, 'database metadata must be an object')
    require(type(database.get('name')) is str and database['name']
            and type(database.get('guest_path')) is str and database['guest_path']
            and hex_digest(database.get('sha256')) and type(database.get('bytes')) is int and database['bytes'] > 0
            and database.get('configured_location') is True
            and hex_digest(database.get('schema_sha256'))
            and type(database.get('schema_guest_path')) is str and database['schema_guest_path'],
            'installed database/schema identity and configured path are required')
    materials = value.get('materials')
    require(type(materials) is list and len(materials) == 2
            and {row.get('key') for row in materials if type(row) is dict} == {'A', 'B'}, 'exactly two material identities are required')
    for row in materials:
        density = row.get('density_kg_m3')
        require(type(row.get('name')) is str and row['name'] and '|' not in row['name'], 'explicit ordinary material name is required')
        require(type(density) in (float, int) and isfinite(density) and density > 0, 'physical SI density must be finite and positive')
        require(type(row.get('density_source_selector')) is str and row['density_source_selector']
                and type(row.get('density_source_unit')) is str and row['density_source_unit']
                and type(row.get('density_si_conversion')) in (float, int)
                and isfinite(row['density_si_conversion']) and row['density_si_conversion'] > 0,
                'independent database density/unit interpretation must be explicit')
    require(materials[0]['name'] != materials[1]['name']
            and abs(materials[0]['density_kg_m3'] - materials[1]['density_kg_m3'])
            > 0.1 * max(materials[0]['density_kg_m3'], materials[1]['density_kg_m3']),
            'materials require distinct names and a discriminating density contrast')
    return {row['key']: row for row in materials}


def plan(catalog, catalog_sha):
    materials = validate_catalog(catalog)
    cases = []
    for authored in CASES:
        first = materials[authored['first_material_key']]
        second = materials[authored['second_material_key']]
        original = geometry(authored, authored['depth_m'])
        edited = geometry(authored, authored['edited_depth_m'])
        cases.append(authored | {
            'plane': 'Front', 'configuration': 'Default', 'reverse': False,
            'document_density_preference_kg_m3': 1000.0,
            'appearance_rgb': [0.11, 0.63, 0.27] if authored['anchor'] == 'corner' else [0.71, 0.19, 0.43],
            'first_assignment': first, 'second_assignment': second,
            'expected_before_edit': original, 'expected_after_depth_edit': edited,
            'expected_first_mass_kg': original['volume_m3'] * first['density_kg_m3'],
            'expected_second_mass_kg': original['volume_m3'] * second['density_kg_m3'],
            'expected_edited_mass_kg': edited['volume_m3'] * second['density_kg_m3'],
            'expected_swap_mass_ratio': second['density_kg_m3'] / first['density_kg_m3'],
            'expected_edit_mass_ratio': authored['edited_depth_m'] / authored['depth_m'],
            'ordinary_part_material_only': True, 'body_material_overrides_allowed': False,
        })
    return {'schema': SCHEMA, 'status': 'source-authoring recipe only; not a native result or CAD writer',
            'catalog_origin': catalog['origin'], 'native_launch_ready': False,
            'catalog_sha256': catalog_sha, 'oracle_sha256': ORACLE, 'control_sha256': CONTROL,
            'disclosed_cases': cases, 'required_fresh_native_processes': 10,
            'phases_per_case': ['author_initial_assignment', 'reopen_swap_material',
                                'reopen_edit_depth', 'fresh_reopen_depth'],
            'native_control_brackets': ['before', 'after'], 'writer_outputs': 0,
            'heldout_inputs_read': 0, 'heldout_credit': 0,
            'requires_before_writer': ['independent first-writer H source locks',
                                       'native source lifecycle and hash custody',
                                       'typed inventory and exact stream re-emission',
                                       'a separately frozen writer/equivalence protocol']}


def main():
    parser = ArgumentParser()
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'new output path is required')
    raw = args.catalog.read_bytes()
    result = plan(json.loads(raw), sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'passed': True, 'source_recipe_sha256': digest(args.output),
                      'native_runs': 0, 'writer_outputs': 0, 'heldout_inputs_read': 0}))


if __name__ == '__main__':
    main()
