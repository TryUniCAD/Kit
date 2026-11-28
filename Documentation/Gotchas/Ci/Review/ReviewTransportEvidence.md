# Review transport errors need endpoint evidence

Expected: a review proceeds after authorization, source selection and container construction succeed.

Observed: hosted reviews failed during the account runtime with an error sending a request.
The retained logs do not establish whether DNS, TLS or the upstream service caused the transport failure.
They show no identified authentication or token-refresh rejection.
The [saved-cuboid review run](https://github.com/TryUniCAD/Kit/actions/runs/46173702647) records one affected workflow.

Use the [credential-free probe](../../../Changes/Review/ReviewerConnectivityProbe.md) on a reviewed ref to collect reachability evidence.
Its Node requests do not prove that the Rust client, authentication or model invocation works.
Retain the failed native report until a complete current-head review succeeds.
Change credentials only when independent evidence identifies an authentication or refresh failure.
