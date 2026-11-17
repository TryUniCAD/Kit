# Author and lock native nested assembly sources

This PR #121 B04-SW2026 source cohort owns the first ordinary resolved SOLIDWORKS 2026 subassembly ground truth. The current native synchronized and planar mate cohorts contain direct part references. The locked public FreeCAD assembly is a separate source format. The nested lock requires two unrelated disclosed native cases and two private held-out cases before writer construction. [Conversion register](../../../Documentation/Maintenance/ConversionBacklog.md#b04-sw2026-solidworks-2026-native-reading-and-writing) · [Public FreeCAD source](PublicAssemblyAcceptance2026.md) · [Pinned subassembly branch evidence](NestedAssemblyReferenceState2026.md)

## Authoring contract

Use `kit.sw2026.nested-assembly-source-specs.v1` with two discovery cases beginning `N01` and `N02` and a separate two-case held-out specification beginning `N03` and `N04`. Each case supplies a name, split, one to three `parts` with `name` and `depth_m`, two to four `assemblies` ordered from dependencies to root, and an `edit` with a leaf part name and changed `depth_m`. Each assembly supplies a name and `occurrences`. An occurrence supplies a prior definition's `target` and a `placement` with principal `axis`, `angle_deg` and `translation_m`. The last assembly is the root. Names are unique within the case. All definitions participate in its acyclic graph, with at most twelve expanded occurrences. [`NestedAssemblySourcePlan.py`](../../tooling/sw2026/NestedAssemblySourcePlan.py)

The first disclosed case places one independently depth-authored prism in a rotated subassembly, then places that subassembly with a noncommuting rotation. It has two expanded occurrences and one body. The second has one direct leaf and two placements of a shared subassembly containing two leaves. It has seven expanded occurrences and five bodies. A single edit of the shared leaf definition changes all four resolved instances of that leaf. The analytic volume predictions are `6.696e-6 → 1.1128e-5 m³` and `4.2248e-5 → 6.036e-5 m³` respectively. The source setup derives the local XY dimensions from the hash-locked native `40 × 20 mm` centered rectangle control and authors each depth with the vendor API. These operations belong to the source oracle.

Freeze the disclosed specification, opaque held-out specification and pinned native part seed with `NestedAssemblySourcePlan.py`. Supply their absolute paths, an unused private deck path and both specification hashes. The freezer stages immutable copies of the inputs and all tool files, then launches the frozen author in `--verify-only` mode on the host. This mode validates the disclosed cases and file hashes. Held-out designs remain with the oracle owner. The guest validates both specifications before launching SOLIDWORKS. [Pinned control and build provenance](../v2026/heldout/AssemblyPlanarMateSourceLock01.json)

## Native source measurement

Through the sole oracle owner's existing serialized transport, run the frozen `Tools/AuthorNestedAssemblySources.py` with `Deck.json` and `--deck-sha256`. A passing batch uses ten fresh SOLIDWORKS processes. Two known native part measurements bracket four pairs of author and reopen sessions. The guest authors one file per definition and inserts both parts and subassemblies with explicit `AddComponents3` transforms. It records each definition while active. The root observation walks `GetRootComponent3` and `GetChildren` recursively. The observer matches each immediate child by exact underlying file identity and the independently composed world transform. Sibling enumeration order from COM is unnecessary. [Native author and observer](../../tooling/sw2026/AuthorNestedAssemblySources.py) · [Root-context transform](https://help.solidworks.com/2019/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IComponent2~Transform2.html) · [Direct child traversal](https://help.solidworks.com/2023/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IComponent2~GetChildren.html)

With row-vector transforms the composed basis is `R_local × R_parent`, and the world origin is `t_local × R_parent + t_parent`. The independent model weights transformed leaf centroids by their volumes. The observer counts each visible leaf body, checks per-document mass properties and native feature trees, and reads the three driving dimensions of every part.

After the temporary depth edit, rebuild the leaf and its owners, measure the new root geometry, restore the original depth, and measure once more. Save the parts, subassemblies and root in dependency order. Require clean save statuses and preserve the persisted dependency hashes and update stamps across each owner save. The fresh read-only process opens the root without preloading siblings and measures the exact bound hierarchy, its native tree, persisted stamps, transforms and geometry before and after rebuild. The temporary edited state is observed in memory. Fresh reopen validates the restored, synchronized source.

Store native artifacts, full call logs and observations only in the private deck's `Results` area. Publish the exact deck and tool hashes, bracket status and the sanitized source lock. The held-out rows carry the hashes of their private records and the complete artifact manifest. Their topology, placements and detailed observations stay sealed. The authoring cohort records zero generated writer outputs and supplies source-lock evidence only.

Host-only preflight validated both disclosed designs and the immutable tool and file binding with a disposable opaque slot. The native cohort and its source lock await the oracle owner's run.

## First run and disclosed replay

The first long transport ended before a full source lock. Both disclosed
authors had saved their dependent file sets. Their original reopen
observers rejected the indexed loading window. The corrected read-only
replay checked the same source hashes and measured two clean reopens and
rebuilds between healthy brackets. The first run's failed status remains
recorded. [Disclosed replay receipt](../measurements/2026/NestedAssemblyDisclosedReplayNative01.json)

The sealed source phases now run independently. The remaining holdout
locks require author, read-only reopen and both controls for each slot.
[Sealed phase procedure](SealedNestedAssemblySourcePhases2026.md)
