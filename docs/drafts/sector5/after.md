# What a player knows after sector 5, Name tags

- A branch is a **name for one commit**. `git branch -v` lists each name with its commit; `*`
  marks the one HEAD rides.
- **HEAD** is "you are here": the commit your folder shows. It rides a branch. A commit moves
  that branch, with HEAD, and no other name.
- `origin/main` is your **bookmark** of the mothership's `main`. It moves only when you talk to
  the mothership: push, fetch or pull.
- `git branch <name> <commit>` puts a name on any commit, and you stay where you are.
  `git branch -d <name>` takes a name off, and the commit stays. Git will not take off the name
  HEAD rides.
- Two branches off one commit make the chain fork like a tree. `git switch <name>` moves HEAD
  between them, and the folder follows. `git log --oneline --graph --all` draws the whole tree.
- `git switch -c <name>` makes a name and moves HEAD onto it, in one step.
- `git checkout <name>` and `git checkout -b <name>` are the older forms of `git switch` and
  `git switch -c`. They do the same.
- The pictures:
  - the chain: commits newest at the top, name tags, the HEAD mark, the dashed bookmark and the
    mothership's pin;
  - 5-5 adds a target picture to match.

Not taught, on purpose: detached HEAD, `HEAD~n`, `git branch -f`, rebase.
