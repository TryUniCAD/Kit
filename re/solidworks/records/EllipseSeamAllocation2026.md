# Full ellipse endpoint allocation and saved seam

SOLIDWORKS 2026 SP05.2 allocates the ordinary full-ellipse seam before adding the sketch segment. The authoritative direct native API branch identified below seeds the point at the sorted major station. The two disclosed saved sketches place the same semantic endpoint at approximately 17 degrees. The static trace reaches allocation and the handle binding. The later position setter remains open. [Linked archive evidence](EllipseBlindBossArchive2026.md)

## Build and source evidence

| File | Build | SHA-256 |
| --- | --- | --- |
| `sldappu.dll` | 34.5.2.0604 | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` |
| `slduiu.dll` | 34.5.2.0604 | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `sldmodu.dll` | 34.5.2.0604 | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |

The static analysis used exact licensed files outside the checkout. PE export and import names, unwind function boundaries and extracted API record labels bind the addresses. Prefer the symbol where present. All addresses are preferred-image virtual addresses for these hashes. The disclosed observer phase records have SHA-256 `0fb76cbe72a270df7645545dd3eb1102a24447fcd83227726deb400c31f195f4` and `16351d9a59ea3630f0bc17d0d0bc11c9ce5b00e05ce65fbcd515d96b26049a3b`. Both phases read `AddToDB=True` immediately before `ISketchManager.CreateEllipse`, supplied nine numeric arguments and restored the previous setting. [Module manifest](../v2026/Manifest2026.json) · [Native acquisition lock](../measurements/2026/EllipseBlindBossDisclosedLock01.json)

## Exact direct creation branch

| Module and location | Confirmed operation |
| --- | --- |
| `sldappu` `0x456e0ca0` | The exported `auSketchManagerWrapper_c::CreateEllipse` forwards nine doubles and the return slot. Call `0x456e0dd1` uses the inner interface at this +0x50 and vtable slot byte offset 0x150. The target of that indirect call remains unbound. |
| `slduiu` `0x49220d20` | The API record-label operand at `0x49220d5d` names `auModelDoc_c::CreateEllipse2`. It calls `0x49279040` at `0x49220e1b`, whose direct call at `0x492790cc` reaches `auModelDoc_c::iCreateEllipse` at `0x49280c60`. Four separately labelled dispatch entries route to the same helper. |
| `sldappu` `0x456f95d0` and `0x456fba00` | The exported `uiEnvironment_c::getAddToDB` and setter read and write the same 32-bit field at +0x2d8. |
| `slduiu` `0x49280d41` through `0x49280db7` | The AddToDB branch gates the direct `uoSketch::createEllipseH` call at `0x49280db7`. Its two optional endpoint arguments are null. The three explicit point arguments come from the nine coordinates. |
| `slduiu` `0x4a1a3d10` through `0x4a1a3e39` | `uoSketch::createEllipseH` computes the centre-to-axis-point lengths and keeps the longer as major. Both measured shapes already supply the larger semiaxis as major. |
| `slduiu` `0x4a1a3e56` and `0x4a1a3f0f` | First resolves or creates the centre. With optional endpoints absent, copies the effective major point and calls `sgSketch::addNewPoint` with point kind 2 at `0x4a1a3f0f`. The one returned index supplies both endpoints. |
| `slduiu` `0x4a1a3f82`, `0x4a1a3fa1`, `0x4a1a3fea`, `0x4a1a4044` | Allocates the signed major and minor points and their reflected partners. The latter use the centre minus the centre-relative axis vector. |
| `slduiu` `0x4a1a4153` | Calls the imported `sgSketch::addEllipse` at model address `0x4c49b2d0` with the resulting indices. Call `0x4a1a41a8` invokes the ellipse's `makeSelfPermanent` owner at model address `0x4c5755f0`, which records point uses through `sgPointHandle::useForSegment` at `0x4c602c10`. |

The proven creation chain is the current ModelDoc direct API lane. The source observations establish manager entry, AddToDB and the three coordinates. A runtime call trace or verified interface target would establish the connection from the manager's indirect call to the same helper.

## Geometry discrimination

The saved endpoint's actual curve phase is computed from both positive directed axes with dot products. For A and B its distance from the native initializer's sorted major station is 0.0027577727927333121 m and 0.0033781376954739695 m respectively. The one separate kind-2 point and shared indices remain stable on both D1 edits.

The near-17-degree literal at `sldmodu+0x1e45090` (VA `0x4cf85090`) and `slduiu+0x1681048` (VA `0x4a521048`) is 0.29670597283903666 radians. Evaluating the two signed vectors at this phase gives exact A coordinates and B residual 2.1684043449710089e-18 m. All six direct model-module references are circle/arc logic, including the distinct circle branch at `0x4c6fabca` before the same enclosing procedure's ellipse import branch at `0x4c6fae68`. The one UI direct reference at `0x49096e40` feeds `sgArcHandle::findUniquePointOnCircle` at `0x49096e51`. That call follows an arc handle's normal, radius and centre. The literal and numeric match alone leave the ellipse position producer unresolved.

A focused native discriminator can keep the centre, both axis points and AddToDB scope fixed. Read the same internal point identity immediately after drawing if the installed sketch-point API exposes it. Then compare a hash-bound sketch-only save and the corresponding fresh boss save with healthy controls. The first retained snapshot with the displaced row distinguishes allocation, sketch close/solve or subsequent feature/save processing. If the public point interface omits the owned seam row, report its limitation and use the two independently authored snapshot phases. [Numeric typed source receipt](../measurements/2026/EllipseBlindBossArchive01.json)
