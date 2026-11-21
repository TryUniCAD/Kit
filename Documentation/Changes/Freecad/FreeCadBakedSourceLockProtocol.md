# FreeCAD standalone baked source locking

For the [standalone import study](../../../re/solidworks/records/BakedFcstdSourceEligibility2026.md), `CollectBakedBoxes.py` prepares two native FreeCAD sources with one baked rectangular solid each and one live `Part::Box` negative control. The collector uses the A16 bundled Windows Python route. It requires FreeCAD 1.1.4 build `4fd3bf320d9566a27e60069fc8387448aaa3a094` and the previously measured FreeCAD Python module. The paired phases also bind the executable, the actual loaded `FreeCADApp.dll` and the `Part` module. An existing installation's `bin\python.exe` is a required operator input. [Collector](../../../re/FreeCad/Oracle/CollectBakedBoxes.py) · [A16 runtime evidence](FreeCadRectangleVerification.md)

## Write the independent input specification

Use a fresh, private custody directory outside every Git checkout. The source custodian supplies `Spec.json` and freezes its SHA-256 before either authoring phase. Use the following fields. The specimen bounds, labels and measurements stay in custody.

| Field | Value |
| --- | --- |
| `schema` | `kit.freecad.baked-source-spec.v1` |
| `baked` | An array of two independently specified cases, with different lengths and different origins |
| `negative` | One actual parametric box case |
| Case `label` | Nonempty printable text |
| Case `origin_mm` | Three finite signed coordinates |
| Case `size_mm` | Three positive finite lengths |
| Negative `edited_length_mm` | One different positive value for its real `Length` driver |

The collector creates a planar rectangle in memory and extrudes it into a closed solid. It assigns the complete shape to one literal `Part::Feature` with identity placement. The negative instead owns `Length`, `Width` and `Height` on a literal `Part::Box`. The topology check verifies all eight stations, twelve line edges and six planar face trims with two uses per edge. Its independent scalar check uses analytic volume, area, bounds and signed centre with relative tolerance `1e-10` and absolute tolerance `1e-9` in the respective millimetre-derived units.

## Author, close, reopen and lock

Run these commands serially in the existing Windows environment. Set `$fcPython` to the verified bundled `bin\python.exe`, `$collector` to the absolute pinned script path and `$custody` to the existing private directory. Set `$toolHash` to the collector's precommitted SHA-256. The packet subdirectory and both log paths must be unused. Give each native process an external timeout and retain its private log on failure.

```powershell
$packet = Join-Path $custody 'Packet01'
$spec = Join-Path $custody 'Spec.json'
$specHash = (Get-FileHash -LiteralPath $spec -Algorithm SHA256).Hash.ToLowerInvariant()
& $fcPython -I -B $collector author $packet $spec --runtime-python $fcPython --tool-sha256 $toolHash --spec-sha256 $specHash *> (Join-Path $custody 'Author.log')
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD source authoring failed' }
$authorHash = (Get-FileHash -LiteralPath (Join-Path $packet 'NativeAuthor.json') -Algorithm SHA256).Hash.ToLowerInvariant()
& $fcPython -I -B $collector reopen $packet $spec --runtime-python $fcPython --tool-sha256 $toolHash --spec-sha256 $specHash --author-sha256 $authorHash *> (Join-Path $custody 'Reopen.log')
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD source verification failed' }
Get-Content -LiteralPath (Join-Path $packet 'PrewriterSourceLock01.json')
```

The author phase brackets the three native saves with known healthy box controls. After closing each document, it checks the literal `Document.xml` declaration and the sole `Shape` property and hashes that owned archive member. It refuses dependencies, expressions, proxy state and linked source owners. The author receipt is private and records the closed files.

The fresh reopen phase checks the native process chronology and the exact original archives before opening. It observes initial geometry before recompute, confirms the rebuilt geometry, and edits and restores the negative control's real `Length`. It closes without saving and rechecks each original hash. The healthy control bracket must pass again. A successful run creates `PrewriterSourceLock01.json` with only counts, verdicts and hashes. Share that file or its hash and keep the spec, original FCStd files, phase records, native logs and profiles private. Keep failed attempts and start a new packet for a retry.

The collector received host syntax and source checks only. The exact runtime locator and native run remain pending. Source transfer, strict SDK source qualification and SOLIDWORKS output acceptance require later evidence. [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md) · [Source corpus protocol](../../../re/Playbook/GenerativeCorpus.md)
