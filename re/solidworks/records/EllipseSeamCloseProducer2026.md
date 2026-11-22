# Full ellipse seam during sketch close

On SOLIDWORKS 2026 SP05.2, both disclosed author phases called `ISketchManager.InsertSketch(True)` to enter and exit the sketch. The live COM point ID `(1, 1)` retained its identity as it moved from the major station to 17° in both phases. The typed archive identifies the corresponding kind-2 seam by the wire handle `(0, 1)` and ordinal 1. A live ID and an archive handle belong to separate identity spaces. The recorded transition brackets restoration of `AddToDB`, the close, and retrieval and naming of the resulting sketch. [Native disposition](../measurements/2026/EllipseSeamNativeDisposition01.json) · [Frozen author](../../tooling/sw2026/ellipse_source/EllipseSeamAuthor.py)

## Build-bound dispatch

Addresses below are preferred-image virtual addresses for the four exact x64 images in the receipt. PE imports, the interface IID and map, C++ RTTI, vtable cells, and bounded instruction assertions independently bind the typed dispatch. The images stay outside Git. [Static receipt](../measurements/2026/EllipseSeamCloseProducer01.json)

| Owner and site | Meaning |
|---|---|
| `sldappu:0x456df3c6`, `0x456e3ea7` | The public wrapper obtains the inner `ISketchManager` by IID `9ce9dace-e595-4d8f-b893-5ae4899517de`. Its ordinary branch loads the queried subobject at wrapper offset `0x50` and calls virtual slot `0x108` with the caller's Boolean. |
| `sldapiu:0x432a7c58`, `0x42eaf1c1`, `0x42eba200` | The same IID selects the actual `auSketchManager_c::XDispatch` subobject at `+0x70`. Its constructor installs vtable `0x432a7cf0`, whose slot `0x108` is `0x42eba200`. That entry converts the input to zero or one and calls `0x42ec24a0`. |
| `sldapiu:0x42ec2515`, `slduiu:0x49cc043c` | The adapter calls `uiModelDoc_c::OnInsertSketch2(UpdateEditRebuild, 1)` on the held document. The ordinary UI command path passes the same Boolean to `uiModelDoc_c::insertSketch` at `0x49cc7c30`. |
| `slduiu:0x49cc7efb`, `0x49cc7f33`, `0x49cc803d` | The active branch obtains the actual sketch and profile and calls `sgSketch::cleanOutUnusedSketchMidPoints` for a 2D sketch before the update Boolean is tested. |
| `slduiu:0x49cc80d3–0x49cc80d8`, `0x49cc8282`, `0x49cc8830` | The test of the original Boolean sends zero to `0x49cc8664`, a distinct path containing `setSketchInProgr(nullptr, …)` at `0x49cc8830`. The nonzero branch contains the closing update helper at `0x49cc63c0`, called from `0x49cc8282`. |
| `slduiu:0x49cc65d4`, `sldmodu:0x4c0e6670`, `0x4c0dccda` | The helper has a guarded `moProfileFeature_c` virtual call through slot `0x138`. The concrete slot has a local profile update alternative via `0x4c0dc6b0` and its call to `sgSketch::update` at `0x4c0dccda`. |
| `slduiu:0x49cc6767`, `sldmodu:0x4c1d2940` | A separate guarded `moPart_c` virtual update at the same slot offset provides a distinct model-level path. The updating helper also clears the active sketch at `0x49cc6918`. |

The `uiEnvironment_c::setAddToDB` leaf at `sldappu:0x456fba00` only writes the 32-bit environment field at `+0x2d8`. The disclosed author did no seam read immediately after restoration. The static update paths do not yet identify the first write to the kind-2 point, or the dependency that produces its phase. The previously identified literal references for circular geometry leave this ellipse rule unproved. [Allocation and literal analysis](EllipseSeamAllocation2026.md)

## Smallest next native discriminator

Use two fresh parts with the same disclosed Front ellipse and the same open `InsertSketch(True)`, template, selection, and `AddToDB` lifecycle. Read the seam after drawing and after restoring the flag. Verify the registered Boolean signature and vary only the close argument. Observe `ActiveSketch` and read the same owner through the retained profile immediately after each close, before rename, save, or explicit rebuild. Check both point getters, actual live point ID, the full point inventory, and unchanged centre and axes. If a False close actually exits and retains the major station, run a separately recorded clean rebuild and read the same point again. If False exits and already moves the point, inspect the shared close work and the no-update branch. A still-active False result is a reported branch outcome. Use independent healthy before and after controls on the exact build. This experiment isolates the Boolean-dependent update window while leaving the exact setter and generalized placement rule as separate questions.

## Replay

Run from the checkout with the explicitly disclosed author receipts and exact installed images outside Git. The command emits only the bounded evidence, digests, and locations. It runs the host disassembler and does not start SOLIDWORKS.

```sh
python3 -B re/tooling/sw2026/ellipse_source/InspectEllipseSeamClose.py \
    --bin /Users/odin/Documents/UniCAD/Sw2026Research01a1dc84/bin \
    --capture /Users/odin/Documents/UniCAD/Oracle121Takeover/EllipseSeamDiscriminator01/DisclosedCapture \
    --objdump /Library/Developer/CommandLineTools/usr/bin/llvm-objdump
```

REA's separate PE resource snapshots checked the original files for `sldappu` (`ev_403c0dd249158467173a9763e5e62a3fd7ccde3527d4c6266c2b800f2363c32a`), `sldapiu` (`ev_6b008bcd5a372a0b81de616a53ac2430cfb90aac54c6a95cdcd623c778dfcc01`), and `slduiu` (`ev_a27008b4457ddf45f2ace7524b7a394f400a6ec5839530913c2453c3d4316f08`). These snapshots establish image identity. The local replay verifies the code paths from the pinned images. The result adds zero native lifecycles and zero writer outputs. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Loader analysis procedure](../../Playbook/LoaderAnalysis.md)
