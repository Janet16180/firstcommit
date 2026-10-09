# Playground 9: Try it from a card

Starting point: **Two branches**. From a field guide card over mission 5-4 to the playground and back, the mission left in progress.

## Beats

### Beat 1

In mission 5-4, the player opens the field guide's card for `git switch -c`.

The card explains the command. Under it: Try it in the playground.

### Beat 2

They press Try it in the playground.

### Beat 3

The playground opens on Two branches, on the chain.

On your terminal, right above the prompt, a chip: Try: git switch -c test. In the header: Back to Mission 5-4.

### Beat 4

They click the chip.

The command waits at the prompt. Nothing has run.

### Beat 5

They press Enter.

A new name, `test`, on main's commit, and HEAD on it. The chip is gone: its command has run.

```
project $ git switch -c test
Switched to a new branch 'test'
```

### Beat 6

They type `git branch -v`.

Four names; `*` on test.

```
project $ git branch -v
  bright-lights 3c9081a Try bright lights
  main          44c16d0 Add the crew list
  quiet-engine  1942d3b Try a quiet engine
* test          44c16d0 Add the crew list
```

### Beat 7

They press Back to Mission 5-4.

Mission 5-4 is where they left it: its own lab, its own terminal, the goals as they were.

*Designer note:* The playground's lab stays too: the next visit opens on Two branches with `test` still there.

## Design notes

A command card in the field guide links to the starting point that suits its command, with the command as a chip: #/playground?start=branches&view=chain&try=git%20switch%20-c%20test. The chip sits on your terminal, right above the prompt, so it is the first thing seen on a phone too. It types the command at the prompt and does not press Enter: the player runs it. The playground keeps its own lab and terminals, so the mission stays as it was; Back to Mission 5-4 returns to it.

Git's output above is real: `.scratch/sector7-design/pg_gen.py` built the starting point and typed each line in the person's own clone. Editor screens are drawn: what the editor saved was written to the real file, and git read it from there.
