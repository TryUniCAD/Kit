# Offline corpus decoding

The research CLI previously requested native verification for every reader invocation.
`kit research --offline --root CHECKOUT solidworks ...` now runs the deterministic reader without native verification.
Fusion supports the same option.
The option precedes the tool name and rejects conflicting native verification arguments.
The default verification behavior remains unchanged.

The corpus driver at `re/automation/OfflineCorpus/RunCorpus.py` runs the pinned readers and CLI inspection.
It retains commands, source hashes, failures, receipts, and decoded documents under `.rescratch/`.
The research findings record the completed run and retained artifact hashes.

Native verification is pending because the PC is off.
Offline decoding does not establish vendor acceptance or complete recovered semantics.
Integration coverage exercises the real CLI and SOLIDWORKS reader in remote CI.
No tests ran locally. Merge-group acceptance remains deferred.
