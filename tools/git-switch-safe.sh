#!/usr/bin/env bash
# git-switch-safe.sh — switch to a branch without silently losing files.
#
# WHY THIS EXISTS
#   This repo has forked branches that predate 9a1f332. Switching to `main`
#   from one of them deletes tracked files to match the branch, which is git
#   working correctly but destroy is user data. See tasks/lessons.md 2026-09-28.
#
# WHAT IT DOES
#   1. Refuses to run on a dirty tree (unless --force), and never touches your
#      uncommitted work.
#   2. Reports which tracked files the switch would DELETE, before deleting them.
#   3. Runs the switch, then re-checks for deletions and tells you exactly how
#      to recover them.
#
# USAGE
#   bash tools/git-switch-safe.sh main
#   bash tools/git-switch-safe.sh main --ff-first   # fast-forward the current
#                                                   # branch to target first,
#                                                   # eliminating all deletions
#   bash tools/git-switch-safe.sh main --force       # skip the clean-tree gate
#
# Run from the repository root.

set -uo pipefail

TARGET="${1:-}"
MODE="${2:-}"
DRY_ONLY=0

if [[ -z "$TARGET" ]]; then
  echo "usage: bash tools/git-switch-safe.sh <branch> [--ff-first|--force]" >&2
  exit 2
fi

git rev-parse --show-toplevel >/dev/null 2>&1 || {
  echo "FATAL: not inside a git repository." >&2; exit 2;
}
cd "$(git rev-parse --show-toplevel)" || exit 2

git rev-parse --verify --quiet "$TARGET^{commit}" >/dev/null || {
  echo "FATAL: no such branch/commit: $TARGET" >&2; exit 2;
}

CURRENT="$(git rev-parse --abbrev-ref HEAD)"

echo "=== repo : $(pwd)"
echo "=== from : $CURRENT"
echo "=== to   : $TARGET"
echo

# --- 1. Clean-tree gate -------------------------------------------------------
DIRTY="$(git status --porcelain --untracked-files=no)"
if [[ -n "$DIRTY" ]]; then
  echo "!! TRACKED CHANGES PRESENT — refusing to switch."
  echo "$DIRTY"
  echo
  echo "Commit, stash, or discard them yourself first. Nothing was changed."
  if [[ "$MODE" != "--force" ]]; then
    exit 1
  fi
  echo "--force given: continuing anyway."
  echo
fi

UNTRACKED="$(git status --porcelain --untracked-files=all | grep '^??' || true)"
if [[ -n "$UNTRACKED" ]]; then
  echo "-- untracked files present (git will leave these alone):"
  echo "$UNTRACKED"
  echo
fi

# --- 2. Prediction: what will the switch delete? ------------------------------
# Files whose content differs between HEAD and the destination, split by
# direction. `git diff --diff-filter=D DEST HEAD` lists files present at HEAD
# and absent at DEST (would be deleted); `--diff-filter=A` lists files present
# at DEST and absent at HEAD (would be created). Reading raw output in both
# directions is the reliable form — do not trust a chain of git state queries
# through `&&` for this, per tasks/lessons.md 2026-09-25.
PREDICTED="$(git diff --name-only --diff-filter=D "$TARGET" HEAD 2>/dev/null | sort)"
CREATED="$(git diff --name-only --diff-filter=A "$TARGET" HEAD 2>/dev/null | sort)"

if [[ -n "$PREDICTED" ]]; then
  COUNT="$(printf '%s\n' "$PREDICTED" | wc -l | tr -d ' ')"
  echo "!! DESTRUCTIVE SWITCH: $COUNT tracked file(s) exist here but not in '$TARGET'."
  echo "   git will delete these from your working tree:"
  printf '%s\n' "$PREDICTED" | sed 's/^/     DEL  /'
  echo
  if [[ "$MODE" != "--ff-first" ]]; then
    echo "   Recovery if you proceed:  git checkout $CURRENT -- <paths>"
    echo "   Safer alternative:        bash tools/git-switch-safe.sh $TARGET --ff-first"
    echo
  fi
else
  echo "-- prediction: no tracked-file deletions expected."
  echo
  DRY_ONLY=1
fi

if [[ -n "$CREATED" ]]; then
  echo "-- '$TARGET' has $(printf '%s\n' "$CREATED" | wc -l | tr -d ' ') file(s) not present here; they will appear:"
  printf '%s\n' "$CREATED" | head -20 | sed 's/^/     NEW  /'
  [[ "$(printf '%s\n' "$CREATED" | wc -l | tr -d ' ')" -gt 20 ]] && echo "     ... and more"
  echo
fi

# --- 3. Optional: fast-forward first so nothing is deleted --------------------
if [[ "$MODE" == "--ff-first" ]]; then
  echo "=== --ff-first: fast-forwarding '$CURRENT' to '$TARGET' first"
  if ! git merge --ff-only "$TARGET"; then
    echo
    echo "FATAL: '$CURRENT' is not a fast-forward of '$TARGET'."
    echo "       Do NOT force a merge. Inspect with:"
    echo "         git log --oneline --graph --all -20"
    echo "         git merge-base --is-ancestor $TARGET $CURRENT; echo \$?"
    exit 1
  fi
  echo "=== now '$CURRENT' contains '$TARGET'; switching is a no-op that deletes nothing."
  echo "=== nothing further to do — '$CURRENT' is already up to date."
  exit 0
fi

if [[ "$DRY_ONLY" -eq 1 && "$MODE" != "--run" ]]; then
  echo "=== nothing to protect against. Running the switch."
fi

# --- 4. The switch ------------------------------------------------------------
git checkout "$TARGET" || { echo "FATAL: checkout failed." >&2; exit 1; }
echo

# --- 5. Verify -----------------------------------------------------------------
AFTER="$(git status --porcelain --untracked-files=no)"
if [[ -n "$AFTER" ]]; then
  echo "!! FILES DISAPPEARED. Recover with:"
  echo "     git checkout $CURRENT -- <path>"
  echo
  echo "$AFTER"
  echo
  echo "Read tasks/lessons.md 2026-09-28 before doing anything else."
  exit 1
fi

echo "=== clean switch. Working tree matches '$TARGET'. Nothing was lost."
echo "=== files tracked: $(git ls-tree -r --name-only HEAD | wc -l | tr -d ' ')"
