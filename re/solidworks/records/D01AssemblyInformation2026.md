# Assembly system information properties

Task `B04-SW2026-MATES-CONCENTRIC/system-information` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The construction shares the measured desktop information-property container with the part writer. Its separate assembly property at ID 19 is `Assembly type` with the ordinary `vt:bool` value `No`. The shared IDs at and after that position advance by one. The dictionary inserts the assembly entry first and keeps the shared order and explicit text aliases. The construction emits no optional mass-summary row for this profile. [Shared framing](../../solidworks/WriterResearch/PartInformation.py)

| Fields | Classification and source |
| --- | --- |
| File and BOM part names | The destination stem supplies `SW-File Name`. The actual saved assembly header and model root agree on the title used for `SW-BOM Part Number`. In the first-save sources the current filename and live model title differ. |
| Folder | The nonempty `moHeader_c.f38.shared.h18` locator supplies its parent directory with a terminal backslash. An absent locator produces the empty property. |
| Configuration | The actual selected CMgr configuration supplies the name. |
| Calendar and provenance | The exact UTC created and modified events and save actor come from the typed core properties. An explicitly supplied UTC offset produces the scoped U.S. English short date, long date and 12-hour timestamps. The source Windows settings in the measured cases correspond to UTC minus eight hours. |
| Empty summary and ordinary assembly flags | The profiled core owner has the three provenance fields. Six absent summary values are empty. Twelve saved assemblies agree on Y-up, ordinary `Assembly type`, modern properties, the absent design table and component type zero. |
| Units | The actual Config-0 unit nodes supply `fb0` selectors, precision `f0c`, decimal modes `f10` and length denominators `f28`. System, time, power, energy, force, mass and volume use one-based property codes. A missing dual length uses the shared `MakeDualLength` constructor for the document's actual primary length. The mass length inherits the primary owner for this profile. Both possible density volume slots agree, allowing either measured `fcc` selector. |
| Remaining display options | The scoped rounding and feet-and-inches selectors retain the measured ordinary values across the twelve assemblies. |

All 49 properties and their dictionary entries reproduce the complete source stream byte for byte in twelve disclosed assemblies. The two guarded model-only workers add the stream to the existing D01 composition. The alternate authored filename includes non-ASCII text and an ampersand. The alternate offset changes the local save date. Both 35-stream variants preserve all earlier 34 streams and the whole child. A foreign document type, invalid clock offset and a duplicate stream refuse. Fourteen earlier part information comparisons still reproduce their original checked digest. [D01 proof](../../tooling/sw2026/para/concentric/ProveD01AssemblyInfo.py) · [Receipt](../measurements/2026/D01AssemblyInformation01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyInfo.py \
  --disclosures /absolute/path/to/Oracle121Takeover \
  --output /tmp/UnusedD01AssemblyInformation.json
```

The new parent has eight original source members outside the composed inventory. Its native lifecycle, additional locale and system-property variants, held-out qualification and public publication remain open.

## Shared assembly emitter

The shared constructor accepts an optional typed `AsmInfoInput`. Both assembly headers must refer to the same generated self-file object. Its actual locator and save event agree with the destination, its title agrees with the root, and its configuration reference agrees with the manager's selected object. The member is computed before the parent container exists. The default-off path adds no member. [Composition](../../tooling/sw2026/para/concentric/ProveSdkAsmInformation.py) · [SDK receipt](../measurements/2026/SdkAssemblyInformation01.json)

The core creation event is independently authored. The paired saved sources show a 0–4 second interval between binary header creation and core creation, including one second in both D01 saves. The core modification time agrees with each actual self-file `f60` save event. The scoped saved comparison derives the same bytes in all twelve source files. The generated comparison retains the complete previously recorded D01 35-stream parent and child digests, including the established D01 stream order. The alternate generated model changes the actual destination, model title, configuration, actor, calendar date and units while retaining every stream shared with its corresponding no-information version. Both isolated workers report zero external accesses. Eight settings and ownership contrasts refuse.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveSdkAsmInformation.py \
  --disclosures /absolute/path/to/Oracle121Takeover \
  --output /tmp/UnusedSdkAssemblyInformation.json
```

This is internal assembly construction evidence. Whole-source admission, the eight outstanding source members and new native qualification retain the boundaries of the prior proof.
