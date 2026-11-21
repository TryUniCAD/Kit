from __future__ import annotations

from pathlib import PureWindowsPath
from math import isfinite

from AuthorCurves import require
from AuthorRectangleAnchors import BOSS, PARAMETERS, SKETCH


def material_identity(author, target, member, configuration):
    result = author.rec.call('observe typed ' + member, getattr(target, member), configuration)
    author.rec.data.setdefault('material_return_shapes', []).append({
        'member': member, 'python_type': type(result).__name__,
        'item_types': [type(value).__name__ for value in result] if isinstance(result, (tuple, list)) else None,
        'raw_value': result,
    })
    author.rec.flush()
    require(isinstance(result, (tuple, list)) and len(result) == 2 and all(value is None or type(value) is str for value in result),
            'material getter did not expose both the BSTR return and BSTR database out value; actual shape retained')
    return {'material': result[0] or '', 'database': result[1] or ''}


def compare_identity(author, actual, material):
    require(actual['material'] == material['name'], 'actual assigned material name differs')
    expected = PureWindowsPath(material['database_name']).stem.casefold()
    observed = PureWindowsPath(actual['database']).stem.casefold()
    require(expected and observed == expected, 'actual assigned database identity differs')


def effective_mass(author):
    properties = author.get(author.get(author.model, 'Extension'), 'CreateMassProperty')
    require(properties is not None, 'native material mass properties unavailable')
    author.set(properties, 'UseSystemUnits', True)
    values = {'volume': float(author.get(properties, 'Volume')),
              'area': float(author.get(properties, 'SurfaceArea')),
              'mass': float(author.get(properties, 'Mass')),
              'density': float(author.get(properties, 'Density')),
              'com': [float(value) for value in author.get(properties, 'CenterOfMass')],
              'use_system_units': bool(author.get(properties, 'UseSystemUnits')),
              'user_assigned': bool(author.get(properties, 'UserAssigned')),
              'override_mass': bool(author.get(properties, 'OverrideMass'))}
    require(all(isfinite(values[key]) and values[key] > 0 for key in ('volume', 'area', 'mass', 'density')),
            'native material properties are nonfinite or nonpositive')
    require(not values['override_mass'], 'manual mass override is outside the material source profile')
    values['mass_over_volume_density'] = values['mass'] / values['volume']
    return values


def selected_mass(author, body):
    author.get(author.model, 'ClearSelection2', True)
    try:
        require(author.get(body, 'Select2', False, author.sw.nothing()), 'selection refused for the actual solid')
        extension = author.get(author.model, 'Extension')
        properties = author.typed(author.get(extension, 'CreateMassProperty2'), 'MassProperty2')
        author.set(properties, 'UseSystemUnits', True)
        require(author.get(properties, 'Recalculate'), 'selected body mass recalculation failed')
        values = {name.lower(): float(author.get(properties, name)) for name in ('Volume', 'Mass', 'Density')}
        require(all(isfinite(value) and value > 0 for value in values.values()),
                'selected body properties are nonfinite or nonpositive')
        values['use_system_units'] = bool(author.get(properties, 'UseSystemUnits'))
        require(values['use_system_units'], 'selected body mass observer did not retain SI units')
        values['mass_over_volume_density'] = values['mass'] / values['volume']
        return values
    finally:
        author.get(author.model, 'ClearSelection2', True)


def observe(author, case, depth):
    selected = dict(case, depth_m=depth)
    base = author.snapshot(selected, 'Original')
    part = author.typed(author.model, 'PartDoc')
    configuration = author.get(author.get(author.model, 'ConfigurationManager'), 'ActiveConfiguration')
    name = str(author.get(configuration, 'Name'))
    require(name == case['configuration'], 'native active source configuration differs')
    solids = author.get(part, 'GetBodies2', 0, False) or ()
    visible = author.get(part, 'GetBodies2', 0, True) or ()
    require(len(solids) == len(visible) == 1, 'material source needs one actual visible solid')
    body = author.typed(solids[0], 'Body2')
    require(author.get(body, 'GetType') == 0, 'material source body is not an actual solid')
    result = {'rectangle': base, 'configuration': name,
              'part_material': material_identity(author, part, 'GetMaterialPropertyName2', name),
              'body_material': material_identity(author, body, 'GetMaterialPropertyName', name),
              'body_material_id_name': author.get(body, 'GetMaterialIdName2'),
              'body_material_user_name': author.get(body, 'GetMaterialUserName2'),
              'body_name': str(author.get(body, 'Name')),
              'legacy_mass': effective_mass(author), 'mass': selected_mass(author, body)}
    width, height = case['width_m'], case['height_m']
    volume = width * height * depth
    legacy = result['legacy_mass']
    author.rec.close_number('independent selected body material prism volume', result['mass']['volume'], volume, absolute=1e-16)
    author.rec.close_number('independent legacy material prism volume', legacy['volume'], volume, absolute=1e-16)
    author.rec.close_number('independent material prism area', legacy['area'], 2 * (width * height + width * depth + height * depth))
    center = [width / 2, height / 2, depth / 2] if case['kind'] == 'corner' else [0.0, 0.0, depth / 2]
    for actual, expected in zip(legacy['com'], center, strict=True):
        author.rec.close_number('independent material prism centroid', actual, expected)
    return result


