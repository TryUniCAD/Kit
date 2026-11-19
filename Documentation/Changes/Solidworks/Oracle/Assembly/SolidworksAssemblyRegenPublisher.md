# Ordinary assembly regeneration-warning source map

PR #121 adds an independently pinned source map for the ordinary SOLIDWORKS 2026 assembly regeneration-warning publisher. It distinguishes the actual assembly configure helper from the existing part and shared-policy publishers, records the actual configuration/mate update query, and joins the concrete assembly document to the shared conditional post-load lighting route.

Use [the source record](../../../../../re/solidworks/records/AssemblyNeedsRegen2026.md) and its linked numeric evidence when selecting a read-only observation. Reproduce original-image verification with `re/tooling/sw2026/InspectPartEnvironmentSource.py --bin-directory <licensed-original-directory> --record <AssemblyNeedsRegen2026.json> --output <unused-receipt>`.

The source replay verifies 12 complete functions, 12 instruction windows, 12 data windows, three imports and 12 virtual cells across three original pinned modules. No vendor listing or software is included. No VM, CAD, COM, tests, held-out access, writer change or target-application acceptance is added. Neither lights nor unsolved mates are assigned as the cause of a particular generated warning without the actual runtime receiver/caller join. [Publisher ownership gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Assembly/Opening/AssemblyRegenWarningNeedsActualPublisher.md)
