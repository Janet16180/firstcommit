#!/usr/bin/env bash
# Record what real git prints for the field guide's branch and merge storyboards.
#
# Usage: record.sh <out-dir>
# Writes one <scene>.txt per scene: "$ command" lines, each followed by what git printed
# (stdout and stderr, in order). Every repository is rebuilt from scratch with fixed identities
# and dates, so a commit has the same hash in every scene that holds it. Git runs only under a
# temporary HOME, with the game's settings (init.defaultBranch=main, core.pager=cat,
# core.editor=true, color.ui=never). Each recorded line runs on a terminal of its own (script(1)),
# as in the game's terminal: git then names branches in git log, prints in a terminal's order,
# and ls prints in columns. What is written is what the terminal shows (screen.py: a line git
# overwrites with \r and ESC [K is written as it ends up), with the temporary folder's path
# written as /home/you.
set -euo pipefail

OUT=$(realpath "$1")
mkdir -p "$OUT"
export HOME=$(mktemp -d)
trap 'cd / && rm -rf "$HOME"' EXIT
export GIT_CONFIG_NOSYSTEM=1 HISTFILE=/dev/null LC_ALL=C
unset GIT_DIR GIT_WORK_TREE GIT_PAGER PAGER EDITOR VISUAL
cat > "$HOME/.gitconfig" <<'EOF'
[init]
	defaultBranch = main
[core]
	pager = cat
	editor = true
[color]
	ui = never
[user]
	name = You
	email = you@station.space
EOF
SHOWN=/home/you
SCREEN=$(dirname "$(realpath "$0")")/screen.py

day=0
when() {
	export GIT_AUTHOR_DATE="2026-06-$(printf %02d "$1")T09:00:00+00:00"
	export GIT_COMMITTER_DATE=$GIT_AUTHOR_DATE
}

save() {
	git add "$1"
	git commit -q -m "$2"
}

# Run one command line, append it and its output to the scene's file.
run() {
	local scene=$1 line=$2 output
	output=$(script -qec "$line" /dev/null | python3 -I "$SCREEN") || true
	output=${output//$HOME/$SHOWN}
	{
		printf '$ %s\n' "$line"
		if [ -n "$output" ]; then printf '%s\n' "$output"; fi
	} >> "$OUT/$scene.txt"
}

# A fresh repository: two commits on main.
start() {
	rm -rf "$HOME/ship"
	mkdir "$HOME/ship"
	cd "$HOME/ship"
	git init -q
	when 1; printf 'Notes\n' > notes.txt; save notes.txt "Start the project"
	when 2; printf 'Route: Moon\n' > route.txt; save route.txt "Plot the route"
}

# start, then scout with one commit of its own; HEAD back on main.
scout() {
	start
	git branch scout
	git switch -q scout
	when 3; printf 'probe=ready\n' > probe.txt; save probe.txt "Ready the probe"
	git switch -q main
}

# scout, then main moves on too: the two lines fork.
fork() {
	scout
	when 4; printf 'fuel=full\n' > fuel.txt; save fuel.txt "Fill the tanks"
}

rm -f "$OUT"/*.txt

start
run branch "git branch scout"
run branch "git branch"
run branch "git log --oneline"

scout
run switch "ls"
run switch "git switch scout"
run switch "ls"
run switch "git log --oneline --all"

scout
run switch-back "git switch scout"
run switch-back "git switch main"
run switch-back "ls"

scout
printf 'Notes\nFuel: 80%%\n' > notes.txt
run switch-carry "git switch scout"
run switch-carry "git status --short"

start
git switch -q -c scout
when 3; printf 'Route: Mars\n' > route.txt; save route.txt "Head for Mars"
git switch -q main
printf 'Route: Moon, Phobos\n' > route.txt
run switch-refused "git switch scout"

start
run switch-c "git switch -c lights"
run switch-c "git log --oneline"

start
run switch-missing "git switch lights"

start
run checkout-b "git checkout -b lights"

scout
run checkout "git checkout scout"

scout
when 4
run merge-ff "git merge scout"
run merge-ff "git log --oneline --graph --all"

fork
run graph "git log --oneline --graph --all"
run graph-no-all "git log --oneline --graph"

fork
when 5
run merge-commit "git merge scout"
run merge-commit "git log --oneline --graph --all"
run merge-graph "git log --oneline --graph --all"

fork
when 5
run merge-no-edit "git merge --no-edit scout"
run merge-no-edit "git log --oneline -1"

# What the editor would open with, when git asks for the merge's message: a stand-in editor
# copies the file git hands it.
fork
when 5
printf '#!/bin/sh\ncp "$1" "%s/editor.txt"\n' "$HOME" > "$HOME/editor.sh"
chmod +x "$HOME/editor.sh"
# git opens the editor for a merge only on a terminal, unless GIT_MERGE_AUTOEDIT says yes.
GIT_MERGE_AUTOEDIT=yes GIT_EDITOR="$HOME/editor.sh" git merge -q scout
cp "$HOME/editor.txt" "$OUT/merge-editor.txt"

scout
when 4
git merge -q scout
run branch-d "git branch -d scout"
run branch-d "git log --oneline --all"

fork
run branch-d-refused "git branch -d scout"

scout
git switch -q scout
run branch-d-here "git branch -d scout"

git --version > "$OUT/version.txt"
