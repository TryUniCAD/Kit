# Neutral input for a scoped oblique linear pattern

Task `B04-SW2026-LOCAL-LINEAR-PATTERN` under PR #121. This research proof projects an ordinary typed `CadDocument` into the exact corrected model-only compiler at `d644ff7beb6b61a147a3b5de82ba5614efb155c8`. Its two disclosed originals and the independently changed pitch and count arms produce the same ten stream digests, nine exact typed stream replays, native identities and geometry as the prior modeled requests. Both original containers are byte-exact. The [guarded receipt](../measurements/2026/LocalLinearPatternNeutralInput01.json) reports twenty isolated processes, twelve neutral refusals and zero runtime input reads or imported CAD application modules in successful processes.

## Owned inputs

| Intent | Neutral representation and validation |
| --- | --- |
| Plate and raised seed | Two sketches with an explicit four-line closed loop, the actual Front support and four matching unary axis relations. Each forward blind extrusion owns its distinct editable D1. The plate creates a solid. The seed joins the selected historical plate body. |
| Finite hinge | Research-only `PlaneIntersectionAxis(FeatureDef)` with two ordered support selection IDs and checked start and end in millimetres. The actual Top and Right planes determine the line. The prior joined stock determines its finite trim through the [first-plane rule](LocalLinearPatternFiniteHinge2026.md). The emitted coordinates come from this calculation, which must agree with the presented endpoints. |
| Angled datum | Existing `BoundConstructionPlane` and two typed local selections identify the actual Right base and preceding hinge. The feature owns a live D1 in radians plus a derived zero-offset invariant. The output support's frame must agree with that live angle at the selected base. |
| Feature pattern | Existing `LinearPattern` with two owned live parameters. D1 is an integer count and D3 is a typed positive length. The feature depends on its actual seed and local angled-plane feature. Its selections preserve the actual current joined seed body and the direction support. The single reversal flag signs the actual support normal. |
| Final body | One implicit named body at the actual pattern result. Supplied counted topology must agree with the joined stock and disjoint interior occurrences. The cold part regenerates the solid from the features. |

The ordinary registry has no typed reference-axis feature that can express a directed finite two-plane intersection. A native feature record, a free sketch line or an undifferentiated reference step loses the two selected support roles. The smallest scoped geometry addition is the finite axis feature definition above, plus exact validation of the existing ordered selection edges. The successor angled plane reuses the existing neutral angle and support-frame contract. The isolated process registers the new type only for this experiment. The same neutral wire refuses when the finite axis type is unregistered.

Both disclosed cases also author dimension presentation. The ordinary part model lacks a document annotation-view catalog and angle leader choice. A typed export input binds the angle display, pattern count and pitch presentation to the actual live parameter IDs. It preserves the ordered annotation catalog and each requested inactive slot style. Standard `SelfFileInput` holds the native self locator and event. Existing document metadata supplies the authored part name. A full public source bridge must either represent these owned options or refuse input requiring them.

The profile requires a positive acute angle, both canonical fixed supports, nonoverlapping raised footprints strictly inside the origin plate, and one selected local seed. It rejects mismatched finite trim and frames, an open sketch, a missing or crossed owner, conflicting live count, presentation bound to another driver, an inconsistent final body, and an attempted metadata replacement for the missing axis type.

## Shared preparation

The internal [planner](../../../src/convert/adapters/solidworks/Core/Preparation/Patterns/PlanLinPattern.py) accepts a complete `CadDocument`, explicit `SelfFileInput` and typed [authored presentation](../../../src/convert/adapters/solidworks/Archive/Construction/Patterns/Input/PatPresentInput.py). Ordinary document validation and the scoped reader resolve the actual Front profiles, stock selection, ordered Top and Right hinge picks, Right angle support and local pattern direction and seed. The live values remain the two blind depths, angle D1, integer count D1 and spacing D3. The angle has its actual derived zero offset. The sole final body must name the final joined pattern and any supplied topology must match the ordinary counted result.

The planner reads the registered portable `PlaneAxis` directly. The existing wire tag belongs to that type, while the frozen historical research proof retains its old locally registered prototype. [Portable type boundary](PortablePlaneIntersectionAxis2026.md) · [Registry gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/PortableAxisOwnsLegacyWireTag.md)

The [archive input](../../../src/convert/adapters/solidworks/Archive/Construction/Patterns/Input/LinPatternInput.py) carries both stock boxes, the hinge label, angle intent, ordered annotation catalog, active and shown choices, pattern name, signed direction, count and pitch, and all six explicit display styles. The three supplied presentation IDs must match the real parameter owners. A canonical Back view anchors the angle and count. The standard pitch annotation remains unassigned, with its proven zero text point.

The planner checks that the base plate and seed form the measured two-box profile and that the finite hinge follows the joined stock's first-plane bounds. The downstream shared geometry must still verify containment and separation of all repeated footprints before emitting a complete part. This preparation adds no public write route, native run or held-out credit.

The [shared projection proof](../../tooling/sw2026/linear_pattern/neutral/ProveSharedPatternPlan.py) uses only the two independently authored disclosed recipes and their separate pitch and count changes. Each isolated worker decodes the regular portable document, builds the typed result under the no-read guard and verifies that the document wire remains intact. The parent compares every recipe field to the frozen disclosed model. The authored integer zeros at the first origin corner are represented as metre floats. The original file digests serve as outside construction evidence.

The [recorded receipt](../measurements/2026/SharedLinearPatternPlan01.json) has SHA-256 `edb8f7b9905eb8edd42195a4fc5741b2cf52a2588d3b423b0de1bf57ccdd64d3`. Six new guarded process runs matched the two original recipes and both separately edited inputs per design with zero runtime reads. Sixteen further isolated processes refused missing or mismatched hinge ownership, a crossed seed, an open outline, inconsistent depth-independent pattern controls, wrong output or configuration, contradictory final topology and misattached presentation. The frozen historical proof remains unchanged.

```sh
pattern_proof="$(mktemp -d)"
uv run --no-project --offline --python 3.14 --with pefile --with capstone python -I -B \
  re/tooling/sw2026/linear_pattern/neutral/ProveSharedPatternPlan.py \
  --disclosed /absolute/path/to/GeneratedLocalPatternNative02 \
  --output "$pattern_proof/Receipt.json"
```

## Reproduce

The command below belongs to the original frozen research codec revision named above.

```sh
pattern_proof="$(mktemp -d)"
python3.14 -I -B re/tooling/sw2026/linear_pattern/neutral/ProveNeutralPattern.py \
  --disclosed /absolute/path/to/GeneratedLocalPatternNative02 \
  --output "$pattern_proof/Receipt.json"
```

The supervisor builds both neutral documents from the original independent model recipes and reads the corrected disclosed packet as comparison evidence. The child receives only the typed wire model, output identity and presentation over stdin. It preloads ordinary model-validation modules before the construction audit closes file access, round-trips the neutral schema, validates the owned graph and uses the unchanged generative emitter. The supervisor checks the result's exact streams and linked objects against the pinned model receipt. It opens the two disclosed comparison containers only after producing each candidate transport. Every scope limitation remains in force. The earlier native D3 lifecycles are comparison evidence for those two original containers. This proof adds zero native lifecycles, zero held-out credit and no public adapter registration.
