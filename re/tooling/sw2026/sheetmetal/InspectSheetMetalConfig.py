from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

LEGACY = 'moPerBodySheetMetalData_c'
PAIR = 'moSMAndFPFeatIdPair'
CUT_LIST = 'moCutListFolder_c'
CUT_LIST_SORT = 'moCutListSortOptions_c'
MAX_PART = 128 * 1024 * 1024
REFERENCE = 'b87f3b12b72874f4289b627d56e3740da2ab725b'
FIELDS = ('f08', 'f10', 'f18', 'f20')
INHERITED = ('f18', 'f78', 'f258', 'f2f0')


def describe(value):
    if value is None:
        return None
    slot = getattr(value, 'index', None)
    return dict(class_name=getattr(value, 'cls', type(value).__name__),
                schema=getattr(value, 'schema', None), slot=slot,
                start=getattr(value, 'pos', None), end=getattr(value, 'end', None))


def image(data):
    return sha256(data).hexdigest()


def map_members(reader):
    return {row.IndexValue: row.EntryValue for row in reader.map_state().state.EntriesValue}


def inspect(archive, registry, name, linked=False):
    from Core import ArchiveError
    from Dsl import i32, obj
    from Schema import Fn
    from defs.ConfigPart import load_config_compat, store_config_state_compat
    from convert.adapters.solidworks.Container.Archive import ContainerMo

    version = ContainerMo(archive.streams)
    if version != 19000:
        raise ArchiveError('research check is scoped to generation 19000')
    data = archive.require(name)
    rules = registry()
    observations = []
    frames = []

    def begin(reader, fields, owner):
        if owner.schema != 1:
            raise ArchiveError('legacy per-body wire descriptor is outside the schema-one proposal')
        frames.append((reader.p, map_members(reader)))

    def end(reader, values, owner):
        start, incoming = frames.pop()
        outgoing = map_members(reader)
        preserved = all(outgoing.get(slot) is value for slot, value in incoming.items())
        if not preserved:
            raise ArchiveError('the per-body candidate changed existing map member identities')
        links = {}
        for field in FIELDS:
            target = values[field]
            item = describe(target)
            if item is not None:
                slot = item['slot']
                item['map_disposition'] = ('unmapped' if slot is None else
                                           'inherited' if incoming.get(slot) is target else 'allocated')
            links[field] = item
        observations.append(dict(body_start=start, body_end=reader.p,
                                 owner=describe(owner), links=links,
                                 active=values['f28'], old_atom_id=values['f2c'],
                                 incoming_identities_preserved=preserved,
                                 allocated_slots=sorted(outgoing.keys()-incoming.keys())))

    def store_noop(writer, fields, owner):
        return None

    rules.provisional(LEGACY, [Fn(begin, store_noop), *(obj(field) for field in FIELDS),
                              i32('f28'), i32('f2c'), Fn(end, store_noop)])
    document, reader = load_config_compat(data, rules, version, archive=archive, name=name)
    if document.tail:
        raise ArchiveError('configuration retains unconsumed bytes')
    part = document.roots[0]
    master = part.get('f1018')
    modern = part.get('f16e8')
    children = [] if master is None else [row['o'] for row in master['f358']]
    count = 0 if master is None else master['n370']
    if master is not None and (master.cls != 'moSheetMetalMaster_c' or master.index is not None):
        raise ArchiveError('f1018 is not the directly owned tagless master')
    if count != len(children):
        raise ArchiveError('master count and child roster differ')
    slots = {node.index for node in children if node is not None}
    if slots != {row['owner']['slot'] for row in observations} or None in slots:
        raise ArchiveError('decoded legacy owners do not match the master child slots')
    generated, written_map = store_config_state_compat(document, rules, version)
    if data != generated or reader.count != written_map.count:
        raise ArchiveError('configuration or allocation count differs after symbolic re-emission')
    source_map = map_members(reader)
    store_map = {entry.IndexValue: entry.EntryValue for entry in written_map.state.EntriesValue}
    if source_map.keys() != store_map.keys():
        raise ArchiveError('store changed the class or object slot roster')
    for slot, value in source_map.items():
        stored = store_map[slot]
        if stored is not value and stored != value:
            raise ArchiveError('store changed the typed owner of a map slot')
    result = dict(config_sha256=image(data), config_bytes=len(data), config_version=version,
                fully_consumed=True, exact_replay=True, exact_slot_roster=True, research_only=True,
                master_present=master is not None,
                master_inherited_links={} if master is None else {key: describe(master.get(key)) for key in INHERITED},
                master_legacy_count=count, master_children=[describe(node) for node in children],
                positive_populated_observed=bool(slots),
                later_body_count=None if modern is None else len(modern),
                legacy_wire_observations=observations)


    if linked:
        result['linked_streams'] = inspect_linked(archive, rules, name, version, reader)
    return result


