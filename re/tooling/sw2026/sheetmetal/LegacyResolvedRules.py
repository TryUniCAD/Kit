"""Provisional typed rules for the version-19000 legacy linked archive."""


def install_legacy_resolved_rules(rules, boundary):
    from Core import ArchiveError
    from Dsl import Vge, base, cstr, i32, u32
    from Schema import Fn, Rep
    from defs.ResolvedCore import concept_vt, vt

    begin, end = boundary

    def require_profile(archive, fields, owner):
        if archive.version != 19000 or owner.schema != 1:
            raise ArchiveError(f'{owner.cls} is outside the version-19000 schema-one legacy proposal')

    profile = Fn(require_profile, require_profile)
    plain = 'moFtrFolder_c'
    table = 'moConfigTableFolder_c'
    concept_vt(plain)
    concept_vt(table)
    # SP04.1 sldmodu vtable 0x1f31ab0: GetDummyFolder returns zero.
    # The Notes-derived object retains its separate true callback.
    vt(0xA40, plain, False)

    def only_plain(operation):
        def load(reader, fields, owner):
            if owner.cls == plain:
                operation.load(reader, fields, owner)

        def store(writer, fields, owner):
            if owner.cls == plain:
                operation.store(writer, fields, owner)

        return Fn(load, store)

    rules.classes[plain] = [
        only_plain(profile), only_plain(begin), *rules.classes[plain], only_plain(end),
    ]
    # SP04.1 sldmodu vtable 0x1f28358 dispatches directly to moFolder_c::Serialize.
    rules.provisional(table, [profile, begin, base('moFolder_c'), end])
    feature = 'moNativeConfigurationTableFeature_c'
    concept_vt(feature)
    # SP04.1 sldmodu RVA 0x4525b0 calls moModelFeature_c before its own data.
    # The current direct archive lane stores the same data that load reads at >= 0x374e.
    rules.provisional(feature, [
        profile, begin, base('moModelFeature_c'),
        Vge(0x374E, [
            cstr('f370'), i32('f378'), i32('f37c'), i32('n380'),
            Rep('n380', 'f380', [cstr('key'), cstr('value')]),
            u32('f390'),
        ]),
        end,
    ])


def install_legacy_bend_rules(rules, boundary):
    from Core import ArchiveError
    from Dsl import i32
    from Schema import Fn, If

    begin, end = boundary
    provisional = rules.provisional

    def legacy_lane(fields, archive):
        return (archive.version == 19000 and archive.ctx.get('model_is_part') == 1
                and archive.ctx.get('cmgr_f658') == 0)

    def require_empty_axes(archive, fields, owner):
        if any(fields[name] != 0 for name in ('n00', 'n04', 'n08')):
            raise ArchiveError('nonempty sheet-metal bend-allowance arrays remain unresolved')

    def register(name, operations, **options):
        if name == 'sm.bend_allow':
            # The frozen probe installs this embedded layout while opening ResolvedFeatures.
            # Its two mode-zero signed fields do not count matrix rows.
            expected = {0: 'n00', 1: 'n04', 2: 'n08', 9: 'n30', 10: 'n34', 12: 'f110'}
            if len(operations) != 20 or any(
                getattr(operations[index], 'name', None) != field for index, field in expected.items()
            ):
                raise ArchiveError('the frozen bend-allowance grammar differs from its legacy overlay')
            legacy = [begin, *operations[:3], Fn(require_empty_axes, require_empty_axes),
                      *operations[4:9], i32('f30'), i32('f34'), *operations[12:], end]
            operations = [If(legacy_lane, legacy, operations)]
        return provisional(name, operations, **options)

    rules.provisional = register


