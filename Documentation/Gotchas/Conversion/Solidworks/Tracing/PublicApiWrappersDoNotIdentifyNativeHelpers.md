# Public API wrappers do not identify native construction helpers

## Expectation

An exported `CreateCircleByRadius` method establishes which internal circle-construction helper a COM authoring call uses.

## Actual behavior

The pinned application export at `0x456e0600` forwards through an interface at wrapper `+0x50` and virtual slot `+0x130`. Interception callbacks run before the target is selected. Reading a receiver at wrapper entry or assuming a helper from the public method name does not establish the actual indirect call target.

## Workaround

Bind the complete wrapper and the exact call instruction. Observe its actual receiver and target registers after interception callbacks, compare them to the live wrapper/interface fields, and retain the target module and relative address. An interior callback must use register provenance from that instruction; a function-entry return-address convention is not assumed there. Independently inspect the selected implementation before deriving its geometry or marker-placement rules.

The [dispatch probe entry](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksCircleApiDispatchProbe.md) records the new bounded observation and its pending native verification. It supplies no whole-helper proof or generated-output acceptance.
