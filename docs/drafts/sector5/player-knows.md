# What a player knows before sector 5, Name tags

Read this before judging the storyboards 5-1 to 5-5. It assumes the layout in `plan.md`: Name
tags is a new sector right after the mothership. The clone level, New recruit, has moved to the
end of sector 4. What sector 5 adds is in `after.md`; read it only after the storyboards.

## The world and its words

- **Your station** has four places: the **workshop** (the working folder), the **cargo dock**
  (the staging area), the **vault** (your repository's commits) and the **mothership** (the
  remote, GitHub). A **capsule** is a commit.
- **Alex** is your teammate, with a clone of their own.
- The page has shown `HEAD → main` on the newest commit, but no level has said what `HEAD` is.
  `main` and `origin/main` have been typed, never explained as names.

## Commands typed so far

| Sector | Commands | Ideas met |
|---|---|---|
| 1 Lift-off | `ls`, `ls -a`, `git init`, `git status` | Git works only in a repository; `.git` holds it |
| 2 Cargo dock | `git add`, `git restore --staged`, `.gitignore` | you choose what goes into the next commit |
| 3 Vault | `git commit -m`, `git diff`, `git diff --staged`, `git log`, `git log <file>` | a commit seals what is staged; the history lists commits newest first, each with a hash |
| 4 Mothership | `git remote add origin`, `git push -u origin main`, `git push`, `git commit -am`, `git pull`, `git fetch`, `git pull --no-rebase`, `git clone`, `git log --oneline` | push sends your commits; fetch updates `origin/main` only; pull is fetch plus merge; a push is refused when the mothership has commits you don't; a clone brings the whole history |

## Not met yet

Branches as such (`git branch`, `git switch`), `HEAD` as an idea, and any way to move a name
other than committing.
