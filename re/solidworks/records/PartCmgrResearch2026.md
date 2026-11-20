# Standalone ordinary single-configuration CMgr research

Task `B04-SW2026-CMGR` uses accepted SDK base
`dbfbb09cbe8576b275b01487b8e195d6b00e08be` and the layout source at
`2393c3a8106e83ee90e977fb167d27900e5f4f2a`. The [original branch evidence](https://github.com/TryUniCAD/Kit/blob/2393c3a8106e83ee90e977fb167d27900e5f4f2a/re/solidworks/records/CmgrBodyGrammar2026.md)
binds the ordinary version-19000 serializer and map. This local
research covers `Contents/CMgr` with one `moPartConfiguration_c` row.

The wrapper starts at map base 1 and uses 31 body and embedded layouts
and eight concrete schema-one descriptors. Each positive reads to
the physical end of the stream, verifies the contiguous map from slot 1,
and matches all reached objects, descriptors and byte spans after emission
and readback. Both selectors must alias the actual directory object
with local ID 0. A manager name is either null or its own name object.
The configuration name, comment, alternate name and description are
separate fields.

| Disclosed control | Manager name | CMgr bytes | Next map slot | Reached layouts |
| --- | --- | ---: | ---: | ---: |
| SOLIDWORKS-authored L1 | Absent | 2159 | 19 | 31 |
| Kit-authored ConcaveOwned | Present | 1129 | 10 | 19 |
| Kit-authored RectangularBare | Present | 1129 | 10 | 19 |

The two independent authored geometry controls share identical manager
bytes. The two distinct streams and all three input digests are pinned in
the [process receipt](../measurements/2026/PartCmgrResearch01.json).
Two separate typed graph edits add and remove the optional name and vary
the actual row's text, including Unicode. Adding the manager name moves
the configuration from slot 4 to slot 6. Removing it moves the configuration
from slot 6 to slot 4. The emitted maps retain selector identity. The source
maps retain their original slots. These are edits of typed disclosed graphs.

Eleven refusals cover the logical version, concrete class and schema,
truncation, trailing bytes, absent or empty name fields, equal-looking but
distinct selector objects, and multiple configuration rows. The last two
also refuse after reparsing malformed streams emitted by the typed executor.
Each case ran twice in a fresh process with identical output. The worker
denies file, process, library and network access during decode and emission.

## Shared executor requirements

The accepted read-side `NotCondition` and context actions suffice.
The research wrapper reuses the main SDK for graph identity, scalar and
string fields, conditional body execution and array counts. It adds
only two local write actions. `Context` invokes the shared
`ChangeFlagsMut`. `Virtual` with `Flag` evaluates the concrete
Boolean rule before writing the nested fields. With only write Context
added, the first replay stops at the accepted writer's
`unsupported native body virtual dispatch mode` diagnostic. The actual
feature base uses concrete slot `0x3f8` for this decision.

The remaining layout definitions are pinned aggregate Git objects loaded
before the guard. No aggregate universal body registry is mounted.
The unique graft is the configuration group, the user property helper,
external bodies built from the accepted Header rules, the PBR layout,
and the `su_CDWordArray` and framework `su_CMapStringToInt` rows.
The existing feature, geometry, mass, object-list and CString-array
grammars are reused. The virtual registry selects the existing manager
and part-configuration entries. The eight descriptor entries allow
schema one only. The receipt pins the layout files and source tools.

```sh
python3.14 -I -B re/tooling/sw2026/cmgr_slice/CheckPartCmgr.py l1
python3.14 -I -B re/tooling/sw2026/cmgr_slice/CheckPartCmgr.py concave
python3.14 -I -B re/tooling/sw2026/cmgr_slice/CheckPartCmgr.py rectangular
python3.14 -I -B re/tooling/sw2026/cmgr_slice/CheckPartCmgr.py add-name
python3.14 -I -B re/tooling/sw2026/cmgr_slice/CheckPartCmgr.py remove-name
python3.14 -I -B re/tooling/sw2026/cmgr_slice/CheckPartCmgr.py refuse
```

The constructor, assembly contexts and public transfer require separate
evidence. This work records zero native runs, zero held-out cases and
zero native output qualification. Public admission remains subject to
the [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
