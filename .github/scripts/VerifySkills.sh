# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

set -euo pipefail

ExpectedPath=.agents/skills/standard-pr-practice/SKILL.md
mapfile -t SkillPaths < <(git ls-files -- '*/SKILL.md')
if [ "${#SkillPaths[@]}" -ne 1 ] || [ "${SkillPaths[0]}" != "$ExpectedPath" ]; then
  echo '::error::standard-pr-practice must be the only repository skill'
  exit 1
fi
test "$(head -n 1 "$ExpectedPath")" = '---'
rg --quiet '^name: standard-pr-practice$' "$ExpectedPath"
rg --quiet '^license: MIT$' "$ExpectedPath"
test -L .claude/skills/standard-pr-practice
test "$(readlink .claude/skills/standard-pr-practice)" = '../../.agents/skills/standard-pr-practice'
test -f .claude/skills/standard-pr-practice/SKILL.md
if [ -n "$(git ls-files -- .kiro/steering .kiro/skills tools/skills)" ]; then
  echo '::error::legacy skills and their generator must not be restored'
  exit 1
fi
echo 'standard-pr-practice is the only repository skill'
