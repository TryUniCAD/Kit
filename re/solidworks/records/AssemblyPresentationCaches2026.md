# Assembly preview, tessellation and motion members

Task `B04-SW2026-MATES-CONCENTRIC/presentation-cache-boundary` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Twelve disclosed assemblies and a previously measured neutral-generated radial assembly and its native save give the byte and lifecycle boundaries below. [Measured inventory](../measurements/2026/AssemblyPresentationCaches01.json) · [Radial lifecycle](../measurements/2026/ConcentricRadialAssemblyNative01.json)

| Member | Observed structure and role |
| --- | --- |
| `Preview` | A length-prefixed packed DIB. The 40-byte information header describes an eight-bit palette image with RLE compression. Its palette and compressed extent account for every remaining byte in the witnessed samples. [Windows DIB fields](https://learn.microsoft.com/en-us/previous-versions/dd183376%28v%3Dvs.85%29) |
| `PreviewPNG` | A standalone PNG image. The observed stream starts with its dimension header and ends at the closing chunk. The audit verifies each chunk's extent and CRC. [PNG structure](https://www.w3.org/TR/png/) |
| `FaceTessellations/` | The directory accompanies separately named mesh members in the eleven disclosed nonempty examples. The saved empty assembly has neither. The D01 source and edited cache sizes differ, and the radial save allocates its member under `000-000-001`. The receipt records the actual membership and extent. |
| `ThirdPty/Animator` | The observed 342-byte stream starts with version 19000, an ordinary `moAnimationManager_c` and a single `moAnimKeyData_c` declaration. The manager's active index is -1. The study has a UUID4 value that survives each of the three paired source edits. The audit records its digest and the two class roles. |

The exact 2026 model DLL writes the manager's signed index from `+0x30` before the study count. The active-animation getter reads the same field and instantiates the default study if its vector is empty. The [receipt](../measurements/2026/AssemblyPresentationCaches01.json) pins the serialization and getter windows.

The earlier exact radial parent lacks all four member groups. In SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, it passed open, rebuild, driving-radius edit, save and fresh reopen, with 140 numeric comparisons and healthy controls across four separate native processes. Its vendor-saved derivative has both previews, the tessellation directory and mesh, and the motion manager. This establishes an omission boundary for that measured resolved geometry lifecycle. Thumbnail appearance, retained mesh bytes, active motion studies and the newly composed D01 native lifecycle remain independently scoped. [Radial edit and save evidence](ConcentricRadialAssembly2026.md)

The [audit](../../tooling/sw2026/para/concentric/ObserveAssemblyPresentationCaches.py) checks each full archive hash before inspection. It emits structure, sizes and identity digests and leaves every archive intact. It has no new native launches, held-out exposures or writer outputs.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ObserveAssemblyPresentationCaches.py \
  --disclosures /absolute/path/to/Oracle121Takeover \
  --model-module /absolute/path/to/sldmodu.dll \
  --output /tmp/UnusedAssemblyPresentationCaches.json
```
