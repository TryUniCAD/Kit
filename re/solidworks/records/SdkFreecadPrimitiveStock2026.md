# Editable FreeCAD box stock from actual source owners

This is `B04-SW2026-FCSTD/primitive-stock`, owned by `/root/release_path` for PR #121. The scope uses the strict FreeCAD reader, shared origin-fixed SOLIDWORKS box constructor and linked ordinary part reader. The exit for this intermediate step is guarded construction and strict readback of a selected original stock primitive. Whole-source transfer still requires the complete consuming history, presentation, references and SOLIDWORKS lifecycle for the emitted file. [Host receipt](../measurements/2026/SdkFreecadPrimitiveStock01.json)

The exact disclosed inventory identifies C077-P01, C114-P01 and C151-P01 by independent FCStd hashes. Each contains an independently editable, origin-fixed `Part::Box`. The probe reads the original `Document.xml` owner and its own retained `Shape` member. The decoded solids have eight corners, twelve distinct line carriers, six plane carriers with ordered outer rings and twenty-four coedges. The same incidence is present in the separately generated SDK model. Source OCCT pcurves and explicit identity locations are used as corroborating geometry; they remain in the original bytes. The target sketch, dimensions, feature graph and streams are built from the three dimensional inputs.

| Disclosed stock owner | Literal feature and body label | Length × Width × Height (mm) | Generated SHA-256 prefix |
| --- | --- | --- | --- |
| C077-P01 `Box` | `Cube` | 10 × 10 × 10 | `ec9af7d7345e` |
| C114-P01 `Box` | `Cube` | 400 × 300 × 4 | `f1473afe52e1` |
| C151-P01 `Box` | `120x400x5` | 120 × 400 × 5 | `68e0d931c26c` |

The original parameter IDs and their literal aliases survive preparation. Strict target reads resolve Length and Width to the real sketch and Height to its boss. The ten physical streams have a complete linked readback, including the actual Header self-file alias. Full strict read recovers the exact body label, solid, geometric measures and the creating operation. Design-only read preserves the same drivers, body-to-feature link and tree. The existing design-only behavior reports the `Solid Bodies` folder label and generic join operation for this geometry-free read.

Each case runs twice in a fresh guarded process. The selected source read is isolated, the source bytes and neutral document are checked again, and later file access is refused. The output is retained in memory. Altered source aliases, missing shape ownership and selection of the actual consuming feature refuse. The two translated conditions refuse before construction. Both public APIs refuse the intact documents and all three selected-stock projections without changing the caller's stream.

For C077-P01 the original cut owns `Box` and `Cylinder`. The tool starts at `(5, 5, 5)` mm and has its own 10 mm Height. Preserving its blind tool placement and live height requires a separate target graph. C114-P01 selects all twelve original cube edges at 1 mm on both sides, outside the measured single-edge chamfer. C151-P01 includes a second, translated physical `Part::Box` and retains its distinct alias and 5 mm actual height. The separately disclosed 1.1.4 live primitive has nonzero translation on all three axes. [Translated source gotcha](../../../Documentation/Gotchas/Conversion/Freecad/Primitives/BoxStockUsesActualPlacement.md)

Rerun the host proof with the existing disclosed custody manifest and translated control. It emits only digest-bound observations and counts.

```sh
python3.14 -I -B re/tooling/sw2026/freecad_census/primitive_stock/ProveSourceStock.py \
  --inventory /absolute/path/PublicFcstdWriterCensus01/VerifiedInputs01.json \
  --offset-control /absolute/path/FreeCADRuntime114/DisclosedSources01/ParametricControl.FCStd
```

The new candidates carry no native or held-out qualification and add zero FCStd corpus conversion credit. Two independent qualifying native histories are still required before any publication change. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