def record_boundary(observations):
    from Core import ArchiveError
    from Schema import Fn

    frames = []

    def begin(reader, fields, owner):
        if owner.schema != 1:
            raise ArchiveError(f'{owner.cls} is outside the schema-one proposal')
        frames.append((reader.p, reader.map_state(), dict(reader.ctx)))

    def end(reader, fields, owner):
        start, seed, context = frames.pop()
        observations.append((start, reader.p, seed, context, reader.map_state(), fields, owner))

    def noop(*args):
        return None

    return Fn(begin, noop), Fn(end, noop)


def cut_list_candidate(rules, observations):
    from Dsl import base, emb, f64, i32, u8
    from defs.ResolvedCore import concept_vt, obarray, xo

    begin, end = record_boundary(observations)
    concept_vt(CUT_LIST)
    rules.provisional(CUT_LIST_SORT, [
        begin, i32('f08'), obarray('f10'), end,
    ])
    rules.provisional('moAtomBodyFolder_c', [
        base('moFolder_c'), i32('f37c'), i32('f380'),
        xo('f388', 'moMaterialFolder_c'), xo('f3d8', 'moCutListSortOptions_c'),
    ])
    rules.provisional('moSubAtomFolder_c', [
        base('moAtomBodyFolder_c'), xo('f3e0', 'suObList'), i32('f3e8'),
        xo('f3f0', 'moFeatureRefWrapper_c'), i32('f3fc'), i32('f3ec'),
    ])
    rules.provisional('moSubWeldFolder_c', [
        base('moSubAtomFolder_c'), emb('f450', 'moCustomPropertyList'),
    ])
    rules.provisional(CUT_LIST, [
        begin, base('moSubWeldFolder_c'), xo('f498', 'moCompFeature_c'),
        i32('f4a4'), i32('f4a0'), u8('f48c'), xo('f468', 'moPlaneRef_w'),
        f64('f470'), f64('f478'), f64('f480'), i32('f4b0'), i32('f4b4'), end,
    ])


def template_candidate(rules, observations):
    from Core import ArchiveError
    from Dsl import base, count, cstr, emb, f64, i32, u8, u32
    from Schema import Fn, If
    from defs.ResolvedCore import concept_vt, xo

    def require_empty_array_counts(archive, fields, owner):
        if any(fields.get(key, 0) != 0 for key in ('n00', 'n04', 'n08', 'n30', 'n34')):
            raise ArchiveError('nonempty sheet-metal bend-allowance arrays remain unresolved')

    def contextual(fields, archive):
        # sldmodu SP04.1 moModel_c::loadResolvedFeatures copies CMgr.f658 to helper+0x890.
        return bool(archive.ctx['model_is_part'] and archive.ctx['cmgr_f658'])

    begin, end = record_boundary(observations)
    concept_vt('moTemplateSheetMetal_c')
    concept_vt('moSheetMetal_c')
    rules.provisional('moTemplateSheetMetal_c', [begin, base('moSheetMetal_c'), end])
    rules.provisional('moSheetMetalCommon_c', [
        base('moBodyFeature_c'), emb('f808', 'sm.common808'), i32('f848'), i32('f84c'), i32('f850'),
    ])
    require_empty = Fn(require_empty_array_counts, require_empty_array_counts)
    rules.provisional('sm.bend_allow', [
        u32('n00'), u32('n04'), u32('n08'), require_empty,
        cstr('f38'), i32('f40'), u8('f00'), xo('f08', 'moDisplayDim_c'), xo('f10', 'moDisplayDistanceDim_c'),
        i32('n30'), i32('n34'), require_empty, cstr('f110'), cstr('f100'), cstr('f0f8'), cstr('f108'),
        xo('f128', 'moSMParamsFromMat_c'), emb('f0d0', 'su_CStringArray'),
        emb('f0a8', 'su_CStringArray'), emb('f080', 'su_CStringArray'),
    ])
    rules.provisional('sm.common808', [
        xo('f10', 'moDisplayDim_c'), xo('f18', 'moCompFeature_c'), u8('has_bend_allow'),
        If(lambda scope, ar: bool(scope['has_bend_allow']), [emb('bend_allow', 'sm.bend_allow')]),
        i32('f00'), i32('f04'), i32('temp0'), i32('temp1'),
        If(contextual, [xo('f20', 'moCompSheetmetalFeat_c')]),
    ])
    rules.provisional('moSheetMetal_c', [
        base('moSheetMetalCommon_c'), f64('f8f8'), xo('f900', 'moDisplayDim_c'), i32('f908'),
        xo('f910', 'moDisplayDim_c'), xo('f918', 'moFixedFaceInFlat_c'), i32('f938'),
        i32('f958'), cstr('f960'), i32('f968'), i32('f96c'), i32('f970'), i32('f974'),
        If(contextual, [i32('f980'), i32('f97c'), i32('f984')]),
    ])


