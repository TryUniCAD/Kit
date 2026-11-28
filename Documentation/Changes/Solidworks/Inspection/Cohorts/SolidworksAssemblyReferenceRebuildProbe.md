# Observe child and parent rebuild state across assembly open

The [previous rebuild diagnostic](../../../../../re/solidworks/measurements/2026/AssemblyRebuildProbe02.json)
cleared the parent rebuild flag in memory, but warning 32 returned after
saving and reopening the assembly. The new diagnostic opens the exact
referenced part on its own before any rebuild, then checks that same part
and its active configuration through the ordinary assembly occurrence.

The probe records the child and parent rebuild, save and feature problem
states separately. A fresh process is required for the standalone part,
each parent phase and each bracketing control. It refuses a substituted
or suppressed child and never overwrites the inputs. The [native receipt](../../../../../re/solidworks/measurements/2026/AssemblyReferenceProbe03.json)
records six fresh processes, two healthy controls and unchanged licensing
processes. The child reports `NeedsRebuild2=0` alone and in all three parent
reopens. Each parent reports `NeedsRebuild2=1` with open warning 32. This
distinguishes the reported child rebuild state from the parent, without
identifying the stale-reference or warning origin.
