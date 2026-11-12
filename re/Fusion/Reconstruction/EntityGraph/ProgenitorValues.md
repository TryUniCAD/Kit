# Progenitor Auxiliary Value Layout

The current Fusion 2706.1.17 value type `ProgenitorAuxDataValueMetaType`, identifier `BE7E2847-FBC4-4898-A6E7-632A559A7F89`, has one persisted field: `tag`, an unsigned 32-bit integer. Its schema version is zero and it has no base value class. The value payload is exactly four little-endian bytes.

The static extraction in [ProgenitorEvidence.json](ProgenitorEvidence.json) records the analyzed arm64 image hashes, complete relevant instruction sequences, an independently traced member-option allocation contract, and the complete symbolic registration trace. [ProgenitorValues.py](ProgenitorValues.py) supplies the inverse reader and writer plus a declarative member-set description. The callback consumes no source payload or opaque remainder.

| Native address | Evidence |
| --- | --- |
| `0x9f6f0` | `ProgenitorAuxData::initializeMemberSet(unsigned int, MemberSet*)` starts |
| `0x9f70c` | Loads the literal property name `tag` |
| `0x9f71c` | Loads `__ZTIj`, RTTI for C++ `unsigned int` |
| `0x9f728`–`0x9f72c` | Loads `IntrinsicMetaType<unsigned int>::c_pTheOnlyOneuint32` |
| `0x9f734` | Supplies the member address at object offset `0x18` |
| `0x9f744`, `0x9f748` | Supplies null templated-functions and custom implementation pointers |
| `0x9f74c` | Registers the only member through `MemberSet::addNewMember` |
| `0x9f358` | Reports an in-memory object size of `0x20` bytes |
| `0x9f388` | Constructor writes `0xffffffff` to the tag member |

The member initializer has no schema-version branch, option mutation, or callback registration. The separate `NsDataModel10` allocation trace proves that this direct registration receives default option mask `0x33`; ordinary save/load visits members with bit zero set. A single member also removes any ambiguity about lexical ordering.

The in-memory object contains a vtable pointer, a current-version word at offset `0x08`, and a pointer at `0x10`. Those fields are absent from the registered member set and are not serialized ahead of `tag`. The 32-byte object size must not be mistaken for a 32-byte payload.

The initial corpus inventory reported this metatype as named metadata in 36 `SweepFaceProgenitor` records and two `EntityProgenitor` records. The enclosing named-metadata frame already supplies its name and metatype identifier; the auxiliary value contributes only the four tag bytes. The parent's corpus inventory owns the subsequent complete-record decode results.

The exact tag identity domain and its relationship to geometric tagging remain unproven. The constructor default does not restrict valid serialized values to `0xffffffff`. The reader and writer retain every unsigned 32-bit value. This static analysis did not invoke the application, load its libraries, or establish target-application acceptance for an independently changed auxiliary tag.
