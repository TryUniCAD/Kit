from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
HOST_HOME = Path('/Users/odin')
MANAGED = HOST_HOME / 'Documents/UniCAD/Oracle121Takeover'
SOURCE = MANAGED / 'WidthDepthFresh01/EquationDepthAlpha.json'
SOURCE_SHA = 'bd5ddb99de56fef9bdbc082504e7f83af743ce7e6e696395a262a3b67d14104c'
EARLIER = MANAGED / 'WidthDepthLocalReferences03'
EARLIER_SHA = '8116017bee491b87e3ed2e7fa1bb2a6e8e893be1f991924e71c3a932dfe1ba56'
CONTROL_NAME = 'DisclosedEquationControl.SLDPRT'
CONTROL_SHA = '8d79922604aba1816348ae2b62d3601c44a088dccf4b1373dd17ca0e39b02e58'
METADATA_SHA = '60db6487419215724e9f48f7f17ae1f5aa373e6cb39a868dda02c31658f7f78c'
SCHEMA = 'kit.sw2026.width-depth-same-locator.v1'
PHASES = ('ControlBefore', 'PlainEdit', 'PlainReopen', 'ReferenceEdit', 'ReferenceReopen', 'ControlAfter')
LAYOUT = ('Contents/Config-0', 'Contents/Config-0-ResolvedFeatures')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def canonical(data):
    return (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink(), f'frozen file is missing or redirected: {path.name}')
    data = path.read_bytes()
    require(digest(data) == wanted, f'frozen digest changed: {path.name}')
    return data


def publish(path, data):
    with path.open('xb') as stream:
        stream.write(data)
    return digest(data)


def unc(path):
    return str(PureWindowsPath(r'\\Mac\Home', *path.relative_to(HOST_HOME).parts))


def final_locator(name):
    require(re.fullmatch(r'WidthDepthSameLocator[0-9]{2}', name), 'use a new WidthDepthSameLocatorNN packet')
    return PureWindowsPath(r'C:\KitSdkCandidates', f'{name}.SLDPRT')


def geometry(width, height, depth):
    return {'body_count': 1, 'volume_m3': width * height * depth,
            'area_m2': 2 * (width * height + width * depth + height * depth),
            'com_m': [width / 2, height / 2, depth / 2]}


def prepare(name, revision):
    import subprocess
    import tarfile
    from tempfile import TemporaryDirectory

    final_locator(name)
    require(re.fullmatch(r'[0-9a-f]{40}', revision), 'require the full source commit')
    root = MANAGED / name
    require(not root.exists() and root.resolve() == root, 'packet directory is already used or redirected')
    subprocess.run(['git', 'merge-base', '--is-ancestor', revision, 'HEAD'], cwd=REPO, check=True)
    with TemporaryDirectory(prefix='kit-width-depth-') as directory:
        pin = Path(directory)
        archive = pin / 'source.tar'
        helper = 'tests/Convert/Solidworks/Research/ConstructionGuard.py'
        subprocess.run(['git', 'archive', '--output', str(archive), revision, 'src', helper,
                        'tests/__init__.py', 'tests/Convert/__init__.py', 'tests/Convert/Solidworks/__init__.py'], cwd=REPO, check=True)
        with tarfile.open(archive) as stream:
            stream.extractall(pin, filter='data')
        research = 're/tooling/sw2026'
        subprocess.run(['git', 'archive', '--output', str(archive), '--prefix=' + research + '/',
                        revision + ':' + research], cwd=REPO, check=True)
        with tarfile.open(archive) as stream:
            stream.extractall(pin, filter='data')
        tool = pin / HERE.relative_to(REPO)
        publish(tool, HERE.read_bytes())
        action = 'import runpy,sys; runpy.run_path(sys.argv[1])["freeze"](sys.argv[2],sys.argv[3])'
        return subprocess.run([sys.executable, '-I', '-B', '-c', action, str(tool), name, revision], cwd=pin).returncode