def replay_legacy_bend(resolved, rules, version, observations):
    from hashlib import sha256
    from Core import ArchiveError, Store

    def roster(snapshot):
        return {entry.IndexValue: entry.EntryValue for entry in snapshot.state.EntriesValue}

    records = []
    for start, end, seed, context, read_state, fields, owner in observations:
        writer = Store(seed.count, rules, version, context, seed=seed)
        rules.run_store('sm.bend_allow', writer, fields, owner)
        write_state = writer.map_state()
        inherited, read_map, write_map = roster(seed), roster(read_state), roster(write_state)
        payload = resolved[start:end]
        if (payload != bytes(writer.out) or read_state.count != write_state.count
                or read_map.keys() != write_map.keys()
                or any(read_map.get(slot) is not value or write_map.get(slot) is not value
                       for slot, value in inherited.items())
                or any(write_map[slot] is not value and write_map[slot] != value
                       for slot, value in read_map.items())):
            raise ArchiveError('legacy bend allowance did not reproduce its bytes and map identities')
        records.append(dict(
            owner_class=owner.cls, owner_slot=owner.index, wire_class='sm.bend_allow',
            payload_start=start, payload_end=end, payload_sha256=sha256(payload).hexdigest(),
            inherited_count=seed.count, resulting_count=read_state.count,
            exact_replay=True, signed_members={key: fields[key] for key in ('f30', 'f34')},
        ))
    return records


def install_legacy_sketch_bend_rules(rules, boundary):
    from Core import ArchiveError
    from Dsl import base, emb, f64, i32, u8, u16
    from Schema import Fn, If
    from defs.ResolvedCore import concept_vt, xo
    from defs.ResolvedSketch import HANDLE

    begin, end = boundary

    def profile(ar, fields, owner):
        if (owner.schema != 1 or ar.version != 19000 or
                ar.ctx.get('model_is_part') != 1 or ar.ctx.get('cmgr_f658') != 0):
            raise ArchiveError('OneBend is outside the mode-zero version-19000 schema-one proposal')

    def require_supported_sketch_body(ar, fields, owner):
        if fields['fad0'] == 7:
            raise ArchiveError('unsupported SketchBend mode-seven inline feature and raw body lane')

    def empty_body(field):
        def check(ar, fields, owner):
            if fields[field] != 0:
                raise ArchiveError(f'unsupported OneBend nonempty raw body owner {field} ({fields[field]})')
        return Fn(check, check)

    concept_vt('moOneBend_c')
    concept_vt('moSketchBend_c')
    rules.provisional('moOneBend_c', [
        Fn(profile, profile), base('moSheetMetalCommon_c'),
        xo('f880_sketch', 'sgSketch'), xo('f868', 'moCompBEntRef_c'),
        xo('f870', 'moDisplayAngularDim_c'), xo('f878', 'moDisplayDim_c'),
        u16('f860'), i32('f900'), f64('f8c0'), i32('f8c8'), i32('f8d0'),
        i32('f8d4'), i32('f8cc'), i32('f8d8'), xo('f8e0', 'moDisplayDim_c'),
        xo('f8e8', 'moDisplayDim_c'), i32('f8f0'), u8('fa18'),
        xo('f888_sketch', 'sgSketch'),
        If(lambda fields, ar: fields['f888_sketch'] is not None, [emb('f888_handle', HANDLE)]),
        xo('f890', 'suObList'),
        xo('fa98'), xo('faa8', 'moCompFeature_c'), xo('fab0', 'moCompFeature_c'),
        i32('fad0'), xo('fad8', 'moConicBendData_c'),
        emb('f908', 'mgXform_c.restore'), emb('f990', 'mgXform_c.restore'),
        i32('fae0'), i32('fae4'), i32('fa38'), i32('fb6c'), i32('fa3c'),
        xo('faa0'), xo('fab8', 'moCompFeature_c'), xo('fac0', 'moCompFeature_c'),
        If(lambda fields, ar: fields['f880_sketch'] is not None, [emb('f880_handle', HANDLE)]),
        i32('naf8'), empty_body('naf8'), i32('nb18'), empty_body('nb18'),
        i32('fb48'), empty_body('fb48'), i32('fb58'), empty_body('fb58'),
        i32('fa90'), i32('fa60'), i32('fa64'), i32('fd5c'),
    ])
    rules.provisional('moSketchBend_c', [
        begin, base('moOneBend_c'), Fn(require_supported_sketch_body, require_supported_sketch_body),
        xo('fdf8_sketch', 'sgSketch'),
        xo('fdf8_handle', 'sgEntHandle'), xo('fe20', 'sgEntHandle'), xo('fe48', 'sgEntHandle'),
        xo('fde8', 'moCurveRef_w'), i32('fe78'), end,
    ])


