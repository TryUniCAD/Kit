# Trace the first part solid query after native open

The SOLIDWORKS 2026 research probe can arm one scoped execution stop after a normal cold open, before the first all-visible-and-hidden solid query. It verifies the original CAD images and actual class receivers, then captures the backing array before automation wraps it or the actual arguments to the atom manager.

Use the hash-bound [prism probe](../../../../../re/tooling/sw2026/ProbePrismOpenBoundary.py) with `--cold`, `--continue-after-hit` and either `public_solid_owner_return` or `atom_inventory_call` as the terminal site. The two brackets, each with native controls, measure eight processes. The generated archive opens cleanly and its native backing array is empty. The same-shape native control has one solid. The observation narrows the discovery to the native model and atom path. [Native receipt](../../../../../re/solidworks/measurements/2026/PrismPublicBodyInventoryNative01.json)