def host_paths():
    sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent), str(REPO / 'src'), str(REPO)]


def write_variant(lane):
    from codecs import lookup
    from importlib import import_module

    host_paths()
    import BuildWidthDepthPart as reference
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    request = json.load(sys.stdin)
    for name in ('DocumentAssemblyValidate', 'DocumentFeatureValidate', 'DocumentReferenceValidate'):
        import_module('interchange.document.Validation.' + name)
    for name in ('utf-16-le', 'utf-8', 'latin-1'):
        lookup(name)
    audit = BuildAudit(REPO / 're/tooling/sw2026/serial/defs')
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    if lane == 'Reference':
        payload, proof = reference.compose(request)
    else:
        require(lane == 'Plain', 'the generated lane is not in scope')
        doc = reference.FromData(request['document'])
        inputs = reference.settings(request['settings'])
        plan = reference.ProjectRectDims(doc)
        reference.CheckPartInput(doc, inputs, plan)
        ids = reference.PersistentIds()
        system = reference.MakePartBaseMut(inputs, plan, ids)
        profile = reference.MakePartProfMut(system, inputs, plan, ids)
        drivers = reference.MakeRectDimsMut(profile, reference.input_value(request['rectangle_dimensions'], inputs),
                                            ids, plan.SketchDriverNames)
        reference.MakeCornerMut(profile, system.OriginValue)
        part = reference.FinishBlindMut(system, profile, inputs, plan, ids,
                                        reference.MakeSketchKeys(drivers, inputs.DocumentUnits.LengthUnit))
        payload = part.BytesValue
        proof = {'expression': None, 'config_map_final': part.ConfigValue.MapValue.CounterValue,
                 'resolved_map_final': part.ResolvedValue.MapValue.CounterValue}
    proof.update(runtime_input_file_reads=len(audit.DeniedReads), sha256=digest(payload), bytes=len(payload))
    print(json.dumps(proof, sort_keys=True), file=sys.stderr)
    sys.stdout.buffer.write(payload)


def stream_proof(files, locator, expression):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    streams, rows = {}, {}
    for lane, raw in files.items():
        a = SldprtArchive.from_bytes(raw)
        require(a.format_version == 4 and len(a.streams) == 10, 'expected ordinary ten-stream generated part')
        streams[lane] = a.streams
        header, top = (ReadHeaderGraph(a.require(key), 19000) for key in ('Contents/Config-0-ModelHeader', 'Header2'))
        path = ReadFileKey(header.FieldsValue['f38'])
        require(path == ReadFileKey(top.FieldsValue['f38']) and path[:3] == (locator.stem, str(locator), 2),
                'both generated headers must encode the exact C: staging locator')
        related = lane == 'Reference'
        config = ReadConfigMut(a.require(LAYOUT[0]), 19000, header, PartRelations=related)
        config_again, written = WriteConfigMut(config.RootValue, 19000, header, PartRelations=related)
        cmgr = ReadCmgrMut(a.require('Contents/CMgr'), 19000)
        context = {'cmgr_f658': cmgr.RootValue.FieldsValue['f658'], 'model_is_part': 1, 'model_compressed_stream': 1}
        resolved = ReadResolvedMut(a.require(LAYOUT[1]), 19000, config.MapValue, context)
        resolved_again, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, written.MapValue, context)
        require((config_again, resolved_again) == tuple(a.require(key) for key in LAYOUT),
                'typed Config and linked Resolved replay must preserve the generated bytes')
        manager = config.RootValue.FieldsValue['f9d0']
        listing = manager.FieldsValue['f58']
        relations = [row['o'] for row in listing['items']]
        require(listing['n'] == len(relations) == int(related) and len(resolved.RootsValue) == 19,
                'typed part graph lost its declared equation count or resolved feature inventory')
        if related:
            relation, = relations
            sides = tuple(relation.FieldsValue[key] for key in ('f58', 'f60'))
            wrappers = [row['o'].FieldsValue['f80'] for side in sides for row in side.FieldsValue['f10']['items']
                        if row['o'].ClassValue.NameValue == 'moRelDimension_c']
            handles = [wrapper.FieldsValue['f58'] for wrapper in wrappers]
            require(relation.FieldsValue['f10'] == expression and all(side.FieldsValue['fa0'] is relation for side in sides)
                    and [handle.ClassValue.NameValue for handle in handles] == ['moFeatureDimHandle_c', 'moSkDimHandleValG2_c']
                    and len({id(handle.FieldsValue['f58']) for handle in handles}) == 2
                    and all(handle.FieldsValue['f58'].FieldsValue['owner'] is config.RootValue for handle in handles),
                    'the equation wrappers must link the actual distinct local owner components')
        rows[lane] = {'map_counters': [config.MapValue.CounterValue, resolved.MapValue.CounterValue],
                      'relation_count': len(relations), 'self_file': path,
                      'streams': {key: {'sha256': digest(value), 'bytes': len(value)} for key, value in a.streams.items()}}
    plain, reference = streams['Plain'], streams['Reference']
    require(plain.keys() == reference.keys() and {key for key in plain if plain[key] != reference[key]} == set(LAYOUT),
            'the matched pair may differ only in the actual linked equation streams')
    return rows