def base_flange_candidate(rules, observations):
    from Core import ArchiveError
    from Dsl import base, emb, f64, i32, u8, u32
    from Schema import Fn, If, Rep
    from defs.ResolvedCore import concept_vt, obarray, xo

    def require_termination_mode(archive, fields, owner):
        if fields['f900'] not in (0, 1, 2):
            raise ArchiveError('base-flange termination lane mode remains unresolved')

    def termination_lane(mode, ending, length, wrapper, reference, dimension, offset):
        return If(lambda scope, ar: scope['f900'] in (0, mode), [
            i32(ending),
            If(lambda scope, ar: scope[ending] in (0, 6), [f64(length)]),
            If(lambda scope, ar: scope[ending] == 3, [xo(reference)]),
            If(lambda scope, ar: scope[ending] == 1 and scope['has_control'], [xo(wrapper, 'moRefWrapper_c')]),
            xo(dimension, 'moDisplayDim_c'), f64(offset),
        ])

    begin, end = record_boundary(observations)
    concept_vt('moSMBaseFlange_c')
    rules.provisional('moCompSheetmetalFeat_c', [base('moCompSMDataObjFeat_c')])
    rules.provisional('moCompSMDataObjFeat_c', [base('moCompRef_c'), i32('fe8')])
    rules.provisional('moSheetMetalBendGroup_c', [
        base('moSheetMetalCommon_c'), obarray('f860'), u32('f880'),
    ])
    rules.provisional('sm.base_group', [
        i32('n'), If(lambda scope, ar: scope['n'] > 0, [
            xo('sketch', 'sgSketch'), Rep('n', 'handles', [xo('o', 'sgEntHandle')]),
        ]),
    ])
    rules.provisional('moSMBaseFlange_c', [
        begin, base('moSheetMetalBendGroup_c'), xo('f890', 'moProfileFeature_c'), i32('f8a0'),
        i32('f8d0'), i32('f900'), Fn(require_termination_mode, require_termination_mode),
        u8('has_control'), i32('f888'),
        termination_lane(1, 'f8d8', 'f8c0', 'f8e0', 'ref0', 'fA10', 'f8b0'),
        termination_lane(2, 'f8dc', 'f8c8', 'f8e8', 'ref1', 'fA18', 'f8b8'),
        emb('f960', 'sm.base_group'), emb('f980', 'sm.base_group'),
        emb('f9c0', 'sm.base_group'), emb('f9e0', 'sm.base_group'),
        i32('f8d4'), xo('fA20', 'moFromEndSpec_c'), end,
    ])