def verify_density(author, snapshot, material, case, depth):
    compare_identity(author, snapshot['part_material'], material)
    expected = float(material['density_si_hypothesis'])
    author.rec.close_number('predeclared DENS@value SI interpretation vs live density', snapshot['mass']['density'], expected)
    author.rec.close_number('independent effective density from mass over analytic volume',
                            snapshot['mass']['mass'] / (case['width_m'] * case['height_m'] * depth), expected)
    author.rec.close_number('independent explicit-material mass prediction', snapshot['mass']['mass'],
                            case['width_m'] * case['height_m'] * depth * expected, absolute=1e-12)
    author.rec.close_number('native density agrees with mass divided by volume',
                            snapshot['mass']['mass_over_volume_density'], snapshot['mass']['density'])


def apply_material(author, material, configuration):
    part = author.typed(author.model, 'PartDoc')
    result = author.rec.call('apply explicit part material by actual database', part.SetMaterialPropertyName2,
                             configuration, material['database_path'], material['name'])
    author.rec.data.setdefault('material_setter_returns', []).append({'type': type(result).__name__, 'value': result})
    author.rec.flush()
    require(author.get(author.model, 'ForceRebuild3', False), 'assigned material did not rebuild')


def appearance_contrast(author, before, case):
    part = author.typed(author.model, 'PartDoc')
    rgb = [0.0, 1.0, 0.0] if case['kind'] == 'corner' else [1.0, 0.0, 1.0]
    value = tuple(rgb + [0.5, 0.5, 0.25, 0.5, 0.0, 0.0])
    variant = author.sw.VARIANT(author.sw.pythoncom.VT_ARRAY | author.sw.pythoncom.VT_R8, value)
    author.rec.call('author visual-only contrast', setattr, part, 'MaterialPropertyValues', variant)
    actual = author.rec.call('observe visual-only values', getattr, part, 'MaterialPropertyValues')
    require(isinstance(actual, (tuple, list)) and len(actual) == 9, 'visual property array shape differs')
    for observed, expected in zip(actual[:3], rgb, strict=True):
        author.rec.close_number('actual authored appearance RGB', observed, expected)
    after = observe(author, case, case['depth_m'])
    require(after['part_material'] == before['part_material'], 'visual-only contrast changed assigned identity')
    for key in ('volume', 'mass', 'density'):
        author.rec.close_number('visual-only contrast unchanged ' + key, after['mass'][key], before['mass'][key])
    author.rec.close_number('visual-only contrast unchanged area', after['legacy_mass']['area'], before['legacy_mass']['area'])
    return {'requested_visual_values': value, 'observed_visual_values': actual, 'state': after}


def preserved_model(author, before, after):
    left, right = before['rectangle'], after['rectangle']
    require(left['dimensions_m'] == right['dimensions_m'] and left['geometry'] == right['geometry']
            and left['relations'] == right['relations'] and left['constraint_status'] == right['constraint_status'],
            'material assignment changed the actual driving sketch/profile')
    def structure(rows):
        return [(row['type'], row['parent'], None if row['type'] == 'MaterialFolder' else row['name']) for row in rows]
    require(structure(left['tree']) == structure(right['tree']), 'material assignment changed modeled tree structure')
    author.rec.close_number('material-only change unchanged volume', after['mass']['volume'], before['mass']['volume'])
    author.rec.close_number('material-only change unchanged area', after['legacy_mass']['area'], before['legacy_mass']['area'])
    for actual, expected in zip(after['legacy_mass']['com'], before['legacy_mass']['com'], strict=True):
        author.rec.close_number('material-only change unchanged centroid', actual, expected)
