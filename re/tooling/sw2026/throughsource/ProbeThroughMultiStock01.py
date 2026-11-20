from argparse import ArgumentParser
from hashlib import sha256
from math import acos, isclose, sqrt
from pathlib import Path, PureWindowsPath
from time import time
import json
import os
import sys


HERE = Path(__file__).resolve()
PACKET = 'ThroughMultiStock03'
SCHEMA = 'kit.sw2026.disclosed-through-all-multistock.v3'
SHARED = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover')
GUEST = PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover') / PACKET
DISCLOSED = 'GeneratedThroughAllSelected01'
TRIAL = '2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a'
CONTROL = 'ProbeThroughAutoScope01.py'
SCOPE_PHASES = ('AutoScopeInitial', 'AutoScopeEdited', 'ExplicitScopeInitial', 'ExplicitScopeEdited')
PHASES = ('Before', 'AutoAuthor', 'AutoReopen', 'ExplicitAuthor', 'ExplicitReopen', *SCOPE_PHASES, 'After')
BUILD = '34.5.2.0604'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
STEADY, MOVING, CUT = 'SteadyStock', 'MovingStock', 'ThroughFeature'
PROFILES = ('SteadyProfile', 'MovingProfile', 'ThroughProfile')
PART = 'ThroughMultiStock.SLDPRT'
CUT_MARK = 1
PREVIOUS = {
    'packet': 'ThroughMultiStock02',
    'freeze_sha256': '78224c301b11cddd78591e9a8d30f556b2353c3fddbe2f61f599b99469345bb2',
    'auto_author_failure_sha256': '9c63835fed0e8747b9d6bcdb6ce73e472cf1f2bbdad02cedcd6040aed4b65c8b',
    'native_summary_sha256': '52bd6d7d9f6d1fa5dcf88cd00c44035dd9017954591b644f0e9f6741a69dbffe',
    'direct_scope_observed': {'feature_scope': True, 'auto_select': False, 'reported_count': -1, 'body_array': None},
}

