# Native report shard count

A larger native matrix does not automatically expand the report verifier.
The verifier originally read exactly four artifacts, so a five-way selection omitted the fifth roster and failed exact-once acceptance.

Pass the planner count as the sixth argument to `.github/scripts/VerifyShardReports.sh` from both platform report jobs.
The verifier accepts four or five shards, keeps four as the default for older callers, and retains earlier-attempt artifact fallback.
The native planner process scenarios cover both counts through actual pytest execution and report verification.

The initial finding is recorded in [PR #276](https://github.com/TryUniCAD/Kit/pull/276#discussion_r4668143521).
Remote complete-suite execution remains assigned to merge acceptance.
