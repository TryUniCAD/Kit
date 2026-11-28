# Oblique-cylinder mass precision diagnostic

PR #121 adds a small source-only diagnostic for the two frozen disclosed oblique-cylinder constructions. It retains the original geometry, default mass observations, failed analytic comparisons and tolerances, then collects exact registered document mass results at accuracy 0/1/2 with the real output status and before/after measurements of the actual sole body.

Use `InspectObliqueMass.py prepare` with the frozen flip packet, exact registered mass metadata and an unused external output. The emitted recipe runs a pristine before control, both disclosed constructions and a pristine after control in four fresh applications. Both new APIs must qualify on the first control before candidate measurement. Root alone executes native commands; host verification performs no COM calls.

Two host verifies passed and three independently modified packet copies were refused. Sixteen original tools and the geometry/prediction/control/API inputs are unchanged. No native process, writer output or hidden input was used in preparing this diagnostic. It performs no save or edit and does not qualify conversion, substitute a higher-accuracy result or establish mass precision before the controlled run.

See the [binding, custody and commands](../../../../../re/solidworks/records/ObliqueCylinderMassPrecisionProtocol2026.md) and [middle-output invocation gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Primitives/MassStatusOutputPrecedesUseSelected.md).
