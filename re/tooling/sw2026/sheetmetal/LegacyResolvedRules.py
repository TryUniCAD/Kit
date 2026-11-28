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
