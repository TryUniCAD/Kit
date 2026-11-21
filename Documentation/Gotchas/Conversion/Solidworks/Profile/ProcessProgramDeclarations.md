# Process-program declarations

Splitting a generated child-process program into short string constants in one file does not by itself satisfy the repository's declaration-splitting rule.

The [split standard](../../../../../.agents/skills/standard-pr-practice/references/Standards/Portable/SplitLargeDefinitions.md) also requires focused files for independent responsibilities. The research exemption applies to root `re/`, not `tests/`. Construction, archive encoding, decoding, editing and reporting can need separate files even when every declaration is below 30 logical lines.

The polygon process harness gives each stage one focused module and imports its exact declaration in `PolygonProgram.py`. `PolygonProcess.py` retains the subprocess boundary. This layout preserves the existing integration checks without introducing unit tests or treating short generated chunks as a policy exception.

The [original finding](https://github.com/TryUniCAD/Kit/pull/123#discussion_r4577077175) and [change entry](../../../../Changes/Solidworks/SolidworksProfileConstruction.md) record the repair.
