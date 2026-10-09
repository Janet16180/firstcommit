# What a player knows before sector 8, Time travel

Read this before judging the storyboards 8-1 to 8-5. It assumes the recommended layout
(`docs/drafts/sector5/plan.md`):

1. Lift-off
2. Cargo dock
3. Vault
4. Mothership, which now ends with the clone level, New recruit, before the Base 7 challenge
5. **Name tags** (new)
6. Branches
7. Collisions
8. Time travel

## The world and its words

- **Your station** has four places: the **workshop** (the working folder), the **cargo dock**
  (the staging area), the **vault** (your repository's commits) and the **mothership** (the
  remote, GitHub). A **capsule** is a commit.
- **The chain** (from sector 5): commits newest at the top, each joined to its parent.
  - Name tags: the filled one is the branch you are on, outlined ones are your other branches.
  - The HEAD mark ("you are here").
  - The dashed `origin/main` bookmark.
  - Pins for where the mothership and Alex (green) really are.
- **Alex** is your teammate. Robin appears only as a commit author.
- Names already taken: "**Flight recorder**" is 3-3's title (reading the history with
  `git log`). "**Black box**" is 1-2's name for the hidden `.git` folder.

## Commands typed in guided levels

| Sector | Commands | Ideas met |
|---|---|---|
| 1 Lift-off | `ls`, `ls -a`, `git init`, `git status` | Git works only in a repository |
| 2 Cargo dock | `git add`, `git restore --staged`, `.gitignore` | you choose what goes into the next commit; unstaging keeps your folder's copy |
| 3 Vault | `git commit -m`, `git diff`, `git diff --staged`, `git log`, `git log <file>` | a commit seals what is staged; each commit has a hash |
| 4 Mothership | `git remote add origin`, `git push -u origin main`, `git push`, `git commit -am`, `git pull`, `git fetch`, `git pull --no-rebase`, `git clone`, `git log --oneline` | push, fetch, pull; a refused push; a clone brings the whole history |
| 5 Name tags | `git log --oneline --graph --all`, `git branch -v`, `git branch -d`, `git branch <name> <commit>`, `git branch <name>`, `git switch`, `git switch -c`, `git checkout`, `git checkout -b` | a branch is a name for one commit; HEAD is "you are here" and rides a branch; a commit moves only that branch; `origin/main` is a bookmark that moves only when you talk to the mothership; names come and go, commits stay; two branches off one commit fork the chain into a tree; Git will not delete the name HEAD rides |
| 6 Branches | `git push origin <branch>`, `git push -u origin <branch>`, `git branch -r` | a push sends one branch, by name; uncommitted edits are on no branch and come along on a switch |
| 7 Collisions | `git merge <branch>`, `git merge --no-edit`, `git log --oneline --graph`, `git merge --abort`, `git restore --theirs <file>`, `git commit --no-edit` | a merge makes a commit with two parents; a paused merge can be called off; a conflict is solved by choosing, adding and committing |

## Not met before sector 8

- `git restore <file>` without `--staged` (scrapping your folder's changes). 8-1 teaches it.
- `git revert`, and naming a commit as `HEAD~1`. 8-2 teaches both.
- `git reset`. 8-3 teaches `--hard`.
- `git reflog` and `HEAD@{n}`. 8-4 teaches them.
- Commits no branch leads to, drawn faded. They first appear in 8-3's WHAT IF.
- `git branch -D`. Only 8-5's briefing mentions it; the player never types it.
- "Fast-forward" as a word: 4-3 says a pull "only slides your label"; 5-1's `git status` says
  "can be fast-forwarded".
