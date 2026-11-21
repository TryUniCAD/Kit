# Compose the initial assembly root from shared model fields

The assembly research builder now creates an actual `moAssembly_c` root with
its own unit component and relation manager. It uses the shared model fields,
the initial assembly collection state and the named constructor's defaults
from the [2026 trace](../../../../../re/solidworks/records/AssemblyInitialRoot2026.md).
An empty graph omits both unset bounding boxes. Fresh parts still require
their own analysis unit table.

The remote process check builds two independent roots from different authored
names, writes an in-memory configuration and its header, decodes both through
the container boundary and checks byte identity, map handoff and ownership.
It denies runtime file access. Both root constructions passed the
[remote native-format job](https://github.com/TryUniCAD/Kit/actions/runs/44003713961/job/133773791525)
on `f836b2bc2`; the longer name increased the serialized root length. The
same revision separately failed a test-variable naming check. The corrected
revision `45832385b` passed the [format job](https://github.com/TryUniCAD/Kit/actions/runs/44004721451/job/133777138543)
and every runnable CI check. These bounded archives are not complete
SOLIDWORKS assemblies and do not change the public adapter.
