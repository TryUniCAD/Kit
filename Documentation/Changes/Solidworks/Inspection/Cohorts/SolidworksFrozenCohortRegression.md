# Historical SOLIDWORKS cohort regression

## Behavior

The completed circle, end-condition and orthographic-camera cohorts now keep their
historical source in a separate temporary directory during remote process checks.
The directory contains 3,404 explicitly listed source files from
`f5953529e2114b5648cfe1e5341a83b1c2f0d9d6`. Every file must match its Git object,
byte length and SHA-256 before execution. No native document or saved stream is
restored. The original freeze and source-lock JSON files remain unchanged.

Each of the eight cases runs through both the current writer and the historical
writer in separate interpreters. Historical output must match the original
measured file hash and length. Current output must equal that historical output
byte for byte. Both processes retain their complete archive comparisons and
runtime file/process guards. Recorded project imports from the historical process
must resolve inside the temporary source directory, with no fallback to the
editable current project.

The existing source checks now verify the historical directory explicitly. This
allows the shared model to grow while preserving the original experiments. A
changed output fails the current regression; these inputs cannot supply new
unseen acceptance for a repaired writer.

## Usage

The existing native-format job runs these checks. Its shallow checkout fetches
the single pinned generative-source commit before running the process suite.
It does not fetch all history or restore the removed recorded writer programs.

The independently authored inventory tool reads Git source objects and existing
process audit JSON only:

```sh
python3 re/tooling/sw2026/FreezeCohort.py \
  --audit-directory /path/to/original-camera-process-reports \
  --output /tmp/FrozenCohortSource.json
```

The committed inventory's digest is fixed in `ReadFrozen.py`. Its original
generation used the two camera process reports from the accepted prediction job,
not reports from a new execution. The tool executes no writer, codec or CAD code.
Only remote CI executes the historical writer and current-output comparisons.

## Dependency correction

The prior 354-file manifest covered the writer and many helpers, but package
initialization also imported 2,280 project source modules outside that manifest.
The source audit records 2,456 imported project modules in total. The historical
inventory includes all 3,154 Python source files in the pinned `src` tree, the
original listed research/helper files and three empty test-package initializers.

Every additional source file has the same Git object in both the pre-writer
camera-source author revision and the actual accepted prediction merge revision.
This closes a retrospective dependency accounting gap; it does not create a new
prospective freeze. See the [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/DependencyFreezesMustIncludePackageImports.md)
and [source record](../../../../../re/solidworks/records/ImportDependencyClosure2026.md).

## Verification and limits

Static source/object, SHA-256 and AST inspection completed. Black formatted the
changed Python outside `re`. No local tests or writer/codec executions ran.
Remote execution of this new historical/current comparison is pending.

The prior native measurements retain their original byte identities and scope.
This change adds no generated feature coverage, fresh held-out results, native
acceptance, or production writer. `SldprtAdapter` remains read-only. Each new
behavior still needs independent source inputs locked before its writer changes.
