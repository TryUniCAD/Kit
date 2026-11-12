// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { execFileSync } = require("node:child_process");
const { ReadBaseVersion } = require("./ReadBaseVersion.cjs");
const { VerifyVersionApproval } = require("./VerifyVersionApproval.cjs");

async function ReadGitHubVersion(Github, Repository, Revision) {
  const { data: Content } = await Github.rest.repos.getContent({
    ...Repository,
    path: "pyproject.toml",
    ref: Revision,
    mediaType: { format: "raw" },
  });
  return ReadBaseVersion(Content);
}

function RequireVersionIncrease(Before, After) {
  const Previous = Before.split(".").map(BigInt);
  const Proposed = After.split(".").map(BigInt);
  const Index = Proposed.findIndex((Part, Offset) => Part !== Previous[Offset]);
  if (Index >= 0 && Proposed[Index] < Previous[Index])
    throw new Error(
      `Base package version cannot decrease from ${Before} to ${After}`,
    );
}

async function VerifyPullVersion(Github, Context) {
  const Pull = Context.payload.pull_request;
  const Repository = Context.repo;
  const { data: Comparison } = await Github.rest.repos.compareCommits({
    ...Repository,
    base: Pull.base.sha,
    head: Pull.head.sha,
    per_page: 1,
  });
  const [Before, After] = await Promise.all([
    ReadGitHubVersion(Github, Repository, Comparison.merge_base_commit.sha),
    ReadGitHubVersion(Github, Repository, Pull.head.sha),
  ]);
  RequireVersionIncrease(Before, After);
  if (Before !== After)
    await VerifyVersionApproval(Github, Repository, Pull, After);
}

async function VerifyPublishedVersion(Github, Context) {
  const Repository = Context.repo;
  const First =
    Context.eventName === "push" ? Context.payload.before : `${Context.sha}^`;
  const Changes = execFileSync(
    "git",
    [
      "rev-list",
      "--first-parent",
      `${First}..${Context.sha}`,
      "--",
      "pyproject.toml",
    ],
    { encoding: "utf8" },
  ).trim();
  for (const Revision of Changes.split("\n").filter(Boolean)) {
    const Before = ReadBaseVersion(
      execFileSync("git", ["show", `${Revision}^:pyproject.toml`]),
    );
    const After = ReadBaseVersion(
      execFileSync("git", ["show", `${Revision}:pyproject.toml`]),
    );
    if (Before === After) continue;
    RequireVersionIncrease(Before, After);
    const Pulls = await Github.paginate(
      Github.rest.repos.listPullRequestsAssociatedWithCommit,
      {
        ...Repository,
        commit_sha: Revision,
      },
    );
    const Pull = Pulls.find(
      (Item) =>
        Item.merged_at &&
        Item.merge_commit_sha === Revision &&
        Item.base.ref === "main",
    );
    if (!Pull)
      throw new Error(
        `No merged PR found for base package version change at ${Revision}`,
      );
    await VerifyVersionApproval(Github, Repository, Pull, After);
  }
}

module.exports = { VerifyPullVersion, VerifyPublishedVersion };
