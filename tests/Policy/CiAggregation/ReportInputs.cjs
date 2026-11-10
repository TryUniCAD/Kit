// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const Expected = require("./ExpectedChecks.cjs");
const { BuildReviews } = require("./ReviewReports.cjs");

function BuildReports(Mode, Verdict) {
  const Checks = Expected.map((Name, Index) => ({
    id: Index + 1,
    name: Name,
    app: { id: 15368, slug: "github-actions" },
    check_suite: { id: 1 },
    status: "completed",
    conclusion: "success",
  }));
  const Reviews = BuildReviews(Verdict);
  Checks.push(
    ...Reviews.Checks.map((Check) => ({ ...Check, id: Check.id + 100 })),
  );
  const Statuses = Reviews.Statuses;
  if (Mode === "check") Checks[0].conclusion = "failure";
  if (Mode === "status")
    Statuses.push({
      id: 900,
      context: "Greptile Review",
      creator: { id: 900, login: "build-service" },
      state: "failure",
    });
  if (Mode === "external")
    Checks.push({
      id: 901,
      name: "CodeRabbit",
      app: { id: 901, slug: "external-ci" },
      check_suite: { id: 3 },
      status: "completed",
      conclusion: "neutral",
    });
  return { Checks, Statuses };
}

module.exports = { BuildReports };