DESIGN = {
    'stationary_m': [[.012, -.012, 0], [.030, -.004, .012]],
    'moving_initial_m': [[0, .004, .002], [.010, .012, .016]],
    'moving_edited_x_max_m': .029,
    'tool_center_m': [.021, 0],
    'tool_radius_m': .008,
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def checked(path, pin):
    need(path.is_file() and not path.is_symlink(), 'missing or redirected input: ' + path.name)
    data = path.read_bytes()
    need(digest(data) == pin, 'input hash mismatch: ' + path.name)
    return data


def publish(path, value):
    data = wire(value)
    with path.open('xb') as output:
        output.write(data)
    return digest(data)


def prior_freeze(release):
    previous_root = SHARED / release['packet']
    previous = json.loads(checked(previous_root / 'Freeze.json', release['freeze_sha256']))
    for name, pin in previous['tool_sha256'].items():
        checked(previous_root / name, pin)
    return previous


def body_prediction(box, side, notched):
    lo, hi = box
    x, y, z = (b - a for a, b in zip(lo, hi, strict=True))
    volume = x * y * z
    area = 2 * (x * y + y * z + z * x)
    moment = [volume * (a + b) / 2 for a, b in zip(lo, hi, strict=True)]
    if notched:
        cx, cy = DESIGN['tool_center_m']
        radius = DESIGN['tool_radius_m']
        offset = side * ((lo[1] if side > 0 else hi[1]) - cy)
        need(0 < offset < radius, 'the tool must cross exactly one side of its stock')
        half_chord = sqrt(radius ** 2 - offset ** 2)
        need(lo[0] < cx - half_chord < cx + half_chord < hi[0]
             and side * ((hi[1] if side > 0 else lo[1]) - cy) > radius,
             'the cap must fit clear of the other stock walls')
        angle = acos(offset / radius)
        segment = radius ** 2 * angle - offset * half_chord
        removed = segment * z
        volume -= removed
        area += (2 * radius * angle - 2 * half_chord) * z - 2 * segment
        moment[0] -= removed * cx
        moment[1] -= removed * cy + side * (2 / 3) * half_chord ** 3 * z
        moment[2] -= removed * (lo[2] + hi[2]) / 2
    return {'volume_m3': volume, 'area_m2': area, 'com_m': [m / volume for m in moment], 'box_m': [*lo, *hi]}


def predictions():
    a, b = DESIGN['stationary_m'], DESIGN['moving_initial_m']
    b_edited = [b[0], [DESIGN['moving_edited_x_max_m'], *b[1][1:]]]
    need(a[0][2] >= 0 and b[0][2] > 0 and a[1][1] < b[0][1]
         and b[1][0] < DESIGN['tool_center_m'][0] - DESIGN['tool_radius_m'],
         'the stocks must stay disjoint and the tool must initially miss B')
    return {
        'stock': {STEADY: body_prediction(a, -1, False), MOVING: body_prediction(b, 1, False)},
        'initial': {STEADY: body_prediction(a, -1, True), MOVING: body_prediction(b, 1, False)},
        'edited_fixed': {STEADY: body_prediction(a, -1, True), MOVING: body_prediction(b_edited, 1, False)},
        'edited_cut': {STEADY: body_prediction(a, -1, True), MOVING: body_prediction(b_edited, 1, True)},
    }


def freeze():
    need(os.name != 'nt', 'prepare this disclosed packet on the host')
    from ProbeThroughAutoScope01 import disclosed

    trial = disclosed(SHARED / DISCLOSED)
    previous = prior_freeze(PREVIOUS)
    prior_freeze(previous['previous_attempt'])
    values = predictions()
    need(previous['design'] == DESIGN and previous['predictions'] == values
         and previous['disclosed_control_sha256'] == trial['files_sha256'][trial['control_file']],
         'the selection-method retry must preserve the original geometry, predictions and control')
    root = SHARED / PACKET
    root.mkdir(mode=0o700, exist_ok=False)
    hashes = {}
    for path in (HERE, HERE.with_name(CONTROL)):
        source = path.read_bytes()
        with (root / path.name).open('xb') as output:
            output.write(source)
        hashes[path.name] = digest(source)
    plan = {'schema': SCHEMA, 'guest': str(GUEST), 'phase_order': PHASES,
            'disclosed_trial_sha256': TRIAL, 'disclosed_control_sha256': trial['files_sha256'][trial['control_file']],
            'tool_sha256': hashes, 'design': DESIGN, 'predictions': values, 'oracle_exe_sha256': ORACLE,
            'oracle_build': BUILD, 'previous_attempt': PREVIOUS}
    return {'freeze_sha256': publish(root / 'Freeze.json', plan), 'tool_sha256': hashes,
            'native_processes_started': 0, 'sealed_payloads_read': 0, 'predictions': plan['predictions']}


def installed_api():
    import ThroughAllApiMetadata as api

    extras = {
        'IExtrudeFeatureData2': ('FeatureScope', 'AutoSelect', 'FeatureScopeBodies', 'GetFeatureScopeBodiesCount',
                                'AccessSelections', 'ReleaseSelectionAccess'),
        'IModelDoc2': ('GetPathName', 'GetActiveConfiguration', 'GetConfigurationNames'),
        'IModelDocExtension': ('GetWhatsWrongCount', 'SelectByID2'),
        'IPartDoc': ('GetBodies2',),
        'IBody2': ('Name', 'GetFaces', 'GetMassProperties', 'GetExtremePoint'),
        'IFace2': ('GetFeature',),
        'ISelectionMgr': ('GetSelectedObjectCount2', 'GetSelectedObjectType3', 'GetSelectedObject6'),
    }
    api.MEMBERS = {**api.MEMBERS, **{key: tuple(dict.fromkeys((*api.MEMBERS.get(key, ()), *members)))
                                    for key, members in extras.items()}}
    api.ENUMS = {**api.ENUMS, 'swBodyType_e': {'swSolidBody': 0},
                 'swSelectType_e': {'swSelSKETCHES': 9, 'swSelSOLIDBODIES': 76}}
    value = api.metadata()
    getters = value['interfaces']['IExtrudeFeatureData2']['members']
    need({row['names'][0]: row['member_id'] for row in getters
          if row['invoke_kind'] == 2 and row['names'][0] in ('FeatureScope', 'AutoSelect')}
         == {'FeatureScope': 34, 'AutoSelect': 35}, 'registered scope getter identity differs')
    need(any(row['names'][0] == 'FeatureScopeBodies' and row['invoke_kind'] == 2 for row in getters),
         'registered selected-body property has no getter')
    for name, argc in (('AccessSelections', 2), ('ReleaseSelectionAccess', 0)):
        need(any(row['names'][0] == name and len(row['names']) == argc + 1 and row['invoke_kind'] == 1 for row in getters),
             'registered scope access signature differs: ' + name)
    selector = ('selectbyid2', 'name', 'type', 'x', 'y', 'z', 'append', 'mark', 'callout', 'selectoption')
    need(any(tuple(name.casefold() for name in row['names']) == selector and row['invoke_kind'] == 1
             for row in value['interfaces']['IModelDocExtension']['members']),
         'registered named-body selection signature differs')
    need(any(row['names'][0] == 'Name' and row['invoke_kind'] == 2 for row in value['interfaces']['IBody2']['members']),
         'registered native body name has no getter')
    return value


def profiles():
    a, b = DESIGN['stationary_m'], DESIGN['moving_initial_m']
    return {
        PROFILES[0]: ('front', 'CreateCornerRectangle', [a[0][0], a[0][1], 0, a[1][0], a[1][1], 0]),
        PROFILES[1]: ('right', 'CreateCornerRectangle', [-b[1][2], b[0][1], 0, -b[0][2], b[1][1], 0]),
        PROFILES[2]: ('front', 'CreateCircleByRadius', [*DESIGN['tool_center_m'], 0, DESIGN['tool_radius_m']]),
    }


def body_owners(author, body):
    body = author.typed(body, 'Body2')
    faces = list(author.get(body, 'GetFaces') or ())
    need(0 < len(faces) <= 20, 'unsupported body face inventory')
    names = []
    for face in faces:
        owner = author.get(author.typed(face, 'Face2'), 'GetFeature')
        need(owner is not None, 'a native body face has no actual owning feature')
        names.append(str(author.get(owner, 'Name')))
    stock = set(names) & {STEADY, MOVING}
    need(len(stock) == 1 and set(names) <= {STEADY, MOVING, CUT}, 'body does not identify exactly one authored stock producer')
    return stock.pop(), sorted(names)


def active_bodies(author):
    part = author.typed(author.model, 'PartDoc')
    bodies = list(author.get(part, 'GetBodies2', 0, False) or ())
    need(len(bodies) == 2, 'the authored stocks must remain two actual solids')
    result = {}
    for body in bodies:
        name, owners = body_owners(author, body)
        need(name not in result, 'multiple bodies identify the same stock producer')
        result[name] = (author.typed(body, 'Body2'), owners)
    need(set(result) == {STEADY, MOVING}, 'the two expected producers are not present')
    return result


def body_state(author, body, owners):
    mass = [float(value) for value in author.get(body, 'GetMassProperties', 1.0)]
    need(len(mass) == 12 and isclose(mass[3], mass[5], rel_tol=2e-7) and min(mass[3:6]) > 0,
         'invalid native per-body mass properties at density 1')
    bounds = []
    for sign in (-1, 1):
        for axis in range(3):
            direction = [0.] * 3
            direction[axis] = sign
            points = [author.sw.VARIANT(author.sw.pythoncom.VT_BYREF | author.sw.pythoncom.VT_R8, 0.0) for _ in range(3)]
            need(bool(author.get(body, 'GetExtremePoint', *direction, *points)), 'exact body extrema query failed')
            bounds.append(float(points[axis].value))
    return {'volume_m3': mass[3], 'area_m2': mass[4], 'com_m': mass[:3],
            'box_m': bounds, 'face_owners': owners, 'cut_face': CUT in owners}


def compare_body(author, label, row, prediction, cut):
    need(row['cut_face'] is cut, label + ' cut face owner differs')
    author.rec.close_number(label + ' volume', row['volume_m3'], prediction['volume_m3'], absolute=1e-22)
    author.rec.close_number(label + ' area', row['area_m2'], prediction['area_m2'], absolute=1e-18)
    for key in ('com_m', 'box_m'):
        for axis, (actual, expected) in enumerate(zip(row[key], prediction[key], strict=True)):
            author.rec.close_number(f'{label} {key} {axis}', actual, expected, absolute=1e-10)


def cut_definition(author):
    return author.typed(author.get(author.feature(CUT), 'GetDefinition'), 'ExtrudeFeatureData2')


def cut_scope(author, data, context):
    scoped = bool(author.get(data, 'FeatureScope'))
    automatic = bool(author.get(data, 'AutoSelect')) if scoped else None
    result = {'context': context, 'feature_scope': scoped, 'auto_select': automatic, 'scope_owners': None,
              'owner_status': 'automatic' if automatic else 'all_bodies',
              'reported_count': None, 'returned_array_count': None}
    if scoped and not automatic:
        count = int(author.get(data, 'GetFeatureScopeBodiesCount'))
        raw = author.get(data, 'FeatureScopeBodies')
        bodies = None if raw is None else list(raw)
        result.update(reported_count=count, returned_array_count=None if bodies is None else len(bodies))
        if count == -1 and bodies is None and context == 'direct':
            result['owner_status'] = 'observed_direct_unavailability'
        elif bodies is None:
            result['owner_status'] = 'array_absent'
        elif count != len(bodies):
            result['owner_status'] = 'count_mismatch'
        else:
            need(0 <= count <= 2, 'scope body array exceeds the two-stock model')
            names = sorted(body_owners(author, body)[0] for body in bodies)
            need(len(set(names)) == count, 'duplicate body in actual scope array')
            result.update(owner_status='available', scope_owners=names)
    author.rec.data['last_cut_scope'] = result
    author.rec.flush()
    return result


def observe_profiles(author):
    from ThroughAllSourcePlan import model_point

    result = {}
    for name, (plane, method, values) in profiles().items():
        author.sketch = author.get(author.feature(name), 'GetSpecificFeature2')
        actual = author.geometry()
        if method == 'CreateCircleByRadius':
            profile = {'kind': 'circle', 'center_mm': [value * 1000 for value in values[:2]],
                       'radius_mm': values[3] * 1000}
        else:
            x0, y0, _, x1, y1, _ = values
            profile = {'kind': 'rectangle', 'center_mm': [500 * (x0 + x1), 500 * (y0 + y1)],
                       'width_mm': 1000 * (x1 - x0), 'height_mm': 1000 * (y1 - y0)}
        author.check_geometry({'profile': profile}, actual)
        inverse = author.get(author.get(author.sketch, 'ModelToSketchTransform'), 'Inverse')
        matrix = [float(value) for value in author.get(inverse, 'ArrayData')]
        need(len(matrix) >= 13, 'sketch frame is incomplete')
        for local in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)):
            point = [matrix[9 + col] + matrix[12] * sum(local[row] * matrix[row * 3 + col]
                     for row in range(3)) for col in range(3)]
            need(all(isclose(a, b, abs_tol=1e-12) for a, b in zip(point, model_point(plane, local), strict=True)),
                 'actual signed sketch support differs from the authored plane')
        result[name] = {'shape': profile, 'sketch_to_model': matrix}
    return result


