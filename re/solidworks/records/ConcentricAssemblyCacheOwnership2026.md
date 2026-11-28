# SOLIDWORKS 2026 separate assembly caches

Task `B04-SW2026-MATES-CONCENTRIC`, PR #121. This read-only check at
`d89dd5965880fda9b645336527b20fc02557d4e9` identifies the fresh-save
owners of `Contents/Config-0-LWDATA` and `Contents/DisplayLists`. It
qualifies omission for the exact generated, resolved lifecycles already
measured in SOLIDWORKS 2026 SP05.2 (`34.5.2.0604`). The
[numeric receipt](../measurements/2026/ConcentricAssemblyCacheOwnership01.json)
binds 17 whole-file hashes and the two members' uncompressed sizes and
digests. Only pre-existing disclosed files and licensed local modules
were read. No native process, writer or held-out read ran for this check.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[File anatomy](../../Playbook/README.md)

## Previously measured omission

All six neutral-generated assembly archives in the following four
lifecycles omit both members. The prior native receipts cover open,
rebuild, edit, save and fresh reopen with healthy controls across 16
application processes. Frame and module are separate files in
each nested bundle. Their saved digests refer to the same synchronized
save that the native reopen measured.

| Exact generated assembly SHA-256 | Prior measured profile | `Config-0-LWDATA` on native save (bytes) | `DisplayLists` on native save (bytes) |
| --- | --- | ---: | ---: |
| `9474ca54466a450eec3ba5e49703053fe160e0a221647b2bcc984d8d3672dc74` | Aligned unlocked radial concentric | 1,437 | 7,533 |
| `1522aa21cb3f39db16a6b082088fef0a0063acf6a53df6cb31c479137761eda3` | Explicit planar mate group | 1,437 | 8,896 |
| `90260a5b99429d757208e9354f2e2ba65ece47854751394d576c8a00ab17f9ed` | Nested frame | 1,437 | 8,481 |
| `20fabea8f16ca4a521e4afbd448eb27cbaf3780f02df2c0cafd77aed4872b197` | Nested module | 1,437 | Absent |
| `cd7d242faa4b0abad532663e6a97e4ed806672b501c35128804a6b98d8fc580b` | Repeated nested frame | 1,437 | 16,032 |
| `e7dbdffe30d80296da1655fc88d938c82f22f8cc63f522acdac8d5ecb91f3a07` | Repeated nested module | 1,437 | Absent |

[Radial native measurement](../measurements/2026/ConcentricRadialAssemblyNative01.json) ·
[Planar native measurement](../measurements/2026/SdkExplicitPlanarGroupNative01.json) ·
[Nested native measurements](../measurements/2026/SdkNestedAssemblyNative01.json)

The disclosed ordinary D01 source and its edited native save both
contain both members. Their display streams are 9,659 and 10,071 bytes.
The disclosed scrubbed A07 empty, A08 single-occurrence and A09
repeated-occurrence reader controls also contain both. All 11 present
`Config-0-LWDATA` streams happen to be 1,437 bytes and have distinct
SHA-256 digests. Both saved modules carry `Config-0-LWDATA` while
omitting `DisplayLists`. These contrasts give no fixed cache payload to
emit and do not establish the exact predicate for saving a display list.
[D01 source pins](../measurements/2026/ConcentricMateSdkArchive01.json) ·
[Tracked reader controls](../v2026/corpus/assembly-discovery/Manifest.json)

## Native save owners

- `SolidStorage_c::saveLWData` (`doccplu.dll`, RVA `0x2ffc0`) obtains
  the configuration's actual storage name at `0x18003002e` and appends
  `-LWDATA` at `0x180030057`. It opens the named member under `Contents`.
  The supplied-configuration branch gets the configuration's opened
  `moModel_c` at `0x18003018a`. The other branch obtains the document
  model. At `0x1800301a8` it constructs `moLWdataHelper_c` with that
  model. At `0x1800301c0` it serializes the helper into the member's
  archive. That import binds to `moLWdataHelper_c::Serialize` at
  `0x4c792350` in `sldmodu.dll`. This is a separate per-configuration
  lightweight save layer. The inline `moAssembly_c::SerializeLWData`
  section in `Contents/Config-0` still has its own measured header alias
  and object-map rules. [Inline configuration section](AssemblyDirectAction2026.md)
- `SolidStorage_c::SaveDisplayLists` (`doccplu.dll`, RVA `0x1f7b0`)
  enters the UI document's display-list save state and opens
  `Contents/DisplayLists` at `0x18001fa11`. It sets up
  `moArchiveHelperObject_c` and dispatches at `0x18001fa66` through
  slot `0x3160`. The RTTI-verified `uiAssemblyDoc_c` primary vtable at
  `0x3fc5e0b8` binds that slot to `uiAssemblyDoc_c::iSaveDisplayLists`
  at `0x3f7afa20` in `sldasmu.dll`. That routine reaches the actual
  model configuration manager, UI view array and active B-rep view.
  A separate static branch at `0x18001fd30` dispatches slot `0x3178`
  to `iSaveDisplayListsMultipleConfigs` at `0x3f7b0fb0`. The
  multi-configuration branch is included for ownership only. No dynamic
  branch-count or payload-field inference follows from the file census.

The module and exception-directory routine digests in the numeric
receipt bind these call edges to SP05.2. The bound owner paths make both
members separate derived save data. The measured resolved routes can
omit them while retaining the assembly, mate and edit behavior checked
in the previous trials. Lightweight open, quick view, graphics
fidelity, alternative configuration states and a complete intact D01
source round trip remain unqualified. This observation changes neither
production admission nor the exact source or publication gates.

## Reproduce a member check

For each disclosed file, provide its receipt role and the actual path
from its original packet. The radial files are `Frozen` and `Working`
copies of `RadialConcentricProbe.SLDASM`. The planar and nested
generated/saved pairs are the `FrozenGenerated` and `GeneratedInput`
copies in their respective packets. Use `SdkPlanarGroup3Alpha.SLDASM`
for the planar case and `SdkFrame.SLDASM` or `SdkModule.SLDASM` inside
each nested packet. The D01 files are `ConcentricD01AlignedFree.SLDASM`
under `Disclosed/D01/Native/Source` and `Disclosed/D01/Native/Edited`.
The three tracked controls are named by their discovery manifest.

```sh
PYTHONPATH=src python3.14 -B - radial_concentric_generated /path/to/Frozen/RadialConcentricProbe.SLDASM <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys

from convert.adapters.solidworks.Container.Container import SldprtArchive

receipt = json.loads(Path("re/solidworks/measurements/2026/ConcentricAssemblyCacheOwnership01.json").read_bytes())
case = receipt["inputs"][sys.argv[1]]
data = Path(sys.argv[2]).read_bytes()
assert len(data) == case["archive_bytes"] and sha256(data).hexdigest() == case["archive_sha256"]
container = SldprtArchive.from_bytes(data)
assert container.format_version == case["container_format_version_field"]
for name, expected in case["streams"].items():
    payload = container.get(name)
    actual = None if payload is None else {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}
    assert actual == expected, name
PY
```

To reproduce static bindings, verify the full module hashes before
reading the recorded virtual addresses. The existing
[PE reader](../../tooling/sw2026/CollectDrawingViewSupportEvidence.py)
resolves imports, exports and routine bounds. The
[RTTI table reader](../../tooling/sw2026/CollectConcentricEvidence.py)
resolves both assembly document slots from the same primary table.
Disassemble the bounded functions locally to confirm the named-stream
operations, imports and calls at the recorded sites.
