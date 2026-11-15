# Environment configuration does not establish fixture path containment

An absolute `KIT_RESEARCH_CHECKOUT` value can appear sufficient for trusted CI fixture access.
The security analysis still follows that environment value into filesystem reads, including SDK fingerprints, corpus manifests, and runner lookup.
The failed merge candidate reported seven such paths.

CI already provisions the pinned checkout at the fixed `ResearchCheckout` directory beneath this repository.
Derive that fixture root from the checked-in module location, require the environment value to resolve to it, and reject a symlinked checkout before reading its contents.
The production developer CLI continues to accept an arbitrary explicitly trusted checkout through `--root`.

See [the failed Python security job](https://github.com/TryUniCAD/Kit/actions/runs/43713089501/job/132808725145) and [the boundary change](../../../Changes/Commands/ResearchRuntimeBoundary.md).
