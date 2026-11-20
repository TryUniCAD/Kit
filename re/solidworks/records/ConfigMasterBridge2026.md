# SOLIDWORKS 2026 direct configuration master

| Delivery item | Scope |
| --- | --- |
| Task | B04-SW2026-CONFIG-MASTER |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch codex/solidworks-config-direct-owner |
| Dependencies | Accepted part ModelHeader binding, shared feature layout and concrete virtual dispatch |
| Exit | Exact present and absent native intervals, typed child and inherited map, authored contrasts, current-revision queue and review |

The model stores signed f1014 as a distinct scalar. Zero leaves f1018
absent. A nonzero value enters the inherited feature body of the concrete
`moSheetMetalMaster_c` without a separate archive tag. The four virtual
targets select its concept lightweight and resolved fields and its
feature XML path. The record has its own field scope and no map slot.
The final signed n370 owns the per-body list. This bounded reader
accepts an empty list and absent feature links. Other variants require
their own ownership and source evidence.

| Saved part | Selector and body span | Selector | Body bytes | Map before to after |
| --- | --- | ---: | ---: | ---: |
| RectangleProperties | [25099, 25103) | 0 | 0 | 105 to 105 |
| CircularProperties | [25320, 25473) | 1 | 149 | 119 to 119 |
| CircleRadiusBoss open-save | [24214, 24367) | 1 | 149 | 118 to 118 |

The exact full source traversal uses aggregate revision
`9e0a4b85dd21cdfb7feb50eda94593ef9e9b01f9` for the physical feature grammar.
The earlier version-specific DLL analysis binds the concrete serializer
and its callback cells. CircularProperties and CircleRadiusBoss differ
in f28c and other stored feature words.
[Static serializer evidence](https://github.com/TryUniCAD/Kit/blob/9e0a4b85dd21cdfb7feb50eda94593ef9e9b01f9/re/solidworks/records/SmmMasterArchive2026.json)

## Full physical prefix and bounded queue proof

The full-prefix worker resolves each disclosed source through the pinned
research corpus identity functions. It exports the aggregate SDK from its
pinned Git object and verifies all Python blobs before traversal. The
aggregate parser walks the entire original Config-0 and the named
ModelHeader. The observed dispatch of the part's signed f1014 supplies the
start, end and actual before and after maps. The bounded reader runs at that
boundary with the same objects, including the actual part and header alias.
Five byte-identical map types preserve those object identities between the
two SDK revisions. The original traversal then completes and exhausts the
full Config-0 stream.

Each of the 104, 118 and 117 inherited slots is recorded for the respective
rectangle, circular and circle-save case. A present direct master keeps the
whole map unchanged. The two present controls have distinct full field
digests. Comparing the aggregate and bounded readers checks every decoded
field, including inherited fields outside the selected SDK assertions.
[Complete native prefix receipt](../measurements/2026/ConfigMasterPrefix01.json)

The merge queue runs the bounded check with the three actual slots from
`ReadPartStart` and next counter 4. It asserts the complete direct-master
field digests from the full replay. The former bound reused the early slots
with a separately supplied counter. The [historical receipt](../measurements/2026/ConfigMasterBridge01.json)
preserves that result. The queue's shallow checkout does not carry the
unmerged aggregate object, so the full replay uses a trusted local checkout
containing that exact revision.

The [research automation reader](https://github.com/TryUniCAD/Kit/blob/22075ee5e77c3db9b56bd8c2bc8c415d6baf237d/re/automation/SolidworksReader.py)
exposes a neutral document and separate evidence receipt. Its capture and
neutral comparison interfaces have no internal archive cursor or map handoff.
The full replay reuses the supported corpus pin and Git byte verification.
Its archive observer is specific to this field boundary and produces no
neutral document or change to research-read status.

## Count framing and remaining scope

The independent frames use selectors -7 and 41, variable-length Unicode
text and a separate embedded width. An authored `ffff` escape followed by
an unsigned zero retains the six-byte count in `f60.list.n#width`. The
native controls use the compact form. The extended form grows the authored
body by four bytes and preserves the following fields. Eleven refusals
cover invalid versions, owners, tags, active lists and nonzero tails.
All guarded calls reported zero external accesses.

Populated per-body rows and linked masters retain separate format gates.
Normal `ReadNativePart` integration, complete sheet-metal feature history,
lossless translation and independent native acceptance remain open. The
disclosed controls supply no held-out or generated-file credit.

```sh
python -I -B re/tooling/sw2026/CheckCfgMaster.py rectangle
python -I -B re/tooling/sw2026/CheckCfgMaster.py circular
python -I -B re/tooling/sw2026/CheckCfgMaster.py circle-save
python -I -B re/tooling/sw2026/CheckCfgMasterPrefix.py rectangle --verify
python -I -B re/tooling/sw2026/CheckCfgMasterPrefix.py circular --verify
python -I -B re/tooling/sw2026/CheckCfgMasterPrefix.py circle-save --verify
```
