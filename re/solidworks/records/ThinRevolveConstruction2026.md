# Model-only thin boss construction probe

This disclosure trial generates cold version-19000 SOLIDWORKS parts from explicit neutral thin boss inputs. It uses the [four disclosed SP05.2 source modes](ThinRevolveWireOwners2026.md). The construction revision descends from the [independent pre-writer source lock](../measurements/2026/RevolveThinHeldoutSourceLock01.json), commit `35c607164409bff6fe2222358ac1e8b6da981782` and SHA-256 `e81db7caf2db600543f6f85b61b3a47a27cfd4b670f8e6a55f45dc79e6637653`. The jobs here use disclosed discovery inputs exclusively.

The planner takes one Front-plane open body line, its separate selected upward axis, one positive single-direction partial angle, and the explicitly selected wall mode. It derives the angular owner from the neutral feature and uses a distinct feature-owned length for each active wall. The width stage creates D3 and the physically retained D4 chain, with D4 zero and spatial placement absent for the first-side, opposite-side and symmetric modes. For an active wall, the inverse display frame follows its signed endpoints and the profile midpoint. The mid-plane wall stores the whole D3 thickness and places half on each side. The external wall mode is an explicit research input. No portable interchange feature or normal adapter action is registered.

The probe reuses the common part, open sketch entity, angular end, linear display, header, manager, history, definition, keyword and compound-container constructors. It emits `Revolve-Thin` keyword rows in the observed D3/D1 or D1/D4/D3 order. Model width and angle determine the actual dimension caches and XML values. It computes native archive object identities and explicitly connects the two endpoints of each line. The open body line's `0x40` state is bound to the measured source shape. The broader native producer and other open-profile states remain unclassified.

The cold experiment uses the native thin-spec initializer `-2.0` for the inactive end-thickness field. It omits the post-edit radius display, saved body atom and saved face-ID inventory. Their absence is an explicit trial condition that needs a clean native cold open and comparison. No saved bytes or donor computations participate in construction. [Thin end thickness lifecycle](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/ThinEndThicknessInitializer.md).

## Guarded host construction

The [builder](../../tooling/sw2026/revolve/ThinArchive/BuildThinControls.py) constructs each file twice in a separate process under an external-access guard. It requires deterministic bytes, actual selected-axis incidence, active wall values, correct keyword order, and exact re-emission of all ten constructed streams. A separate rebuild from an edited neutral wall changes the resolved and keyword streams. The suppressed-profile contrast must refuse before publication. Candidate files remain in an external output directory. The generated receipt pins the clean writer commit, `src` tree, pre-writer lock, tools and resulting files.

```sh
python3.14 -B re/tooling/sw2026/revolve/ThinArchive/BuildThinControls.py \
  --spec re/solidworks/v2026/corpus/revolve-family-models/RevolveThinDiscovery.json \
  --output /absolute/path/to/new/Candidates \
  --guest 'C:\KitThinGenerated01\Candidates'
```

## Disclosed native measurement

The [staging tool](../../tooling/sw2026/revolve/ThinArchive/StageThinNative.py) locks the four generated files, four independently authored original sources, eight native reference phase JSON files, known full-revolve bracket control, and the exact Python observer closure. It checks their revision and file digests before copying research inputs to a new external directory.

The [Windows runner](../../tooling/sw2026/revolve/ThinArchive/RunThinNative.py) launches each phase with the existing SOLIDWORKS 2026 SP05.2 source observer, using registered angular and length roles. In a successful run, eighteen distinct processes run the opening control, four same-mode source and candidate pairs with separate original and edited fresh opens, and the closing control. It checks the complete recursive feature tree, actual profile and axis, D1 and each active wall before and after its own edit, body and topology identities, and volume, area, centre of mass, and bounds to six significant figures. It verifies each new source measurement against the pinned original native phase before comparing the candidate to that same-mode source. A failed candidate keeps its observed phase and refusal in the result. The candidate checks require a zero-warning cold open with one body.

The oracle owner copies the complete frozen packet to its exact local Windows locator and calls the runner from Python 3.12 with the job SHA-256 returned by staging. The research build and observer scripts in this change do not start CAD from the host. The paired run supplies disclosed candidate evidence only. Public admission and held-out evaluation remain separate.
