#!/usr/bin/env bash
# Links this repo's skills into ~/.claude/skills and mcp-lazy into ~/.local/bin.
# Never replaces something it did not create, except an mcp-lazy byte-identical to ours.
set -euo pipefail

repo="$(cd "$(dirname "$0")" && pwd)"
skills_dir="$HOME/.claude/skills"
bin_dir="$HOME/.local/bin"
mkdir -p "$skills_dir" "$bin_dir"

for skill in "$repo"/skills/*/; do
  name="$(basename "$skill")"
  target="$skills_dir/$name"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "${skill%/}" ]; then
    echo "ok       $name"
  elif [ -e "$target" ] || [ -L "$target" ]; then
    echo "skipped  $name: $target already exists"
  else
    ln -s "${skill%/}" "$target"
    echo "linked   $name"
  fi
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
