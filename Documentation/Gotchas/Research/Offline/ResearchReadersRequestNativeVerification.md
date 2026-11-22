# Research readers request native verification by default

An offline reader invocation might appear to avoid application access.
The CLI launcher appends `--native-verify` by default, even though direct deterministic readers do not.
Use `research --offline` before the tool name to suppress this request explicitly.
The launcher states that native verification is pending and vendor acceptance is not established.
See [the change entry](../../../Changes/Research/Offline/OfflineCorpusDecoding.md).