def freeze(name, revision):
    import subprocess

    host_paths()
    import BuildWidthDepthPart as builder
    from InspectSdkBlindPart import tree_prediction
    from InspectSdkCornerOwners import TOOLS

    old = json.loads(checked(EARLIER / 'Job.json', EARLIER_SHA))
    source = json.loads(checked(SOURCE, SOURCE_SHA))
    locator = final_locator(name)
    root = MANAGED / name
    require(root.resolve() == root and not root.exists(), 'packet directory is already used or redirected')
    source['document']['metadata']['name'] = locator.stem
    source['settings']['output']['path_name'] = str(locator)
    doc = builder.FromData(source['document'])
    plan = builder.ProjectRectDims(doc)
    sketch, = doc.sketches
    boss, = doc.feature_timeline
    width, height, depth = plan.WidthValue, plan.HeightValue, plan.DepthValue
    divisor = source['equation']['divisor']
    values = old['cases']['Alpha']['case']
    wanted_width = values['edit_width_mm'] / 1000
    require((width, height, depth) == tuple(values[key] / 1000 for key in ('width_mm', 'height_mm', 'depth_mm'))
            and 0 < width < wanted_width and divisor == values['divisor'] == 2 and depth == width / divisor,
            'unmatched neutral width-to-depth geometry')
    names = [f'{name}@{sketch.name}' for name in plan.SketchDriverNames] + [f'{plan.DepthName}@{boss.name}']
    require(names == [f'D1@{sketch.name}', f'D2@{sketch.name}', f'D1@{boss.name}'], 'unexpected declared driver owners')
    expression = f'"{names[2]}" = "{names[0]}" / {divisor}'
    case = {'profile': sketch.name, 'feature': boss.name, 'parameter_names': names, 'density_kg_m3': source['settings']['density_kg_m3'],
            'dimensions_m': dict(zip(names, (width, height, depth), strict=True)), 'vertices_m': plan.VerticesValue,
            'origin': source['settings']['system']['origin_name'], 'configuration_name': doc.configurations[0].name,
            'support': doc.support_planes[0].name, 'initial': geometry(width, height, depth)}
    edits = {lane: {'parameter': names[0], 'value_m': wanted_width,
                    'expected_dimensions_m': dict(zip(names, (wanted_width, height, after), strict=True)),
                    'geometry': geometry(wanted_width, height, after)}
             for lane, after in (('Plain', depth), ('Reference', wanted_width / divisor))}
    tree = tree_prediction(source, {'intent': {'profile': sketch.name, 'feature': boss.name, 'resolved_roots': 19}})
    data = canonical(source)
    bins, builds = {}, {}
    action = 'import runpy,sys; runpy.run_path(sys.argv[1])["write_variant"](sys.argv[2])'
    for lane in edits:
        command = [sys.executable, '-I', '-B', '-c', action, str(HERE), lane]
        attempts = [subprocess.run(command, input=data, capture_output=True, cwd=REPO) for _ in range(2)]
        for item in attempts:
            if item.returncode:
                raise RuntimeError(item.stderr.decode(errors='replace'))
        a, b = attempts
        require(a.stdout == b.stdout and a.stderr == b.stderr, 'independent guarded construction changed')
        proof = json.loads(a.stderr)
        require(proof['runtime_input_file_reads'] == 0 and proof['sha256'] == digest(a.stdout)
                and proof['expression'] == (expression if lane == 'Reference' else None), 'guarded write receipt is inconsistent')
        bins[lane], builds[lane] = a.stdout, proof
    archive = stream_proof(bins, locator, expression)
    require(all(archive[lane]['map_counters'] == [proof['config_map_final'], proof['resolved_map_final']]
                for lane, proof in builds.items()), 'generated and re-read object-map counters differ')
    control = old['cases']['ControlBefore']
    require(control == old['cases']['ControlAfter'] and control['path'] == CONTROL_NAME and control['case']['id'] == 'D02',
            'the exact disclosed D02 bracket is required')
    tools = set(TOOLS) | {'AuthorEquationSources01.py', 'ObserveWidthDepthPart.py'}
    root.mkdir(mode=0o700)
    for directory in ('Tools', 'Frozen', 'Inspection'):
        (root / directory).mkdir()
    inputs = {'Neutral.json': data, 'ApiMetadata01.json': checked(EARLIER / 'ApiMetadata01.json', METADATA_SHA),
              CONTROL_NAME: checked(EARLIER / CONTROL_NAME, CONTROL_SHA)}
    for filename in tools:
        inputs[f'Tools/{filename}'] = (HERE.parent.parent / filename).read_bytes() if filename != 'ObserveWidthDepthPart.py' else HERE.with_name(filename).read_bytes()
    inputs[f'Tools/{HERE.name}'] = HERE.read_bytes()
    inputs.update({f'Frozen/{lane}.SLDPRT': blob for lane, blob in bins.items()})
    inputs['Build.json'] = canonical({'revision': revision, 'source_sha256': SOURCE_SHA,
        'preparer_sha256': digest(HERE.read_bytes()), 'guarded_processes': 4, 'runtime_input_file_reads': 0,
        'native_processes_started': 0, 'heldout_inputs_read': 0, 'encoded_locator': str(locator),
        'equation_delta_streams': LAYOUT, 'writer_receipts': builds, 'archive': archive,
        'initial_prediction': case['initial'], 'edited_predictions': edits})
    hashes = {relative: publish(root / relative, blob) for relative, blob in sorted(inputs.items())}
    job = {'schema': SCHEMA, 'revision': revision, 'files_sha256': hashes, 'encoded_locator': str(locator),
           'control': control, 'guest_runtime': old['guest_runtime'], 'guest_root': unc(root), 'expression': expression,
           'heldout_inputs_read': 0, 'phases': PHASES, 'case': case, 'edits': edits, 'tree': tree}
    pin = publish(root / 'Trial.json', canonical(job))
    commands = {'Verify': ('verify',), **{phase: ('observe', phase) for phase in PHASES}, 'Summary': ('summary',)}
    prefix = ['prlctl', 'exec', 'Windows 11', '--current-user', old['guest_runtime']['executable'],
              '-B', unc(root / 'Tools' / HERE.name)]
    recipe = publish(root / 'Recipe.json', canonical({'trial_sha256': pin, 'ordered_steps': list(commands),
        'max_native_launches': len(PHASES), 'trailing_control_after_failure_if_idle': True,
        'argv': {key: [*prefix, *command, unc(root / 'Trial.json'), pin] for key, command in commands.items()}}))
    print(json.dumps({'packet': str(root), 'trial_sha256': pin, 'recipe_sha256': recipe, 'build_sha256': hashes['Build.json'],
                      'files': {lane: proof['sha256'] for lane, proof in builds.items()}, 'native_processes_started': 0}, sort_keys=True))


