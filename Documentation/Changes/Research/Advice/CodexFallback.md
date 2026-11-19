<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Codex suggestions for parked decoding jobs

On macOS or Linux, the research command can wait for a paired inference job to
park for missing evidence and ask Codex to suggest an experiment. Run it
alongside the controller and supervisor under the account with the authorized
Codex login. The ordinary research workflow requires no model.

Prepare a private JSON file for the exact job and assessment report you approve
for model advice. The inference job's `records.report_sha256` identifies the
report. The two text values are the only evidence sent to Codex. Use a discovery
summary approved for that transmission. Leave out native files, holdout
observations, private paths and credentials.

| Field               | Value                                                          |
| ------------------- | -------------------------------------------------------------- |
| `version`           | `1`                                                            |
| `job`               | Controller ID for the `inference.paired-gap` job               |
| `report_sha256`     | Exact report digest from the inference result                  |
| `model`             | Codex model available on the signed-in account                 |
| `question`          | Approved research question, up to 800 characters               |
| `discovery_summary` | Approved summary of discovery evidence, up to 3,200 characters |

Set the packet permissions to `0600` and create an output directory with
`0700` permissions outside the controller store. Run the companion command
with the repository's research Python environment.

```sh
python re/automation/CodexAdvice/Suggest.py \
  --store /private/research/Store \
  --approved-packet /private/research/ApprovedQuestion.json \
  --output /private/research/Advice \
  --wait-seconds 300
```

Omit the wait to inspect the current state once. The tool reads the accepted
controller receipt and result, checks their fingerprints and verifies the
approved report digest before sending anything. It claims each parked receipt
once in the output directory. Keep that directory across runs to prevent
duplicate calls. An existing incomplete claim requires operator review before
any resend.

The command starts Codex in a private temporary directory with the shell,
plugins, apps, subagents and web search disabled. It starts at medium reasoning
effort and uses extra-high effort if its first answer is invalid or times out.
A provider failure stops the request. Each attempt defaults to 90 seconds and
can be capped with `--attempt-seconds`. Codex uses the selected account's normal
usage limits.

The output records the matching parked receipt, the approved packet digest,
each attempt outcome and any suggestion. A suggestion includes one hypothesis,
one controlled change and two different predictions. It remains advisory.
Run the proposed experiment through the existing research workflow to verify
it. The command leaves the controller and the decoder's rules unchanged.

Process verification covered a malformed first answer, the second attempt,
a refused digest mismatch, repeat invocation, and an unchanged ledger. The
signed-in Codex CLI returned an advisory proposal for a fictional extrusion
question using synthetic measurements.
