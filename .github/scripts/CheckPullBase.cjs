// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { CheckApproval } = require("./CheckApproval.cjs");
const { CheckBaseOrder } = require("./CheckBaseOrder.cjs");
const { ReadRepoVersion } = require("./ReadRepoVersion.cjs");

async function CheckPullBase(Github, Context) {
  const PullRequest = Context.payload.pull_request;
  const Repository = Context.repo;
  const { data: Comparison } = await Github.rest.repos.compareCommits({
    ...Repository,
    base: PullRequest.base.sha,
    head: PullRequest.head.sha,
    per_page: 1,
  });
  const [Before, After] = await Promise.all([
    ReadRepoVersion(Github, Repository, Comparison.merge_base_commit.sha),
    ReadRepoVersion(Github, Repository, PullRequest.head.sha),
  ]);
  CheckBaseOrder(Before, After);
  if (Before !== After)
    await CheckApproval(Github, Repository, PullRequest, After);
}

module.exports = { CheckPullBase };