def flat_pattern_candidate(rules, observations):
    from Core import ArchiveError
    from Dsl import base, count, cstr, emb, f64, i32
    from Schema import Fn, If, Rep
    from defs.ResolvedCore import concept_vt, obarray, xo

    def require_absent_flat_body(archive, fields, owner):
        if fields['has_flat_parasolid']:
            raise ArchiveError('embedded flat-pattern body remains unresolved')

    def require_supported_pair_count(archive, fields, owner):
        if not 0 <= fields['n_pairs'] <= 4096:
            raise ArchiveError('invalid signed flat-pattern pair count')

    def require_absent_fold_properties(archive, fields, owner):
        if fields['n_properties']:
            raise ArchiveError('nonempty fold sketch properties remain unresolved')

    def require_absent_fold_bytes(archive, fields, owner):
        if fields['n_fold_bytes']:
            raise ArchiveError('nonempty fold sketch byte array remains unresolved')

    begin, end = record_boundary(observations)
    concept_vt('moTemplateFlatPattern_c')
    concept_vt('moFlatPattern_c')
    concept_vt('moFoldUpDownSketchFolder_c')
    rules.provisional('moFoldUpDownSketchFolder_c', [
        begin, base('moFolder_c'), xo('f570', 'moFoldUpDownSketchXformData_c'),
        xo('f578', 'moFoldUpDownFeatXformData_c'), end,
    ])
    rules.provisional('moFoldUpDownSketchXformData_c', [
        begin, emb('f58', 'rf.suObList'), emb('fA0', 'rf.suObList'), i32('n_transforms'),
        Rep('n_transforms', 'transforms', [emb('transform', 'mgXform_c.restore')]),
        i32('n_properties'), Fn(require_absent_fold_properties, require_absent_fold_properties),
        count('n_fold_bytes'), Fn(require_absent_fold_bytes, require_absent_fold_bytes),
        emb('f10', 'rf.suObList'), end,
    ])
    rules.provisional('moFoldUpDownFeatXformData_c', [
        begin, emb('f58', 'rf.suObList'), i32('n_transforms'),
        Rep('n_transforms', 'transforms', [emb('transform', 'mgXform_c.restore')]),
        emb('f10', 'rf.suObList'), end,
    ])
    rules.provisional('moFlatPatBoundBox_c', [emb('f10', 'moBoundBoxData_c')])
    rules.provisional('moBoundBoxData_c', [
        *(f64(key) for key in ('x0', 'y0', 'z0', 'x1', 'y1', 'z1', 'f28', 'f30', 'f38', 'f40', 'f80', 'f88')),
        i32('f90'), f64('f48'),
    ])
    rules.provisional('moTemplateFlatPattern_c', [begin, base('moFlatPattern_c'), end])
    rules.provisional('moFlatPattern_c', [
        base('moSheetMetalBendGroup_c'), obarray('f950'),
        *(xo(key, 'moCompBEntRef_c') for key in ('f900', 'f908', 'f910')),
        i32('f9b8'), i32('f9bc'), obarray('f970'),
        *(i32(key) for key in ('f9c4', 'f9c8', 'f9f8', 'f9cc')),
        f64('f9d0'), i32('f9e8'), f64('f9e0'),
        *(i32(key) for key in ('f9ec', 'f9d8', 'f9f4', 'fab0')),
        xo('fA00', 'moCompFeature_c'), xo('fA40', 'suObList'), i32('has_flat_parasolid'),
        Fn(require_absent_flat_body, require_absent_flat_body), i32('f990'), obarray('f998'),
        xo('f928', 'moCompFace_c'), i32('f930'),
        If(lambda scope, ar: bool(scope['f930']), [cstr('f938')]),
        xo('f918', 'moRefWrapper_c'), emb('f920', 'moFlatPatBoundBox_c'),
        *(i32(key) for key in ('fA30', 'fA34', 'fA38', 'fA3c')),
        If(lambda scope, ar: bool(ar.ctx['model_is_part'] and ar.ctx['cmgr_f658']), [i32('fA88')]),
        i32('n_pairs'), Fn(require_supported_pair_count, require_supported_pair_count),
        Rep('n_pairs', 'pairs', [i32('a'), i32('b')]),
    ])
    rules.provisional('moPerBodySheetMetalDataNew_c', [
        begin, emb('f30', 'su_CDWordArray'), i32('f08'), i32('f0c'), xo('f10', 'moSheetMetal_c'),
        xo('f18', 'moFlatPattern_c'), i32('f28'), i32('f20'), i32('f24'), i32('f50'), end,
    ])


