# Completed local imports can warn with empty lighting

On SOLIDWORKS 2026 SP05.2, the four completed local import probes with
an empty environment open with warning 32 despite having their expected
solids. The completed update state, typed imported feature and body
identity remain present. The independent controls open cleanly.

Keep the empty-lighting profile outside native writer qualification until it
also passes clean open, rebuild, save and fresh reopen. Measure any
lighting change with identical inputs and locators, including a trailing
control.
[Native warning receipt](../../../../../../re/solidworks/measurements/2026/GeneratedLocalImportWithoutLight01.json)

At the same logical paths, an explicit ambient light clears warning 32
for all four measured parts. Geometry and rollback streams stay identical.
The ordinary default-light construction still needs qualification.
[Same-locator contrast](../../../../../../re/solidworks/measurements/2026/GeneratedLocalImportLightingContrast01.json)