def parameter(author, stock, expected):
    dimension = author.get(author.model, 'Parameter', 'D1@' + stock)
    need(dimension is not None and not author.get(dimension, 'ReadOnly')
         and int(author.get(dimension, 'DrivenState')) == 2, 'the stock D1 is not a native editable driver')
    name = str(author.get(dimension, 'FullName'))
    need(name.split('@')[:2] == ['D1', stock], 'the stock D1 owner is wrong')
    value = float(author.get(dimension, 'SystemValue'))
    author.rec.close_number(stock + ' D1 value', value, expected)
    return dimension, {'owner': name, 'value_m': value}


def snapshot(author, label, edited, values, rebuild=False):
    if rebuild:
        need(bool(author.get(author.model, 'ForceRebuild3', False)), 'full native rebuild failed')
    extension = author.get(author.model, 'Extension')
    need(int(author.get(extension, 'GetWhatsWrongCount')) == 0, 'native document reports feature errors or warnings')
    configuration = str(author.get(author.get(author.model, 'GetActiveConfiguration'), 'Name'))
    need(configuration == 'Default' and list(author.get(author.model, 'GetConfigurationNames')) == [configuration],
         'the document is outside the ordinary one-configuration case')
    tree = author.feature_tree(required_names=(*PROFILES, STEADY, MOVING, CUT))
    operation_order = [row['name'] for row in tree if row['name'] in {STEADY, MOVING, CUT}]
    need(operation_order == [STEADY, MOVING, CUT], 'native feature order differs')
    driver_rows = {}
    for profile, name, depth in ((PROFILES[0], STEADY, DESIGN['stationary_m'][1][2]),
                                 (PROFILES[1], MOVING, DESIGN['moving_edited_x_max_m'] if edited
                                  else DESIGN['moving_initial_m'][1][0])):
        stock = author.definition(name)
        need(stock['fallback_type'] in ('Boss', 'Extrusion', 'BaseBody') and stock['end_forward'] == 0
             and stock['from_type'] == 0 and profile in stock['parents']
             and not any(stock[key] for key in ('both_directions', 'reverse_direction', 'thin', 'draft_forward', 'draft_reverse')),
             'a stock left its single forward blind profile')
        author.rec.close_number(name + ' forward blind depth', stock['depth_forward_m'], depth)
        _, driver_rows[name] = parameter(author, name, depth)
    cut = author.definition(CUT)
    need(cut['fallback_type'] == 'Cut' and cut['end_forward'] == 1 and cut['end_reverse'] == 0
         and cut['reverse_direction'] and cut['from_type'] == 0 and cut['dimensions'] == []
         and cut['depth_forward_m'] == cut['depth_reverse_m'] == 0 and PROFILES[2] in cut['parents']
         and not any(cut[key] for key in ('both_directions', 'thin', 'draft_forward', 'draft_reverse',
                                         'flip_side_to_cut', 'normal_cut')), 'the cut left its depthless +Z profile')
    shapes = observe_profiles(author)
    solids = {name: body_state(author, body, owners) for name, (body, owners) in active_bodies(author).items()}
    b_cut = solids[MOVING]['cut_face']
    need(not b_cut or edited, 'the initially missed stock has cut-owned geometry')
    case = ('edited_cut' if b_cut else 'edited_fixed') if edited else 'initial'
    for name, row in solids.items():
        compare_body(author, label + ' ' + name, row, values[case][name], name == STEADY or b_cut)
    return {'tree': tree, 'profiles': shapes, 'drivers': driver_rows, 'cut': cut, 'bodies': solids,
            'cut_scope': cut_scope(author, cut_definition(author), 'direct'),
            'moving_stock_cut': b_cut, 'analytic_case': case}


