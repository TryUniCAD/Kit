# A motion controller points to its own study

## Expectation

The controller’s first stored word represents independent metadata.

## Observed behavior

The embedded controller's first stored object reference resolves to its own `moAnimKeyData_c` study in the manager's archive map. The measured direct case assigns slot four to that study. [Field record](../../../../../re/solidworks/records/D01AssemblyMotion2026.md)

## Workaround

Bind the controller to the actual study object and let the shared archive map assign its reference tag. Require the same object on typed readback.