def install_legacy_mitered_flange(rules, boundary):
    from Core import ArchiveError
    from Dsl import base, emb, f64, i32
    from Schema import Fn, If, Rep
    from defs.ResolvedCore import concept_vt, obarray, xo

    begin, end = boundary
    name = 'moSMMiteredFlange_c'

    def require_profile(ar, fields, owner):
        if (owner.cls != name or owner.schema != 1 or ar.version != 19000 or
                ar.ctx.get('model_is_part') != 1 or ar.ctx.get('cmgr_f658') != 0):
            raise ArchiveError('MiteredFlange is outside the mode-zero version-19000 schema-one proposal')

    def count_check(ar, fields, owner):
        if fields['n'] < 0:
            raise ArchiveError('unsupported MiteredFlange sketch handle count')

    rules.provisional('sm.mitered_group', [
        i32('n'), Fn(count_check, count_check),
        If(lambda fields, ar: fields['n'] > 0, [
            xo('sketch', 'sgSketch'), Rep('n', 'handles', [xo('o', 'sgEntHandle')]),
        ]),
    ])

    def require_edge_schema(ar, fields, owner):
        if owner.schema != 1:
            raise ArchiveError(f'{owner.cls} is outside the schema-one edge-geometry proposal')

    rules.provisional('moEdgeGeom_c', [
        Fn(require_edge_schema, require_edge_schema), i32('f08'),
        emb('f10', 'mgVector_c.restore'), emb('f28', 'mgVector_c.restore'),
        emb('f40', 'mgPoint_c.restore'), emb('f58', 'mgPoint_c.restore'),
        emb('f70', 'mgPoint_c.restore'),
    ])
    rules.provisional('moLinearEdgeGeom_c', [base('moEdgeGeom_c')])
    concept_vt(name)
    rules.provisional(name, [
        Fn(require_profile, require_profile), begin, base('moSheetMetalBendGroup_c'),
        xo('f920', 'moProfileRef_w'),
        f64('f950'), f64('fc28'), f64('fc30'), f64('fc38'),
        i32('f970'), i32('f974'), i32('f978'), i32('f984'), i32('f988'),
        i32('fba4'), i32('f98c'), i32('fba0'),
        f64('fc10'), f64('fc18'), i32('fc20'), i32('fc24'),
        xo('fc40', 'moDisplayDim_c'), xo('fc48', 'moDisplayDim_c'), i32('f97c'),
        obarray('f990'), emb('fbb0', 'su_CDWordArray'), emb('fbd0', 'su_CDWordArray'), obarray('fbf0'),
        *(emb(field, 'sm.mitered_group') for field in ('f9f8', 'fa18', 'fa38', 'fa58')),
        obarray('fc60'), i32('f980'), end,
    ])


def install_legacy_ui_bend(rules, boundary):
    from Core import ArchiveError
    from Dsl import base
    from Schema import Fn
    from defs.ResolvedCore import concept_vt, xo

    begin, end = boundary
    name = 'moUiBend_c'

    def require_profile(archive, fields, owner):
        if (owner.cls != name or owner.schema != 1 or archive.version != 19000
                or archive.ctx.get('model_is_part') != 1
                or archive.ctx.get('cmgr_f658') != 0):
            raise ArchiveError('UiBend is outside the mode-zero version-19000 schema-one proposal')

    concept_vt(name)
    rules.provisional(name, [
        Fn(require_profile, require_profile), begin, base('moBodyFeature_c'),
        xo('f810', 'moOneBend_c'), end,
    ])