def build(author, controller, automatic, values):
    author.model = author.rec.call('create the disclosed multistock part', controller.new_part)
    manager = author.get(author.model, 'FeatureManager')
    specs = profiles()
    for profile, name, depth in ((PROFILES[0], STEADY, DESIGN['stationary_m'][1][2]),
                                 (PROFILES[1], MOVING, DESIGN['moving_initial_m'][1][0])):
        plane, method, coordinates = specs[profile]
        author.create_profile({'plane': plane}, profile, method, coordinates)
        args = (True, False, False, 0, 0, depth, 0.0, False, False, False, False,
                0.0, 0.0, False, False, False, False, False, False, False, 0, 0.0, False)
        boss = author.get(manager, 'FeatureExtrusion3', *args)
        need(boss is not None, 'native nonmerging stock authoring failed')
        author.set(boss, 'Name', name)
    need(bool(author.get(author.model, 'ForceRebuild3', False)), 'stock rebuild failed')
    for name, (body, owners) in active_bodies(author).items():
        compare_body(author, 'uncut ' + name, body_state(author, body, owners), values['stock'][name], False)
    plane, method, coordinates = specs[PROFILES[2]]
    author.create_profile({'plane': plane}, PROFILES[2], method, coordinates)
    selection = author.get(author.model, 'SelectionManager')
    selected_name = None
    if not automatic:
        names = {role: author.get(body, 'Name') for role, (body, _) in active_bodies(author).items()}
        need(all(isinstance(name, str) and name.strip() for name in names.values())
             and len({name.casefold() for name in names.values()}) == 2, 'the two actual stock body names are ambiguous')
        selected_name = names[STEADY]
        extension = author.get(author.model, 'Extension')
        need(bool(author.get(extension, 'SelectByID2', selected_name, 'SOLIDBODY', 0., 0., 0.,
                             True, CUT_MARK, author.sw.nothing(), 0)), 'explicit named native cut body selection failed')
        need(int(author.get(selection, 'GetSelectedObjectCount2', CUT_MARK)) == 1
             and int(author.get(selection, 'GetSelectedObjectType3', 1, CUT_MARK)) == 76,
             'explicit selected role is not exactly one marked solid')
        selected = author.typed(author.get(selection, 'GetSelectedObject6', 1, CUT_MARK), 'Body2')
        need(author.get(selected, 'Name') == selected_name and body_owners(author, selected)[0] == STEADY,
             'the explicitly selected native solid differs from the requested stock')
    need(int(author.get(selection, 'GetSelectedObjectCount2', -1)) == (1 if automatic else 2)
         and int(author.get(selection, 'GetSelectedObjectCount2', 0)) == 1
         and int(author.get(selection, 'GetSelectedObjectType3', 1, 0)) == 9, 'wrong native through-all profile or additional selection')
    args = (True, False, True, 1, 0, .012, .006, False, False, False, False, 0.0, 0.0,
            False, False, False, False, False, True, automatic, False, False, False, 0, 0.0, False, False)
    author.rec.data['cut_request'] = {'arguments': list(args), 'profile_mark': 0,
                                     'body_mark': None if automatic else CUT_MARK,
                                     'selected_body_name': selected_name,
                                     'preselected_producer': None if automatic else STEADY}
    author.rec.flush()
    feature = author.get(manager, 'FeatureCut4', *args)
    need(feature is not None, 'native FeatureCut4 refused the requested scope')
    author.set(feature, 'Name', CUT)
    author.get(author.model, 'ClearSelection2', True)