def load_trial(packet, pin):
    import AuthorEquationSources01 as equations

    root = packet.resolve(strict=True).parent
    trial = json.loads(checked(packet, pin))
    exact = final_locator(root.name)
    require(packet.name == 'Trial.json' and HERE.parent == root / 'Tools' and Path(trial['guest_root']).resolve() == root
            and trial['schema'] == SCHEMA and trial['encoded_locator'] == str(exact) and trial['phases'] == list(PHASES)
            and trial['heldout_inputs_read'] == 0 and trial['files_sha256'][CONTROL_NAME] == CONTROL_SHA
            and trial['files_sha256']['ApiMetadata01.json'] == METADATA_SHA, 'the exact matched disclosed packet is required')
    for relative, value in trial['files_sha256'].items():
        path = root / relative
        require(path.resolve() == path and path.is_relative_to(root), 'unexpected packet file path')
        checked(path, value)
    equations.guest_only(trial)
    return root, trial, Path(exact)


def prior_phase(root, pin, role):
    path = root / 'Inspection' / role / 'TrialReceipt.json'
    if not path.is_file():
        return None
    row = json.loads(path.read_bytes())
    require(row['trial_sha256'] == pin and row['role'] == role, 'a native phase belongs to a different trial')
    checked(path.with_name('Record.json'), row['record_sha256'])
    return row['result']


