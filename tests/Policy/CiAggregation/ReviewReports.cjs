// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const {
  Reviewers,
  ExcludedReports,
} = require("../../../.agents/skills/standard-pr-practice/ReviewBot.json");
const KProviders = [...Reviewers, ...ExcludedReports];

function BuildReviews(Verdict) {
  const Checks = [];
  const Statuses = [];
  for (const Provider of KProviders) {
    Checks.push({
      id: Checks.length + 1,
      name: "Review report",
      app: { id: Provider.AppId, slug: Provider.AppSlug },
      check_suite: { id: 2 },
      status: Verdict === "pending" ? "in_progress" : "completed",
      conclusion: Verdict === "pending" ? null : Verdict,
    });
    Statuses.push({
      id: Statuses.length + 1,
      context: `review-${Provider.UserId}`,
      creator: { id: Provider.UserId, login: Provider.UserLogin },
      state: Verdict === "neutral" ? "error" : Verdict,
    });
  }
  return { Checks, Statuses };
}

module.exports = { BuildReviews };
