#!/usr/bin/env bash
# Links this repo's skills into ~/.claude/skills (every Claude account) and ~/.agents/skills
# (Codex, Gemini CLI, opencode, Cursor and other agents that read the shared folder), and
# mcp-lazy into ~/.local/bin.
# Never replaces something it did not create, except an mcp-lazy byte-identical to ours.
set -euo pipefail

repo="$(cd "$(dirname "$0")" && pwd)"
bin_dir="$HOME/.local/bin"
mkdir -p "$bin_dir"

# Each ~/.claude-account* config dir shares the default account's skills folder.
for account in "$HOME"/.claude-account*/; do
  [ -d "$account" ] || continue
  if [ -e "${account}skills" ] || [ -L "${account}skills" ]; then continue; fi
  ln -s "$HOME/.claude/skills" "${account}skills"
  echo "linked   ${account}skills"
done

for skills_dir in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$skills_dir"
  for skill in "$repo"/skills/*/; do
    name="$(basename "$skill")"
    target="$skills_dir/$name"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "${skill%/}" ]; then
      echo "ok       $name  ($skills_dir)"
    elif [ -e "$target" ] || [ -L "$target" ]; then
      echo "skipped  $name: $target already exists"
    else
      ln -s "${skill%/}" "$target"
      echo "linked   $name  ($skills_dir)"
    fi
  done
done

lazy="$bin_dir/mcp-lazy"
if [ -L "$lazy" ] && [ "$(readlink "$lazy")" = "$repo/tools/mcp-lazy" ]; then
  echo "ok       mcp-lazy"
elif [ -e "$lazy" ] && ! cmp -s "$lazy" "$repo/tools/mcp-lazy"; then
  echo "skipped  mcp-lazy: $lazy differs from the repo copy"
else
  ln -sf "$repo/tools/mcp-lazy" "$lazy"
  echo "linked   mcp-lazy"
fi
