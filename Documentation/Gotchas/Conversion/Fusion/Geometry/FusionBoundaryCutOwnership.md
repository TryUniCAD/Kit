# Fusion boundary cut ownership

A modifying extrusion does not necessarily list its resulting solid in `dcBodies`. In the captured rectangular cuts this list is empty. Its `targetDataRefs` instead resolves through `ModelDataRef.dataRefs` to `DRBody.refBodies`, identifying the original create extrusion body. Treating an empty list as no solid loses the target dependency.

The existing planar journal reader also requires a convex shell and convex face rings. A corner cut produces a valid concave shell and its top and bottom rings can be concave. The native reader refusal is a qualification boundary, not evidence of corrupt source geometry. Do not suppress it or promote partial output.

The research [boundary cut evidence](../../../../../re/Fusion/Reconstruction/BoundaryCuts/Findings.md) records distinct journal states, target joins and independent native measurements. The research inspector measures these boundaries without claiming complete strict neutral semantics or polygon validity. A production implementation must validate both the live feature dependencies and nonconvex topology.