def replay_boundaries(resolved, rules, version, observations):
    from Core import ArchiveError, Store

    def roster(snapshot):
        return {entry.IndexValue: entry.EntryValue for entry in snapshot.state.EntriesValue}

    result = []
    for start, end, seed, context, read_state, fields, owner in observations:
        writer = Store(seed.count, rules, version, context, seed=seed)
        rules.run_store(owner.cls, writer, fields, owner)
        write_state = writer.map_state()
        inherited, incoming, outgoing = roster(seed), roster(read_state), roster(write_state)
        if (resolved[start:end] != bytes(writer.out) or read_state.count != write_state.count or
                incoming.keys() != outgoing.keys() or
                any(incoming.get(slot) is not value or outgoing.get(slot) is not value
                    for slot, value in inherited.items()) or
                any(outgoing.get(slot) is not value and outgoing.get(slot) != value
                    for slot, value in incoming.items())):
            raise ArchiveError(f'{owner.cls} candidate did not reproduce its bytes and map identities')
        row = dict(owner=describe(owner), payload_start=start, payload_end=end,
                   payload_sha256=image(resolved[start:end]), exact_replay=True,
                   inherited_count=seed.count, resulting_count=read_state.count)
        if owner.cls == 'moPerBodySheetMetalDataNew_c':
            row['fields'] = {key: fields[key] for key in ('f08', 'f0c', 'f28', 'f20', 'f24', 'f50')}
            row['fields']['f30'] = [item['v'] for item in fields['f30']['items']]
            row['links'] = {key: describe(fields[key]) for key in ('f10', 'f18')}
        result.append(row)
    return result


def inspect_linked(archive, rules, name, version, configuration):
    from CmgrBridge import load_cmgr, store_cmgr
    from Core import ArchiveError
    from Dsl import i32
    from Schema import Fn
    from defs.ResolvedCore import load_resolved, store_resolved_state

    def check_pair_schema(reader, fields, owner):
        if owner.schema != 1:
            raise ArchiveError('sheet-metal manager pair is outside the schema-one proposal')

    # SP04.1 sldmodu.dll Serialize at RVA 0x10e8b40 has three signed long operations.
    # The native meanings of the three values need independently measured identity controls.
    rules.provisional(PAIR, [Fn(check_pair_schema, lambda *_: None), i32('f08'), i32('f0c'), i32('f10')])
    manager_bytes = archive.require('Contents/CMgr')
    manager, manager_reader = load_cmgr(manager_bytes, rules, version, archive=archive, name='Contents/CMgr')
    if manager.tail or manager_reader.left() or store_cmgr(manager, rules, version) != manager_bytes:
        raise ArchiveError('linked check requires complete identical CMgr replay')
    roots = [root for root in manager.roots if root.cls == 'moConfigurationMgr_c']
    if len(roots) != 1:
        raise ArchiveError('linked check requires one typed configuration manager')
    result = {
        'cmgr': dict(bytes=len(manager_bytes), sha256=image(manager_bytes), exact_replay=True,
                     map_count=manager_reader.count, mode=roots[0].get('f658'), pairs=[]),
    }
    for row in roots[0].get('f660') or ():
        pair = row['o']
        if pair is None or pair.cls != PAIR or pair.schema != 1:
            raise ArchiveError('linked check encountered an unresolved sheet-metal manager pair')
        result['cmgr']['pairs'].append(dict(key=row['key'], owner=describe(pair), fields=dict(pair.f)))

    resolved_name = name + '-ResolvedFeatures'
    resolved = archive.require(resolved_name)
    resolved_report = dict(bytes=len(resolved), sha256=image(resolved),
                           inherited_config_count=configuration.count,
                           recorded_prefix=int.from_bytes(resolved[:4], 'little'),
                           exact_replay=False)
    result['resolved'] = resolved_report
    if len(resolved) < 4 or resolved_report['recorded_prefix'] != configuration.count:
        raise ArchiveError('resolved archive prefix differs from the measured configuration map')
    seed = configuration.map_state()
    cut_lists, templates, base_flanges, flat_patterns = [], [], [], []
    cut_list_candidate(rules, cut_lists)
    template_candidate(rules, templates)
    base_flange_candidate(rules, base_flanges)
    flat_pattern_candidate(rules, flat_patterns)
    with rules.track_usage('load', resolved_name, role='linked', sources=archive.streams) as usage:
        try:
            document, reader = load_resolved(resolved, rules, version, archive=archive, name=resolved_name, seed=seed)
            if document.tail or reader.left():
                raise ArchiveError('resolved archive retains unconsumed bytes')
            generated, written = store_resolved_state(document, rules, version, seed=seed)
            if resolved != generated or reader.count != written.count:
                raise ArchiveError('resolved archive bytes or map allocation count changed')
            inherited = map_members(configuration)
            read_map = map_members(reader)
            written_map = {entry.IndexValue: entry.EntryValue for entry in written.state.EntriesValue}
            if any(read_map.get(slot) is not value or written_map.get(slot) is not value
                   for slot, value in inherited.items()):
                raise ArchiveError('resolved archive changed an inherited configuration map identity')
            if read_map.keys() != written_map.keys() or any(
                written_map[slot] is not value and written_map[slot] != value
                for slot, value in read_map.items()
            ):
                raise ArchiveError('resolved archive read and write map rosters differ')
            mbsm = document.head.get('mbsm')
            if mbsm is not None:
                rows = mbsm.get('fcd8') or ()
                resolved_report['mbsm_modern_entries'] = [
                    dict(key=row['key'], owner=describe(row['o'])) for row in rows
                    if row['o'] is not None and row['o'].cls == 'moPerBodySheetMetalDataNew_c'
                ]
            resolved_report.update(exact_replay=True, map_count=reader.count, roots=len(document.roots))
        except (ArchiveError, ValueError, KeyError) as error:
            resolved_report.update(error_type=type(error).__name__, diagnostic=str(error)[:350],
                                   boundary=getattr(error, 'details', None), missing_schemas=usage.snapshot()['missing_schemas'])
    resolved_report['cut_list_candidate_replays'] = replay_boundaries(resolved, rules, version, cut_lists)
    resolved_report['template_candidate_replays'] = replay_boundaries(resolved, rules, version, templates)
    resolved_report['base_flange_candidate_replays'] = replay_boundaries(resolved, rules, version, base_flanges)
    resolved_report['flat_pattern_candidate_replays'] = replay_boundaries(resolved, rules, version, flat_patterns)
    return result


