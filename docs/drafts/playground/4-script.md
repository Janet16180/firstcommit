# Playground 4: Alex joins

Starting point: **Alex is ahead**. Two terminals: Alex pushes, you fetch and pull, and the pins move. The phone shows one terminal at a time.

## Beats

### Beat 1

The playground opens on Alex is ahead, on History, with Alex's terminal shown.

The mothership has two commits more than your repository: pink rows with nothing beside them on your side.

### Beat 2

They type `git status`.

"Your branch is up to date with 'origin/main'." Up to date with your bookmark, which is old: History shows the mothership is ahead.

```
project $ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

*Designer note:* A trap the levels teach; the playground lets the player meet it again on their own.

### Beat 3

They type `git fetch`.

The two commits come into your repository and `origin/main` moves up to them. `main` stays.

```
project $ git fetch
From ../github.com/moonbase/project
   44c16d0..bb7060e  main       -> origin/main
```

### Beat 4

They type `git status` again.

Behind by 2 commits, and can be fast-forwarded. The phone's summary agrees: "main 2 behind origin/main".

```
project $ git status
On branch main
Your branch is behind 'origin/main' by 2 commits, and can be fast-forwarded.
  (use "git pull" to update your local branch)

nothing to commit, working tree clean
```

### Beat 5

They type `git pull`.

`main` slides up: your side and the mothership's side match row for row.

```
project $ git pull
Updating 44c16d0..bb7060e
Fast-forward
 notes.txt | 1 +
 route.txt | 2 +-
 2 files changed, 2 insertions(+), 1 deletion(-)
```

### Beat 6

Now in Alex's terminal: `echo "Dock 3 is free tonight." >> notes.txt`.

Crew view: Alex's notes.txt is edited, at Alex's station only.

```
alex: project $ echo "Dock 3 is free tonight." >> notes.txt
```

*Designer note:* On a phone the Terminal: You | Alex switch moves to Alex, and the picture follows it: the folded line now reads "Alex's repository: …".

### Beat 7

Alex's terminal: `git commit -am "Note the free dock"`.

A commit at Alex's station only, signed Alex.

```
alex: project $ git commit -am "Note the free dock"
[main 08387e9] Note the free dock
 1 file changed, 1 insertion(+)
```

### Beat 8

They pick Chain, then Picture: Alex's repository.

Alex's chain, in Alex's green: the new commit on top with Alex's `main` on it; your violet pin, You: main, one below.

### Beat 9

Alex's terminal: `git push`.

Alex's `origin/main` bookmark and the pink mothership pin climb to Alex's commit.

```
alex: project $ git push
To ../../github.com/moonbase/project.git
   bb7060e..08387e9  main -> main
```

### Beat 10

Picture: your repository.

Your chain, in violet: Alex's commit floats above yours, pink dotted, only on the mothership, with the mothership's pin and Alex's green pin on it.

### Beat 11

In your terminal: `git pull`.

Crew view: the mothership and both stations end on the same commit.

```
project $ git pull
From ../github.com/moonbase/project
   bb7060e..08387e9  main       -> origin/main
Updating bb7060e..08387e9
Fast-forward
 notes.txt | 1 +
 1 file changed, 1 insertion(+)
```

## Design notes

Alex's terminal is hidden by default and shown in the two starting points about two people. It is a second shell in Alex's clone, with Alex's name and email: Alex's commits are signed by Alex because Alex's git says so. Colour never changes owner: violet is always you, green always Alex, whoever's repository is drawn. In Alex's repository Alex's capsules and filled tag are green, and your pin is violet. Your terminal is framed in violet, Alex's in green. On a phone only one terminal fits: "Terminal: You | Alex" above it picks which, and the picture follows the terminal shown, so a phone has one switch, not two. On a wide screen "Picture: your repository | Alex's repository" picks which repository the chain, desk, move log and graph draw; History and Crew always show both people.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