def describe_ui_bend_links(probe, observations):
    rows = []
    for _, _, incoming, _, _, fields, owner in observations:
        if owner.cls != 'moUiBend_c':
            continue
        target = fields['f810']
        target_slot = getattr(target, 'index', None)
        inherited = any(entry.IndexValue == target_slot and entry.EntryValue is target
                        for entry in incoming.state.EntriesValue)
        rows.append(dict(
            owner=probe.describe(owner), owner_f08=fields.get('f08'),
            target=probe.describe(target), target_f08=getattr(target, 'f', {}).get('f08'),
            target_inherited=inherited,
        ))
    return rows


def install_legacy_flat_body_reader(rules, observations):
    from Core import ArchiveError
    from Schema import Fn
    from convert.Geometry.ParaFormatError import ParaFormatError
    from convert.Geometry.ParaFraming import KWrapperMagic
    from convert.Geometry.Parasolid import DecodeBrepMut, IsPayloadApiMut
    from convert.Geometry.ReadParaSection import ReadParaSection
    from hashlib import sha256
    from struct import unpack_from

    provisional = rules.provisional

    def read(original, archive, fields, owner):
        if (owner.cls != 'moFlatPattern_c' or owner.schema != 1 or archive.version != 19000
                or archive.ctx.get('model_is_part') != 1 or archive.ctx.get('cmgr_f658') != 0
                or fields['has_flat_parasolid'] != 1):
            return original.load(archive, fields, owner)
        start = archive.p
        if archive.left() < 5:
            raise ArchiveError('truncated legacy flat-pattern body header')
        length, kernel = unpack_from('<iB', archive.b, start)
        if not 29 <= length <= min(archive.left() - 4, 16 * 1024 * 1024) or kernel != 0:
            raise ArchiveError('unsupported legacy flat-pattern body framing or kernel')
        end = start + 4 + length
        frame = archive.b[start + 5:end]
        if (unpack_from('<I', frame)[0] != len(frame) - 4
                or frame[4:4 + len(KWrapperMagic)] != KWrapperMagic):
            raise ArchiveError('legacy flat-pattern body lacks an exact chained native frame')
        try:
            section = ReadParaSection(frame, 4, 16 * 1024 * 1024)
            if section.Start != 0 or section.End != len(frame) or not IsPayloadApiMut(section.Data):
                raise ArchiveError('legacy flat-pattern body does not occupy one exact native frame')
            model = DecodeBrepMut(section.Data)
        except (ParaFormatError, ValueError) as error:
            raise ArchiveError(f'legacy flat-pattern body failed typed geometry decode: {error}') from error
        if model is None or len(model.bodies) != 1:
            raise ArchiveError('legacy flat-pattern cache lacks one typed geometry body')
        fields['legacy_flat_body'] = model
        archive.p = end
        observations.append(dict(start=start, end=end, map_count=archive.count, feature_id=fields.get('f08'),
                                 sha256=sha256(section.Data).hexdigest(), body_count=len(model.bodies),
                                 face_count=len(model.faces), edge_count=len(model.edges), vertex_count=len(model.vertices)))

    def store(original, archive, fields, owner):
        if fields.get('legacy_flat_body') is not None:
            raise ArchiveError('legacy flat-pattern body typed cache has no exact store rule')
        return original.store(archive, fields, owner)

    def register(name, operations, **options):
        if name == 'moFlatPattern_c':
            indices = [i for i, op in enumerate(operations)
                       if getattr(op, 'name', None) == 'has_flat_parasolid']
            if (len(indices) != 1 or indices[0] + 2 >= len(operations)
                    or not isinstance(operations[indices[0] + 1], Fn)
                    or getattr(operations[indices[0] + 2], 'name', None) != 'f990'):
                raise ArchiveError('frozen flat-pattern layout differs from its legacy cache overlay')
            at = indices[0] + 1
            original = operations[at]
            operation = Fn(lambda ar, fields, owner: read(original, ar, fields, owner),
                           lambda ar, fields, owner: store(original, ar, fields, owner))
            operations = [*operations[:at], operation, *operations[at+1:]]
        return provisional(name, operations, **options)

    rules.provisional = register
