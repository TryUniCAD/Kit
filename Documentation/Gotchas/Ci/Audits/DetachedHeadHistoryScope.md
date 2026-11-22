# Detached HEAD does not restrict a Git history scan

A source audit can check out an exact old commit while retaining newer branch and tag refs from a full fetch.
TruffleHog 3.97.0 walks every ref when no scan head is supplied, so detaching HEAD alone does not bound its history to the selected revision.
See the [scan-head implementation](https://github.com/trufflesecurity/trufflehog/blob/v3.97.0/pkg/sources/git/git.go)
and [review finding](https://github.com/TryUniCAD/Kit/pull/223#discussion_r4652676973).

For manual source audits, pass `--branch` with the full selected SHA.
Retain the existing all-ref scope on native triggers and preserve verification and exclusion settings.
