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
grep --quiet '^name: standard-pr-practice$' "$ExpectedPath"
grep --quiet '^license: MIT$' "$ExpectedPath"
test -f CLAUDE.md
grep --quiet '.agents/skills/standard-pr-practice/SKILL.md' CLAUDE.md
if [ -n "$(git ls-files -- .kiro/steering .kiro/skills tools/skills)" ]; then
  echo '::error::legacy skills and their generator must not be restored'
  exit 1
fi
echo 'standard-pr-practice is the only repository skill'
