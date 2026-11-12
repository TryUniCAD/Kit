// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { CiWorkflows } = require("../../../.github/scripts/CiAllowlist.cjs");

function BuildExpected(IsQueue, HeadSha) {
  const Runs = [];
  const Checks = [];
  for (const [Path, Spec] of CiWorkflows(!IsQueue, false, !IsQueue)) {
    const Suite = Runs.length + 10;
    Runs.push({
      id: Suite,
      check_suite_id: Suite,
      head_sha: HeadSha,
      event: Spec.event,
      path: Path,
      name: Path.endsWith("/MergeQueue.yml") ? "Merge queue" : Path,
      status: "completed",
      conclusion: "success",
    });
    const Names = new Set([
      ...Spec.required,
      ...(Spec.optional ?? []),
      ...(Spec.preflight ? [Spec.preflight] : []),
    ]);
    for (const Name of Names)
      Checks.push({
        id: Checks.length + 1,
        name: Name,
        head_sha: HeadSha,
        app: { id: 15368, slug: "github-actions" },
        check_suite: { id: Suite },
        status: "completed",
        conclusion:
          Spec.skip?.includes(Name) || (!IsQueue && Name === Spec.preflight)
            ? "skipped"
            : "success",
      });
  }
  return { Runs, Checks };
}

module.exports = { BuildExpected };
