# Observe child and parent rebuild state across assembly open

The [previous rebuild diagnostic](../../../../../re/solidworks/measurements/2026/AssemblyRebuildProbe02.json)
cleared the parent rebuild flag in memory, but warning 32 returned after
saving and reopening the assembly. The new diagnostic opens the exact
referenced part on its own before any rebuild, then checks that same part
and its active configuration through the ordinary assembly occurrence.

The probe records the child and parent rebuild, save and feature problem
states separately. A fresh process is required for the standalone part,
each parent phase and each bracketing control. It refuses a substituted
or suppressed child and never overwrites the inputs. The new native
measurement remains pending. These observations can distinguish a reported
child rebuild from the parent state but cannot by themselves identify the
native stale-reference branch.