def stage_part(root, job, exact, lane):
    import Swapp

    expected = job['files_sha256'][f'Frozen/{lane}.SLDPRT']
    payload = checked(root / 'Frozen' / f'{lane}.SLDPRT', expected)
    require(exact.resolve() == exact and not exact.is_symlink(), 'C: locator is redirected')
    Swapp.sweep()
    if lane == 'Plain':
        exact.parent.mkdir(parents=True, exist_ok=True)
        publish(exact, payload)
    else:
        plain = job['files_sha256']['Frozen/Plain.SLDPRT']
        checked(exact, plain)
        pending = exact.with_suffix('.SLDPRT.pending')
        publish(pending, payload)
        checked(exact, plain)
        pending.replace(exact)
    checked(exact, expected)
    return {'staged_sha256': expected, 'path': str(exact), 'cad_processes_started_by_staging': 0}


def candidate_phase(root, job, role, source, expected, lane, prior):
    from types import SimpleNamespace
    import AuthorEquationSources01 as equations
    import InspectSdkCornerOwners as corner
    import SdkCornerOwnerGraph as owners

    base_snapshot = corner.snapshot
    base_verify = corner.verify_state
    metadata = json.loads((root / 'ApiMetadata01.json').read_bytes())['interfaces']['IEquationMgr']['members']
    related = lane == 'Reference'
    depth_name = job['case']['parameter_names'][2]

    def snapshot(author, case):
        state = base_snapshot(author, case)
        state['opened_path'] = str(author.get(author.model, 'GetPathName'))
        require(Path(state['opened_path']).samefile(source), 'the original native locator was not opened')
        dimension = author.get(author.model, 'Parameter', depth_name)
        state['depth_driven_state'] = int(author.get(dimension, 'DrivenState'))
        state['depth_read_only'] = bool(author.get(dimension, 'ReadOnly'))
        require(state['depth_driven_state'] == (1 if related else 2) and not state['depth_read_only'],
                'the actual leaf depth changed its declared equation ownership')
        manager = author.typed(author.get(author.model, 'GetEquationMgr'), 'IEquationMgr')
        bound = SimpleNamespace(metadata=metadata, rec=author.rec)
        value = lambda name, kind=2, *args: equations.EquationAuthor.eq(bound, manager, name, kind, *args)
        state['equations'] = []
        require(value('GetCount', 1) == int(related) and not value('LinkToFile') and not value('FilePath'),
                'the actual equation manager does not own the declared local rows')
        if related:
            equation = str(value('Equation', 2, 0))
            disabled, global_row = bool(value('Disabled', 2, 0)), bool(value('GlobalVariable', 2, 0))
            require(''.join(equation.split()) == ''.join(job['expression'].split()) and not disabled and not global_row,
                    'the native reference equation row or operand owners differ')
            state['equations'].append({'text': equation, 'disabled': disabled, 'global_variable': global_row})
        return state

    def verify(author, state, case, tree, dims, *, roles, rebuilt):
        require([[row['name'], row['type'], row['parent']] for row in state['tree']] == tree
                and not any(row['suppressed'] or row['error'] or row['warning'] for row in state['tree']),
                'the complete native tree differs or has diagnostics')
        require(state['configuration'] == case['configuration_name'] and case['support'] in state['sketch_parents']
                and case['profile'] in state['boss_parents'] and case['support'] in state['boss_parents']
                and state['whats_wrong'] == 0 and state['body_count'] == 1
                and state['constraint_status'] in ((3,) if rebuilt else (1, 3)), 'native support, body or rebuild state differs')
        selected = state['selected_origin']
        require(selected['same_origin_raw'] == selected['same_self_raw'] == selected['owner_same_self_raw'] == 1
                and selected['owner_same_profile_raw'] == 0 and selected['owner_same_origin_raw'] == 1
                and not selected['owner_null'] and all(owners.close(value, 0.) for value in selected['position_m']),
                'the native origin owner differs')
        for name in case['parameter_names']:
            value = state['dimensions'][name]
            require(value['short_name'] == name and value['driving'] is (not related or name != depth_name),
                    'native parameter ownership or driving role differs')
            author.rec.close_number(name, value['value_m'], dims[name])
        width, height, depth = (dims[name] for name in case['parameter_names'])
        for actual, expected_point in zip(owners.ordered_points(state['geometry'], roles),
                ((0., 0.), (width, 0.), (width, height), (0., height)), strict=True):
            for coordinate, target in zip(actual, expected_point, strict=True):
                author.rec.close_number('origin preserved rectangle corner', coordinate, target)
        predicted = geometry(width, height, depth)
        mass = state['mass']
        for field, key in (('volume', 'volume_m3'), ('area', 'area_m2')):
            author.rec.close_number('native rectangle ' + field, mass[field], predicted[key], absolute=1e-16)
        author.rec.close_number('native rectangle mass', mass['mass'], predicted['volume_m3'] * case['density_kg_m3'], absolute=1e-16)
        for actual, target in zip(mass['com'], predicted['com_m'], strict=True):
            author.rec.close_number('native rectangle centroid', actual, target)
        owners.verify_relations(state['relations'], roles, case['parameter_names'], dims)
        return json.loads(canonical(owners.relation_signature(state['relations'])))

    corner.snapshot, corner.verify_state = snapshot, verify
    try:
        return corner.phase(root / 'Inspection', role, source, expected, job['case'], job['tree'], job['edits'][lane], prior=prior)
    finally:
        corner.snapshot, corner.verify_state = base_snapshot, base_verify


