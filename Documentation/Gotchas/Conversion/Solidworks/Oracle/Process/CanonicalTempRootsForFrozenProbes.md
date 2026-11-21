# Frozen probes need canonical temporary roots on macOS

macOS can supply a temporary path under `/var` that resolves under `/private/var`. The trusted-root check and the frozen-process source guard compare paths against the resolved directory. A lexical alias can make an intended digest check stop at path validation or leave historical archive modules unavailable.

Set `TMPDIR` to an existing canonical temporary directory when running the SOLIDWORKS integration suite on macOS. The signature digest and five frozen visual or feature checks passed after this adjustment. The original fixture and source constraints still apply. [CAD acceptance criteria](../../../../../Reference/Operations/CadSuccessCriteria.md)