def prior_phase(folder, phase):
    path = folder / phase / 'Record.json'
    need(path.is_file() and not path.is_symlink(), 'missing phase receipt: ' + phase)
    row = json.loads(path.read_bytes())
    need(row['job']['phase'] == phase, 'phase receipt names another run')
    return row


def edit_stock(author):
    initial = DESIGN['moving_initial_m'][1][0]
    target = DESIGN['moving_edited_x_max_m']
    dimension, _ = parameter(author, MOVING, initial)
    need(int(author.get(dimension, 'SetSystemValue3', target, 1, author.sw.nothing())) == 0,
         'the native upstream D1 edit failed')


def observe_scope(author, edited, values, result):
    initial = snapshot(author, 'scope-only initial', False, values, rebuild=True)
    result['before_edit'] = initial
    if edited:
        edit_stock(author)
    result['pre_access'] = snapshot(author, 'scope-only edited', True, values, rebuild=True) if edited else initial
    data = cut_definition(author)
    accessed = bool(author.get(data, 'AccessSelections', author.model, author.sw.nothing()))
    result['access_selections'] = accessed
    need(accessed, 'registered scope access returned false')
    try:
        result['accessed_scope'] = cut_scope(author, data, 'access_selections')
    finally:
        author.get(data, 'ReleaseSelectionAccess')
        result['selection_access_released'] = True
    need(int(author.get(author.get(author.model, 'Extension'), 'GetWhatsWrongCount')) == 0,
         'scope-only access left native feature errors or warnings')


