# 5-1 Name tags

Mission. Command: `git branch -v`.

## Briefing

You noted the fuel level in `notes.txt`. Commit the note and send it to the mothership, then check for news from the crew. Watch which names move.

## Goals

1. Read the history: `git log --oneline`.
2. List your branches: `git branch -v`.
3. Predict first.
4. Commit your note: `git commit -am "Note the fuel level"`.
5. Read the history again: `git log --oneline`.
6. Send it up: `git push`.
7. Predict first.
8. Ask the mothership for news: `git fetch`.
9. Ask how `main` stands: `git status`.

## Beats

### Beat 1: scene

**Rama:** New sector: Name tags. Since you met the mothership you have typed `main` and `origin/main` in `git push` and `git status`. This sector says what they are: names. Commits are the work; names are how you find it.

**Designer note (what the picture does):** The sector opens on the chain, born here.

### Beat 2: scene

**Rama:** This is the chain: your commits, newest at the top, each joined by a line to the one before it. The commits are the work. This mission is about the names on them.

### Beat 3: type

The player types:

```
$ git log --oneline
61255a6 (HEAD -> main, origin/main) Add the crew list
205de41 Plot the route
ce9b38c (test-run) Start the project
```

**Rama:** The names in brackets sit on that commit. `main` is a branch: a name for one commit. `test-run` is another branch, a name for an older commit. On the chain, names are the tags beside a commit.

### Beat 4: say

**Rama:** One more word in the brackets: `HEAD -> main` means `HEAD` is on `main`. `HEAD` is "you are here": the commit your folder shows. On the chain it is the `HEAD ▶` mark, riding the `main` tag.

**Designer note (what the picture does):** The HEAD mark is ringed, on the same commit as the highlighted line.

### Beat 5: type

The player types:

```
$ git branch -v
* main     61255a6 Add the crew list
  test-run ce9b38c Start the project
```

**Rama:** That is all a branch is: a name and the hash of one commit. Two names, two commits. The `*` marks the branch `HEAD` is on. On the chain, that branch's tag is filled; the other is outlined.

### Beat 6: say

**Rama:** `origin/main`, dashed, is your bookmark: where the mothership's `main` was the last time you talked to the mothership. The pink pin is where the mothership's `main` really is. Right now they agree.

### Beat 7: predict

**Prediction:** You commit your fuel note now. Which names move up to the new commit?

- Only `main`
- `main` and `origin/main`
- `main` and `test-run`
- None of them

Reveal: Only `main`, with `HEAD` riding it. A commit moves the branch `HEAD` rides. `test-run` names its own commit, and the bookmark moves only when you talk to the mothership.

### Beat 8: type

The player types:

```
$ git commit -am "Note the fuel level"
[main 6c35b8f] Note the fuel level
 1 file changed, 1 insertion(+)
```

**Rama:** `main` moved up to the new commit, and `HEAD` rode along. `test-run` stayed. The bookmark and the pin stayed too: the mothership has not heard of this commit.

**Designer note (what the picture does):** A new capsule lands on top. The filled `main` tag and the HEAD mark slide up onto it; the bookmark and the pin stay one commit below.

### Beat 9: type

The player types:

```
$ git log --oneline
6c35b8f (HEAD -> main) Note the fuel level
61255a6 (origin/main) Add the crew list
205de41 Plot the route
ce9b38c (test-run) Start the project
```

**Rama:** `git log` says the same in words: `HEAD -> main` on the new commit, `origin/main` one below.

### Beat 10: type

The player types:

```
$ git push
To ../github.com/moonbase/project.git
   61255a6..6c35b8f  main -> main
```

**Rama:** The push sent your commit up, and the mothership's `main` moved to it. Git moved your bookmark at the same moment, because you were talking to the mothership.

**Designer note (what the picture does):** The pin and the bookmark climb onto the new commit.

### Beat 11: event

Event: Alex pushed Fix the route.

**Rama:** News: Alex just pushed a fix. The pin jumped up to Alex's commit. Your bookmark did not move: you have not talked to the mothership since your push.

**Designer note (what the picture does):** A pink dotted capsule appears above yours: Alex's commit, only on the mothership, with the pink pin on it. Your bookmark stays on your commit. The bookmark and the pin are apart for the first time.

### Beat 12: predict

**Prediction:** You type `git fetch`, which asks the mothership for news. Afterwards, is Alex's fix in your folder?

- Yes
- No

Reveal: No. A fetch brings Alex's commit into your repository and moves your bookmark to it. `main` stays where it was, so your folder, which shows `main`'s commit, does not change.

### Beat 13: type

The player types:

```
$ git fetch
From ../github.com/moonbase/project
   6c35b8f..6b6a005  main       -> origin/main
```

**Rama:** Your bookmark caught up with the pin, and Alex's commit is now in your repository: it turned solid. `main` and `HEAD` stayed on your commit, so your folder did not change.

**Designer note (what the picture does):** Alex's capsule turns from pink dotted (only on the mothership) to solid; the dashed bookmark jumps up onto it, beside the pin.

### Beat 14: type

The player types:

```
$ git status
On branch main
Your branch is behind 'origin/main' by 1 commit, and can be fast-forwarded.
  (use "git pull" to update your local branch)

nothing to commit, working tree clean
```

**Rama:** `git status` compares `main` with your bookmark: one commit behind. "Fast-forwarded" means `main` can simply slide up to it; `git pull` would do that. The next mission starts after that pull.

### Beat 15: done

**Debrief:**

A branch is a name for one commit. `HEAD` is "you are here", and it rides the branch you are on. When you commit, that branch moves up to the new commit and `HEAD` rides along; no other name moves.

`origin/main` is your bookmark of the mothership's `main`. The mothership can move on without you, as it did when Alex pushed; your bookmark catches up only when you talk to the mothership: `git push`, `git fetch` or `git pull`.

Commands to keep:

```
$ git log --oneline   # the names in brackets sit on that commit
$ git branch -v       # each branch and the commit it names; * is where HEAD rides
$ git fetch           # update your bookmark of the mothership
```

## Losses


## Rama's reactions

- `git branch -v`: "Each line is a name and the commit it points at. `*` marks the one `HEAD` rides."
- `git pull` before the fetch goal: allowed; the fetch and status goals then pass with it.

## Design notes (after playing)

**The one idea:** A branch is a name for one commit. HEAD is "you are here" and rides a branch. A commit moves only the branch HEAD rides. `origin/main` is your bookmark of the mothership: it moves only when you talk to the mothership.

**On screen:** The chain, born here: your commits, newest at the top, the names on them, the HEAD mark, the dashed `origin/main` bookmark, and a pink pin for where the mothership's `main` really is.

**Hidden on purpose:** The desk (one file changes, and it is not the point), Alex's station (Alex's push shows as the pin moving).

## Hints and solution (the last hint gives every line)

1. `git log --oneline` shows each commit on one line; the names in brackets are the names on that commit.
2. `git commit -am` commits every tracked file you changed; `git push` sends `main` up; `git fetch` asks the mothership for news.
3. Every line of the mission, in order:
   
       $ git log --oneline
       $ git branch -v
       $ git commit -am "Note the fuel level"
       $ git log --oneline
       $ git push
       $ git fetch
       $ git status

Git's output above is real: `.scratch/sector7-design/gen.py` built the level's lab and typed each line as the game's terminal does. `<lab>` stands for the level's lab folder on the player's computer, which the game shows in full.
