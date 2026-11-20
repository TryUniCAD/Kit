# Author independently shaped imported feature controls

The [topology cohort](../../../../../re/tooling/sw2026/imported_body_source/README.md#use-the-results)
uses the exact SOLIDWORKS 2026 SP05.2 modeler to author two ordinary BaseBody
sources with differently positioned cylinders. Its observer checks the
measured radius, axis, two caps, cylinder wall, body properties and actual
owning feature before save and in a fresh read-only native process.

The controlled comparison tests model geometry and archive ownership.
Native writer verification remains a separate requirement. The topology
cohort has not completed its first native run.