def candidate(folder, phase, plan, api_sha):
    import Swapp
    from AuthorCurves import Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor

    automatic = phase.startswith('Auto')
    authoring = phase.endswith('Author')
    reviewing = phase in SCOPE_PHASES
    review_edited = reviewing and phase.endswith('Edited')
    arm = 'Auto' if automatic else 'Explicit'
    stage = folder / phase
    stage.mkdir(exist_ok=False)
    record = Recorder(stage / 'Record.json', {'schema': SCHEMA, 'phase': phase, 'api_sha256': api_sha})
    values = plan['predictions']
    path = folder / (arm + 'Author') / PART
    result = {'passed': False, 'requested_automatic': automatic}
    controller = observer = None
    pin = None
    with AssemblyLoadMonitor() as monitor:
        try:
            if not authoring:
                pin = prior_phase(folder, arm + 'Author')['result']['saved_sha256']
                checked(path, pin)
                result['opened_sha256'] = pin
            record.call('verify the serial native oracle is idle', Swapp.sweep)
            controller = record.call('start the pinned native scope observer', Swapp.Sw)
            identity = record.call('verify the native executable', application_identity, controller.app)
            need(identity['version_matches'] and identity['file_version'] == BUILD and identity['sha256'] == ORACLE,
                 'the installed native build changed')
            result['native_identity'] = identity
            observer = ThroughAllAuthor(controller.app, record, Swapp)
            if authoring:
                build(observer, controller, automatic, values)
                result['created'] = snapshot(observer, 'created', False, values)
            else:
                model, error, warning = record.call('fresh open of the owned unedited native save', controller.open, path,
                                                     read_only=reviewing and not review_edited)
                observer.model = model
                result['open'] = [model is not None, error, warning]
                need(result['open'] == [True, 0, 0] and Path(observer.get(model, 'GetPathName')).samefile(path),
                     'owned original was not reopened at its actual locator without warnings')
                if not reviewing:
                    result['cold'] = snapshot(observer, 'cold', False, values)
            if reviewing:
                observe_scope(observer, review_edited, values, result)
            else:
                result['before_edit'] = snapshot(observer, 'before edit', False, values, rebuild=True)
                if authoring:
                    need(not path.exists(), 'the owned save destination already exists')
                    result['save'] = list(record.call('save only the unedited owned native part', controller.save_as, observer.model, path))
                    need(result['save'] == [True, 0, 0] and path.is_file() and Path(observer.get(observer.model, 'GetPathName')).samefile(path),
                         'own native save warned or used another locator')
                    pin = digest(path.read_bytes())
                    result['saved_sha256'] = pin
                    result['after_save'] = snapshot(observer, 'after save', False, values)
                edit_stock(observer)
                result['after_edit'] = snapshot(observer, 'after edit', True, values, rebuild=True)
                need(result['before_edit']['tree'] == result['after_edit']['tree']
                     and result['before_edit']['profiles'] == result['after_edit']['profiles'],
                     'an upstream depth change altered the feature tree or tool/profile definitions')
            result['passed'] = True
        except Exception as error:
            record.failure(error)
        finally:
            if controller is not None:
                if observer is not None and observer.model is not None:
                    record.call('close the owned document without saving the edit', controller.close_doc, observer.model)
                try:
                    controller.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                result['controller_diagnostics'] = controller.diagnostics
    result['original_save_unchanged'] = bool(pin and path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == pin)
    result['dialogs'] = monitor.log
    result['passed'] = bool(result['passed'] and result['original_save_unchanged'] and not result['dialogs']
                            and not result.get('controller_diagnostics') and record.data['first_failure'] is None)
    record.data.update(result=result, passed=result['passed'], finished_at=time())
    record.flush()
    return {'phase': phase, 'passed': result['passed'], 'record_sha256': digest(record.path.read_bytes())}