def main():
    parser = ArgumentParser(description='Check a digest-pinned native Config stream against the provisional sheet-metal child layout')
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--part', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--linked', action='store_true', help='also check CMgr and the inherited ResolvedFeatures handoff')
    args = parser.parse_args()
    with args.part.open('rb') as handle:
        source = handle.read(MAX_PART + 1)
    digest = image(source)
    if not source or len(source) > MAX_PART or digest != args.sha256:
        parser.error('part is empty, oversized or differs from its supplied digest')
    git = ['git', '--no-replace-objects', '-C', str(args.reference)]
    clean_env = {key: value for key, value in os.environ.items()
                 if not key.upper().startswith('GIT_')}
    with TemporaryDirectory(prefix='KitSheetMetal') as temporary:
        root = Path(temporary)
        archive = root / 'Reference.tar'
        serial = 're/tooling/sw2026/serial'
        for arguments in ([REFERENCE, 'src'], [f'--prefix={serial}/', f'{REFERENCE}:{serial}']):
            with archive.open('wb') as output:
                subprocess.run([*git, 'archive', *arguments], check=True,
                               stdout=output, env=clean_env, timeout=90)
            with open_tar(archive) as payload:
                payload.extractall(root, filter='data')
        sys.path[:0] = [str(root / 'src'), str(root / 're/tooling/sw2026/serial')]
        from Classes import registry
        from Core import ArchiveError
        from convert.adapters.solidworks.Container.Container import SldprtArchive
        try:
            result = inspect(SldprtArchive.from_bytes(source), registry, 'Contents/Config-0', args.linked)
        except (ArchiveError, ValueError, KeyError) as error:
            print(json.dumps(dict(source_sha256=digest, reference_revision=REFERENCE,
                                  research_only=True, exact_replay=False,
                                  error_type=type(error).__name__, diagnostic=str(error)[:350])))
            return 2
    print(json.dumps(dict(source_sha256=image(source), reference_revision=REFERENCE, **result), indent=2, sort_keys=True))
    return 2 if args.linked and not result['linked_streams']['resolved']['exact_replay'] else 0


if __name__ == '__main__':
    sys.exit(main())