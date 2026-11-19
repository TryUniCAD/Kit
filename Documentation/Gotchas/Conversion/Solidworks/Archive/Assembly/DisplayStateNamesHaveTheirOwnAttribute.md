# Display-state names have their own attribute

Assembly model and configuration rows use `swName`. The disclosed SOLIDWORKS 2026 `swDisplayState` rows use `swDisplayStateName`. Reading the same attribute as the model produced an empty label while the raw attributes retained `Display State-1`.

Use the display-state attribute when it is present. Retain support for files that store the label in `swName`. Read the original attributes alongside the label when inspecting additional state. [Disclosed root audit](../../../../../../re/solidworks/records/ConcentricParentRootAudit2026.md)