def run_phase(root, job, pin, exact, role):
    import ObserveWidthDepthPart as legacy

    require(role in PHASES, 'undeclared native phase')
    if role != 'ControlAfter':
        ready = root / 'Inspection/Verification.json'
        require(ready.is_file() and json.loads(ready.read_bytes())['trial_sha256'] == pin, 'the exact guest preflight must pass')
    phase = root / 'Inspection' / role
    require(not phase.exists(), 'native phase already used')
    custody = None
    if role.startswith('Control'):
        result = legacy.inspect(root / 'Trial.json', {'cases': {role: job['control']}}, role)
    else:
        index = PHASES.index(role)
        previous = prior_phase(root, pin, PHASES[index - 1])
        require(previous and previous['passed'], 'the preceding matched native phase must pass')
        lane = 'Plain' if role.startswith('Plain') else 'Reference'
        staged_sha = job['files_sha256'][f'Frozen/{lane}.SLDPRT']
        if role.endswith('Reopen'):
            source = root / 'Inspection' / PHASES[index - 1] / 'Edited.SLDPRT'
            expected = previous['derivative_sha256']
            checked(exact, staged_sha)
        else:
            custody = stage_part(root, job, exact, lane)
            source, expected, previous = exact, staged_sha, None
        result = candidate_phase(root, job, role, source, expected, lane, previous)
        checked(exact, staged_sha)
    record = phase / 'Record.json'
    publish(phase / 'TrialReceipt.json', canonical({'trial_sha256': pin, 'role': role, 'record_sha256': digest(record.read_bytes()),
                                                    'staging': custody, 'result': result}))
    return result['passed']


