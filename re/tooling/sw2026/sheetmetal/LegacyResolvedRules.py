"""Provisional typed folder rules for the version-19000 legacy linked archive."""


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