def outcome(start, end, moving_stock_cut):
    if not moving_stock_cut:
        return 'moving stock remained intact'
    if not start['feature_scope']:
        return 'moving stock cut with initial all-body scope'
    if start['auto_select']:
        return 'moving stock cut with initial native automatic flag'
    if start['scope_owners'] is None:
        return 'moving stock cut with initial membership unknown'
    if MOVING in start['scope_owners']:
        return 'moving stock cut from an initially enrolled body'
    if start['scope_owners'] == [STEADY] and end['scope_owners'] == sorted((STEADY, MOVING)):
        return 'moving stock cut and observed owner list expanded'
    if end['scope_owners'] is None:
        return 'moving stock cut with edited membership unknown'
    return 'moving stock cut without the expected owner-list expansion'


def same_measured_model(first, second):
    keys = ('tree', 'profiles', 'drivers', 'cut', 'analytic_case')
    return all(first[key] == second[key] for key in keys)


def scope_evidence(row, before, state, source_sha):
    if row is None:
        return None
    data = row['result']
    probe = data.get('accessed_scope')
    initial = data.get('before_edit')
    compared = data.get('pre_access')
    if not row['passed'] or probe is None or initial is None or compared is None:
        return {'passed': False, 'access_selections': data.get('access_selections'), 'accessed_scope': probe}
    direct = state['cut_scope']
    pre_access = compared['cut_scope']
    matching_model = (data['opened_sha256'] == source_sha and same_measured_model(initial, before)
                      and same_measured_model(compared, state))
    matching_flags = all(direct[key] == pre_access[key] == probe[key] for key in ('feature_scope', 'auto_select'))
    owner_lists = {tuple(record['scope_owners']) for record in (direct, pre_access, probe)
                   if record['scope_owners'] is not None}
    return {'passed': matching_model and matching_flags and len(owner_lists) <= 1,
            'matching_model': matching_model, 'matching_flags': matching_flags, 'owner_conflict': len(owner_lists) > 1,
            'pre_access_scope': pre_access, 'accessed_scope': probe}


def explicit_pair(first, second):
    return all(row['feature_scope'] and row['auto_select'] is False and row['scope_owners'] == [STEADY]
               for row in (first, second))


def summary(folder, freeze_sha, api_sha):
    rows = {phase: prior_phase(folder, phase) for phase in PHASES if (folder / phase / 'Record.json').is_file()}
    processes = [row['result']['native_identity']['process_creation_filetime']
                 for row in rows.values() if 'native_identity' in row['result']]
    serial = all(a['finished_at'] <= b['started_at'] for a, b in zip(tuple(rows.values()), tuple(rows.values())[1:]))
    healthy = (serial and len(processes) == len(set(processes))
               and all(phase in rows and rows[phase]['passed'] for phase in ('Before', 'After')))
    outcomes = {}
    if healthy:
        for arm in ('Auto', 'Explicit'):
            if not all(phase in rows and rows[phase]['passed'] for phase in (arm + 'Author', arm + 'Reopen')):
                continue
            authored, reopened = (rows[arm + suffix]['result'] for suffix in ('Author', 'Reopen'))
            before, edited = reopened['before_edit'], reopened['after_edit']
            start, end = before['cut_scope'], edited['cut_scope']
            source_sha = authored['saved_sha256']
            matched_save = same_measured_model(authored['after_save'], reopened['cold']) and reopened['opened_sha256'] == source_sha
            if not matched_save:
                outcomes[arm] = {'geometry_passed': False, 'saved_sha256': source_sha}
                continue
            audited = {suffix: scope_evidence(rows.get(arm + 'Scope' + suffix), before, state, source_sha)
                       for suffix, state in (('Initial', before), ('Edited', edited))}
            resolved = all(audit is not None and audit['passed'] for audit in audited.values())
            scoped_start, scoped_end = ((audited[suffix]['accessed_scope'] for suffix in ('Initial', 'Edited'))
                                        if resolved else (None, None))
            explicit_observed = None
            if arm == 'Explicit':
                consistent = all(audit is None or not (audit.get('owner_conflict') or audit.get('matching_flags') is False)
                                 for audit in audited.values())
                explicit_observed = (consistent and not authored['after_edit']['moving_stock_cut']
                                     and not edited['moving_stock_cut']
                                     and (explicit_pair(start, end) or resolved and explicit_pair(scoped_start, scoped_end)))
            outcomes[arm] = {
                'geometry_passed': True,
                'same_process': outcome(authored['after_save']['cut_scope'], authored['after_edit']['cut_scope'],
                                        authored['after_edit']['moving_stock_cut']),
                'fresh_reopen_direct': outcome(start, end, edited['moving_stock_cut']),
                'fresh_reopen_accessed': outcome(scoped_start, scoped_end, edited['moving_stock_cut']) if resolved else None,
                'moving_stock_reopen': edited['bodies'][MOVING],
                'created_scope': authored['created']['cut_scope'], 'saved_scope': authored['after_save']['cut_scope'],
                'cold_scope': reopened['cold']['cut_scope'], 'cold_rebuilt_scope': start,
                'author_edited_scope': authored['after_edit']['cut_scope'],
                'reopen_edited_scope': end, 'separate_scope_observations': audited,
                'explicit_cold_scope_confirmed': explicit_observed, 'saved_sha256': source_sha,
            }
    passed = set(outcomes) == {'Auto', 'Explicit'} and all(arm['geometry_passed'] for arm in outcomes.values())
    result = {'schema': SCHEMA, 'passed': passed, 'freeze_sha256': freeze_sha, 'api_sha256': api_sha,
              'distinct_processes': len(set(processes)), 'serial': serial, 'healthy_bracket': healthy,
              'phase_receipts': {phase: digest((folder / phase / 'Record.json').read_bytes()) for phase in rows},
              'phase_status': {phase: row['passed'] for phase, row in rows.items()}, 'outcomes': outcomes,
              'sealed_payloads_read': 0, 'production_coverage': 0, 'heldout_coverage': 0}
    return result | {'result_sha256': publish(folder / 'Result.json', result)}


