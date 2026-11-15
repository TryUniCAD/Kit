# Derive configuration progress from the generated history

The research composer now records the active configuration's highest processed
persistent ID after constructing its history and live parameters. The shared
operation computes `allocator.next_id - 1`, matching the native header getter
and completed-update assignments.

Leaving the constructor's initial zero allowed the loader's new-feature branch
to apply default suppression to the generated sketch and extrusion. Their
constructor state and the configuration's default suppression flag remain
unchanged. The [native rule and field classification](../../../re/solidworks/records/ConfigurationProgress2026.md)
distinguish progress from unfinished explicit override persistence.

The complete-file process harness now decodes both independently stored streams
and checks their progress relationship. Checks run only in remote PR CI.
Remote validation and controlled native measurements of this repair remain
pending; production writing and native generated-output acceptance remain disabled.