def summary(root, job, pin, exact):
    phases = {phase: prior_phase(root, pin, phase) for phase in PHASES}
    before, after = (phases[phase] for phase in ('ControlBefore', 'ControlAfter'))
    controls = bool(before and after and before['passed'] and after['passed']
                    and before['original'] == after['original'])
    births = [row['oracle_identity']['process_creation_filetime'] for row in phases.values() if row and 'oracle_identity' in row]
    complete = all(row and row['passed'] for row in phases.values())
    same_locators = False
    if complete:
        plain, reference = (phases[role]['states']['Initial'] for role in ('PlainEdit', 'ReferenceEdit'))
        same_locators = all(Path(row['opened_path']).samefile(exact) for row in (plain, reference))
        checked(exact, job['files_sha256']['Frozen/Reference.SLDPRT'])
    passed = bool(controls and complete and same_locators and len(births) == len(PHASES)
                  and all(a < b for a, b in zip(births, births[1:])))
    publish(root / 'Result.json', canonical({'schema': SCHEMA, 'trial_sha256': pin, 'passed': passed,
        'controls_healthy': controls, 'same_encoded_native_locator': same_locators, 'distinct_native_processes': len(set(births)),
        'heldout_acceptance': False, 'phases': phases}))
    return passed


def main():
    parser = argparse.ArgumentParser(description='Freeze or observe the disclosed same-locator width-depth trial')
    sub = parser.add_subparsers(dest='command', required=True)
    host = sub.add_parser('prepare')
    host.add_argument('name')
    host.add_argument('revision')
    for name in ('verify', 'observe', 'summary'):
        guest = sub.add_parser(name)
        if name == 'observe':
            guest.add_argument('role', choices=PHASES)
        guest.add_argument('packet', type=Path)
        guest.add_argument('sha256')
    args = parser.parse_args()
    if args.command == 'prepare':
        require(os.name == 'posix', 'prepare on the host only')
        return prepare(args.name, args.revision)
    require(os.name == 'nt', 'native trial phases belong to the root-owned Windows guest')
    root, job, exact = load_trial(args.packet, args.sha256)
    if args.command == 'verify':
        require(not exact.exists() and not exact.is_symlink() and exact.resolve() == exact, 'the exact authored C: locator must be unused')
        publish(root / 'Inspection/Verification.json', canonical({'trial_sha256': args.sha256, 'cad_processes_started': 0,
                                                                  'encoded_locator': str(exact)}))
        passed = True
    elif args.command == 'observe':
        passed = run_phase(root, job, args.sha256, exact, args.role)
    else:
        passed = summary(root, job, args.sha256, exact)
    print(json.dumps({'passed': passed, 'mode': args.command, 'role': getattr(args, 'role', None)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