def main():
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest='mode', required=True)
    modes.add_parser('freeze')
    for mode in ('metadata', 'phase', 'summary'):
        command = modes.add_parser(mode)
        command.add_argument('manifest', type=Path)
        command.add_argument('pin')
        if mode == 'phase':
            command.add_argument('phase', choices=PHASES)
    args = parser.parse_args()
    if args.mode == 'freeze':
        sys.path.insert(0, str(HERE.parent))
        result = freeze()
    else:
        need(os.name == 'nt', 'registered API and native phases require the Windows guest')
        plan = json.loads(checked(args.manifest, args.pin))
        root = args.manifest.parent
        need(root == Path(GUEST) and plan['guest'] == str(root) and HERE == root / HERE.name
             and plan['schema'] == SCHEMA and plan['phase_order'] == list(PHASES)
             and plan['disclosed_trial_sha256'] == TRIAL and plan['oracle_exe_sha256'] == ORACLE
             and plan['oracle_build'] == BUILD and plan['design'] == DESIGN
             and plan['previous_attempt'] == PREVIOUS, 'freeze identity or scope changed')
        for name in (HERE.name, CONTROL):
            checked(root / name, plan['tool_sha256'][name])
        sys.path.insert(0, str(root))
        from ProbeThroughAutoScope01 import disclosed, measure

        trial_root = root.with_name(DISCLOSED)
        trial = disclosed(trial_root)
        need(plan['disclosed_control_sha256'] == trial['files_sha256'][trial['control_file']], 'disclosed control changed')
        sys.path.insert(0, str(trial_root / 'Tools'))
        folder = Path('C:/KitSdkCandidates') / PACKET
        need(folder.resolve() == folder and not folder.is_symlink(), 'owned work folder is redirected')
        metadata = folder / 'ApiMetadata.json'
        if args.mode == 'metadata':
            api = installed_api()
            folder.mkdir(exist_ok=False)
            result = {'metadata_sha256': publish(metadata, {'freeze_sha256': args.pin, 'api': api}),
                      'native_processes_started': 0}
        else:
            raw = metadata.read_bytes()
            need(json.loads(raw)['freeze_sha256'] == args.pin, 'registered metadata is not bound to this packet')
            api_sha = digest(raw)
            if args.mode == 'summary':
                result = summary(folder, args.pin, api_sha)
            elif args.phase in ('Before', 'After'):
                result = measure(folder, args.phase, trial_root, trial)
            else:
                phase = args.phase
                need(prior_phase(folder, 'Before')['passed'], 'the leading healthy control is absent')
                arm = 'Auto' if phase.startswith('Auto') else 'Explicit'
                if phase == 'ExplicitAuthor':
                    need(prior_phase(folder, 'AutoAuthor')['result'].get('created') is not None,
                         'automatic geometry did not pass its initial authoring checks')
                if not phase.endswith('Author'):
                    need(prior_phase(folder, arm + 'Author')['passed'], 'the arm has no qualified unedited save')
                if phase in SCOPE_PHASES:
                    need(prior_phase(folder, arm + 'Reopen')['passed'], 'the arm has no independent rollback-free geometry')
                result = candidate(folder, args.phase, plan, api_sha)
    sys.stdout.buffer.write(wire(result))
    return int(result.get('passed') is False)


if __name__ == '__main__':
    raise SystemExit(main())
