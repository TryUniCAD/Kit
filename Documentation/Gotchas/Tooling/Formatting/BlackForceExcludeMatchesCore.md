# Black force-exclude matches Core paths

Expectation: invoking Black on an explicit production Python file checks that file's content.

Actual behavior: this checkout's `force-exclude = "(examples|modules|re)/"` is a regular expression without a path-segment boundary. The `re/` alternative also matches the end of `Core/`. Black can exit successfully after skipping an explicitly named `Core/...` file, even though that file is production code.

Workaround: for a scoped verification, pass each actual file's content to Black on standard input with the repository's explicit `--config`, retain its formatted result, and independently verify the resulting file hash. Do not count an exit-zero command as evidence for a file that was skipped. A repository-wide exclude-rule repair is separate from the body-name reader change.

The named-body reader's first pass skipped 18 Core paths. Its retained stdin pass formatted all 47 actual source contents, followed by the two-file output-owner extension. The original private formatting receipt is `BlackCoreStdin01.json`; it remains outside the repository with the exact source closure. The measured reader proof is described in [SdkNamedBodyRead2026.md](../../../../re/solidworks/records/SdkNamedBodyRead2026.md).
