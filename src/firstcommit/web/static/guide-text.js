"use strict";

/*
 * The words of the field guide's command cards and of its conflict, beside InfographicText (the
 * one-sentence meaning of each command lives there). A card ({command, picture, runs, mistake,
 * lessons, related}) adds to its command: a picture before and after it (a desk or a chain, the
 * game's teaching pictures; `after` left out when the command only looks), the transcripts real
 * git printed (keys of GuideGit.runs), the free playground's start to try it in
 * (`playground`: {start, view, try}, with `try` a real one-line command that works there,
 * docs/drafts/playground/plan.md), the common beginner mistake, the mission that teaches it
 * (`lessons`, the command labels of the missions that teach it, as the map's records carry them;
 * the first such mission in the chapter that tags the command is named) and related commands.
 * Never a level's id: the page does not know them.
 *
 * A desk is {kind: "desk", folder, staging, vault, remote}: only the places it names are drawn,
 * and a place that is null is not there yet. Each holds chips {name, state, fresh}: state is
 * "new", "edited", "conflict", "clean" or "ignored" (left out in the staging area, the vault and the
 * remote), and `fresh` lights what the command just changed; the desk's own `fresh` lists the
 * places that just appeared.
 * A chain is {kind: "chain", commits, names, head}: commits newest first, each {id, parents,
 * who, ghost, fresh, mark}, with `who` "you" (the default), "alex" or "mothership" (a commit the
 * mothership has and you do not) and `mark` a key of pictures.marks said beside it; names [{name,
 * on, kind, fresh, gone}] with kind "branch", "remote" (origin/main, your bookmark) or
 * "mothership" (where the mothership really is), `gone` for a name the command took off; `head`
 * is the branch HEAD rides, or a commit's id when detached. Every after picture lights something.
 *
 * Every word is {en, es}; commands, file names and branch names are said once. Data only.
 * Defines one global, GuideText.
 */

/* exported GuideText */

const GuideText = (function () {
  const desk = (places) => ({ kind: "desk", ...places });
  const chain = (commits, names, head = "main") => ({ kind: "chain", commits, names, head });
  const commit = (id, parents = [], more = {}) => ({ id, parents, ...more });
  const branch = (name, on) => ({ name, on, kind: "branch" });
  const bookmark = (on) => ({ name: "origin/main", on, kind: "remote" });
  const mothership = (on) => ({ name: "mothership", on, kind: "mothership" });

  const cards = [
    {
      command: "ls",
      picture: { before: desk({ folder: [{ name: "map.txt", state: "clean" }] }) },
      runs: ["ls"],
      mistake: {
        en: "Expecting ls to show .git: names that start with a dot are hidden, so only ls -a lists them.",
        es: "Esperar que ls muestre .git: los nombres que empiezan con un punto están ocultos, y solo ls -a los lista.",
      },
      lessons: ["ls · git status"],
      playground: { start: "empty", view: "desk", try: "ls -a" },
      related: ["git status", "git init"],
    },
    {
      command: "git status",
      picture: { before: desk({ folder: [{ name: "fuel.txt", state: "clean" }, { name: "map.txt", state: "edited" }], staging: [{ name: "fuel.txt" }] }) },
      runs: ["status"],
      mistake: {
        en: "Typing it in a folder that is not a repository: Git answers \"not a git repository\". Run git init first, or go into the project's folder.",
        es: "Escribirlo en una carpeta que no es un repositorio: Git responde \"not a git repository\". Primero haz git init, o entra en la carpeta del proyecto.",
      },
      lessons: ["ls · git status"],
      playground: { start: "changes", view: "desk", try: "git status" },
      related: ["git add <file>", "git diff", "git restore --staged <file>"],
    },
    {
      command: "git diff",
      picture: { before: desk({ folder: [{ name: "map.txt", state: "edited" }], staging: [] }) },
      runs: ["diff"],
      mistake: {
        en: "Seeing nothing after git add: git diff compares with the staging area, so lines you staged show only with git diff --staged.",
        es: "No ver nada después de git add: git diff compara con el staging area, así que las líneas que ya agregaste solo salen con git diff --staged.",
      },
      lessons: ["git diff"],
      playground: { start: "changes", view: "desk", try: "git diff" },
      related: ["git status", "git add <file>", "git log"],
    },
    {
      command: "git log",
      picture: { before: chain([commit("b", ["a"]), commit("a")], [branch("main", "b")]) },
      runs: ["log"],
      mistake: {
        en: "Thinking git log shows every commit: it lists only the ones your branch leads back to. git reflog finds the others.",
        es: "Creer que git log muestra todos los commits: solo lista los que alcanza tu branch hacia atrás. git reflog encuentra los demás.",
      },
      lessons: ["git log <file>", "git show <commit>:<file>", "git show HEAD~1:<file>"],
      playground: { start: "branches", view: "chain", try: "git log --oneline" },
      related: ["git commit -m \"<message>\"", "git diff", "git reflog"],
    },
    {
      command: "git init",
      picture: {
        before: desk({ folder: [], staging: null, vault: null }),
        after: desk({ folder: [], staging: [], vault: [], fresh: ["staging", "vault"] }),
      },
      runs: ["init"],
      mistake: {
        en: "Running it in the wrong folder, such as your home folder: that whole folder becomes a repository. Check where you are first.",
        es: "Hacerlo en la carpeta equivocada, como tu carpeta personal: toda esa carpeta se convierte en un repositorio. Primero revisa dónde estás.",
      },
      lessons: ["git init"],
      playground: { start: "empty", view: "desk", try: "git init" },
      related: ["git status", "ls", "git clone <url>"],
    },
    {
      command: "git clone <url>",
      picture: {
        before: chain([commit("b", ["a"], { who: "mothership" }), commit("a", [], { who: "mothership" })], [mothership("b")], "b"),
        after: chain([commit("b", ["a"], { fresh: true }), commit("a", [], { fresh: true })], [branch("main", "b"), bookmark("b"), mothership("b")]),
      },
      runs: ["clone"],
      mistake: {
        en: "Cloning inside another repository's folder: go out of it first, so the copy gets a folder of its own.",
        es: "Clonar dentro de la carpeta de otro repositorio: primero sal de ella, para que la copia tenga su propia carpeta.",
      },
      lessons: ["git clone"],
      playground: { start: "alex-ahead", view: "history", try: "git clone ../github.com/moonbase/project.git ../copy" },
      related: ["git init", "git pull", "git remote add origin <url>"],
    },
    {
      command: "git add <file>",
      picture: {
        before: desk({ folder: [{ name: "map.txt", state: "new" }], staging: [] }),
        after: desk({ folder: [{ name: "map.txt", state: "new" }], staging: [{ name: "map.txt", fresh: true }] }),
      },
      runs: ["add"],
      mistake: {
        en: "Editing the file again after git add: the staging area keeps the version you added, so add it again before you commit.",
        es: "Volver a editar el archivo después de git add: el staging area guarda la versión que agregaste, así que agrégalo otra vez antes del commit.",
      },
      lessons: ["git add", "git add <file> <file>"],
      playground: { start: "changes", view: "desk", try: "git add notes.txt" },
      related: ["git commit -m \"<message>\"", "git restore --staged <file>", "git status"],
    },
    {
      command: "git rm --cached <file>",
      picture: {
        before: desk({ folder: [{ name: "notes.txt", state: "new" }], staging: [{ name: "notes.txt" }] }),
        after: desk({ folder: [{ name: "notes.txt", state: "new", fresh: true }], staging: [] }),
      },
      runs: ["rm-cached"],
      mistake: {
        en: "Leaving out --cached: git rm also deletes the file from your working folder.",
        es: "Olvidar --cached: git rm también borra el archivo de tu carpeta de trabajo.",
      },
      lessons: ["git add <file> <file>"],
      playground: { start: "changes", view: "desk", try: "git rm --cached notes.txt" },
      related: ["git restore --staged <file>", "git add <file>"],
    },
    {
      command: "git restore --staged <file>",
      picture: {
        before: desk({ folder: [{ name: "map.txt", state: "edited" }], staging: [{ name: "map.txt" }] }),
        after: desk({ folder: [{ name: "map.txt", state: "edited", fresh: true }], staging: [] }),
      },
      runs: ["restore-staged"],
      mistake: {
        en: "Leaving out --staged: git restore <file> throws away your edits in the working folder instead.",
        es: "Olvidar --staged: git restore <file> descarta, en cambio, tus ediciones de la carpeta de trabajo.",
      },
      lessons: ["git restore --staged"],
      playground: { start: "changes", view: "desk", try: "git restore --staged notes.txt" },
      related: ["git add <file>", "git restore <file>", "git rm --cached <file>"],
    },
    {
      command: "git commit -m \"<message>\"",
      picture: {
        before: desk({ staging: [{ name: "map.txt" }], vault: [] }),
        after: desk({ staging: [], vault: [{ name: "Add the star map", fresh: true }] }),
      },
      runs: ["commit"],
      mistake: {
        en: "Forgetting git add first: a commit takes only what is staged, so Git answers \"no changes added to commit\".",
        es: "Olvidar git add antes: un commit solo toma lo que está en el staging area, así que Git responde \"no changes added to commit\".",
      },
      lessons: ["git commit -m"],
      playground: { start: "changes", view: "chain", try: "git commit -am \"Note the fuel\"" },
      related: ["git add <file>", "git log", "git push"],
    },
    {
      command: "git remote add origin <url>",
      picture: {
        before: desk({ vault: [{ name: "Add the star map" }], remote: null }),
        after: desk({ vault: [{ name: "Add the star map" }], remote: [], fresh: ["remote"] }),
      },
      runs: ["remote-add"],
      mistake: {
        en: "Expecting it to send your work: it only saves the address. Nothing goes up until git push.",
        es: "Esperar que envíe tu trabajo: solo guarda la dirección. No sube nada hasta que haces git push.",
      },
      lessons: ["git remote add"],
      playground: { start: "branches", view: "history" },
      related: ["git push", "git clone <url>"],
    },
    {
      command: "git push",
      picture: {
        before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "c"), bookmark("b"), mothership("b")]),
        after: chain([commit("c", ["b"], { fresh: true }), commit("b", ["a"]), commit("a")], [branch("main", "c"), bookmark("c"), mothership("c")]),
      },
      runs: ["push-first", "push"],
      mistake: {
        en: "Pushing edits you have not committed: push sends commits only, never what is in your working folder or staging area.",
        es: "Hacer push de ediciones sin commit: push solo envía commits, nunca lo que está en tu carpeta de trabajo o en el staging area.",
      },
      lessons: ["git push"],
      playground: { start: "branches", view: "history", try: "git push" },
      related: ["git commit -m \"<message>\"", "git pull", "git fetch"],
    },
    {
      command: "git fetch",
      picture: {
        before: chain([commit("c", ["b"], { who: "mothership" }), commit("b", ["a"]), commit("a")], [branch("main", "b"), bookmark("b"), mothership("c")]),
        after: chain([commit("c", ["b"], { who: "alex", fresh: true }), commit("b", ["a"]), commit("a")], [branch("main", "b"), bookmark("c"), mothership("c")]),
      },
      runs: ["fetch"],
      mistake: {
        en: "Expecting your files to change: fetch only moves origin/main. git pull, or a merge, brings the commits into your branch.",
        es: "Esperar que cambien tus archivos: fetch solo mueve origin/main. git pull, o un merge, trae los commits a tu branch.",
      },
      lessons: ["git fetch · git pull"],
      playground: { start: "alex-ahead", view: "history", try: "git fetch" },
      related: ["git pull", "git status", "git merge <branch>"],
    },
    {
      command: "git pull",
      picture: {
        before: chain([commit("c", ["b"], { who: "mothership" }), commit("b", ["a"]), commit("a")], [branch("main", "b"), bookmark("b"), mothership("c")]),
        after: chain([commit("c", ["b"], { who: "alex", fresh: true }), commit("b", ["a"]), commit("a")], [branch("main", "c"), bookmark("c"), mothership("c")]),
      },
      runs: ["pull"],
      mistake: {
        en: "Pulling with uncommitted edits to the same files: Git refuses, so it never overwrites them. Commit them first.",
        es: "Hacer pull con ediciones sin commit en los mismos archivos: Git se niega, para no sobrescribirlas. Primero haz commit.",
      },
      lessons: ["git pull"],
      playground: { start: "alex-ahead", view: "history", try: "git pull" },
      related: ["git fetch", "git push", "git merge <branch>"],
    },
    {
      command: "git switch -c <branch>",
      picture: {
        before: chain([commit("b", ["a"]), commit("a")], [branch("main", "b")]),
        after: chain([commit("b", ["a"]), commit("a")], [branch("main", "b"), { ...branch("scout", "b"), fresh: true }], "scout"),
      },
      runs: ["switch-c"],
      mistake: {
        en: "Expecting a copy of your files: a new branch is only a new name tag on the commit you are on.",
        es: "Esperar una copia de tus archivos: un branch nuevo es solo una etiqueta nueva en el commit donde estás.",
      },
      lessons: ["git switch -c"],
      playground: { start: "branches", view: "chain", try: "git switch -c test" },
      related: ["git switch <branch>", "git merge <branch>"],
    },
    {
      command: "git switch <branch>",
      picture: {
        before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("scout", "c"), branch("main", "b")], "scout"),
        after: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("scout", "c"), { ...branch("main", "b"), fresh: true }]),
      },
      runs: ["switch"],
      mistake: {
        en: "Switching with edits the other branch would overwrite: Git refuses. Commit them, or undo them, first.",
        es: "Cambiar de branch con ediciones que el otro branch sobrescribiría: Git se niega. Primero haz commit de ellas, o deshazlas.",
      },
      lessons: ["git branch", "git switch"],
      playground: { start: "branches", view: "chain", try: "git switch bright-lights" },
      related: ["git switch -c <branch>", "git status", "git merge <branch>"],
    },
    {
      command: "git merge <branch>",
      picture: {
        before: chain([commit("d", ["b"], {}), commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("scout", "d"), branch("main", "c")]),
        after: chain([commit("m", ["c", "d"], { fresh: true, mark: "merge" }), commit("d", ["b"], {}), commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "m"), branch("scout", "d")]),
      },
      runs: ["merge"],
      mistake: {
        en: "Thinking a merge deletes the other branch, or copies it over yours: both lines stay, and scout's tag stays where it was.",
        es: "Creer que un merge borra el otro branch, o lo copia encima del tuyo: las dos líneas se quedan, y la etiqueta de scout sigue donde estaba.",
      },
      lessons: ["git merge"],
      playground: { start: "both", view: "chain", try: "git merge origin/main" },
      related: ["git merge --abort", "git switch <branch>", "git pull"],
      conflict: true,
    },
    {
      command: "git merge --abort",
      picture: {
        before: desk({ folder: [{ name: "checklist.txt", state: "conflict" }] }),
        after: desk({ folder: [{ name: "checklist.txt", state: "clean", fresh: true }] }),
      },
      runs: ["merge-abort"],
      mistake: {
        en: "Using it once the merge commit is made: there is no merge left to stop, and Git says so.",
        es: "Usarlo cuando el commit de merge ya está hecho: ya no hay un merge que detener, y Git lo dice.",
      },
      lessons: ["git merge --abort"],
      playground: { start: "conflict", view: "conflict", try: "git merge --abort" },
      related: ["git merge <branch>", "git status"],
      conflict: true,
    },
    {
      command: "git restore <file>",
      picture: {
        before: desk({ folder: [{ name: "map.txt", state: "edited" }], vault: [{ name: "Fill the tanks" }] }),
        after: desk({ folder: [{ name: "map.txt", state: "clean", fresh: true }], vault: [{ name: "Fill the tanks" }] }),
      },
      runs: ["restore"],
      mistake: {
        en: "Expecting to get the edits back: Git never saved them, so nothing can bring them back.",
        es: "Esperar recuperar las ediciones: Git nunca las guardó, así que nada puede traerlas de vuelta.",
      },
      lessons: ["git restore"],
      playground: { start: "changes", view: "desk", try: "git restore notes.txt" },
      related: ["git restore --staged <file>", "git diff", "git revert <commit>"],
    },
    {
      command: "git revert <commit>",
      picture: {
        before: chain([commit("b", ["a"]), commit("a")], [branch("main", "b")]),
        after: chain([commit("r", ["b"], { fresh: true, mark: "revert" }), commit("b", ["a"]), commit("a")], [branch("main", "r")]),
      },
      runs: ["revert"],
      mistake: {
        en: "Expecting the old commit to disappear: it stays in the history, and a new commit undoes it.",
        es: "Esperar que el commit viejo desaparezca: se queda en la historia, y un commit nuevo lo deshace.",
      },
      lessons: ["git revert"],
      playground: { start: "branches", view: "chain", try: "git revert HEAD" },
      related: ["git reset --hard <commit>", "git log", "git push"],
    },
    {
      command: "git reset --hard <commit>",
      picture: {
        before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "c")]),
        after: chain([commit("c", ["b"], { ghost: true }), commit("b", ["a"]), commit("a")], [{ ...branch("main", "b"), fresh: true }]),
      },
      runs: ["reset"],
      mistake: {
        en: "Using --hard with edits you still want: they are gone for good. Commit them first, or leave out --hard to keep your files as they are.",
        es: "Usar --hard con ediciones que todavía quieres: se pierden para siempre. Primero haz commit, o no uses --hard para conservar tus archivos como están.",
      },
      lessons: ["git reset --hard"],
      playground: { start: "branches", view: "chain", try: "git reset --hard HEAD~1" },
      related: ["git revert <commit>", "git reflog", "git restore <file>"],
    },
    {
      command: "git reflog",
      picture: { before: chain([commit("b", ["a"], { ghost: true }), commit("a")], [branch("main", "a")]) },
      runs: ["reflog"],
      mistake: {
        en: "Thinking a commit is gone after a reset: the reflog still lists it, and a new branch on its hash brings it back.",
        es: "Creer que un commit desapareció después de un reset: el reflog todavía lo lista, y un branch nuevo en su hash lo recupera.",
      },
      lessons: ["git reflog"],
      playground: { start: "lost", view: "movelog", try: "git reflog" },
      related: ["git reset --hard <commit>", "git log"],
    },
    {
      command: "git log --oneline --graph --all",
      picture: { before: chain([commit("d", ["b"]), commit("c", ["b"], {}), commit("b", ["a"]), commit("a")], [branch("main", "d"), branch("scout", "c")]) },
      runs: ["log-graph"],
      mistake: {
        en: "Leaving out --all: git log shows only what your branch leads back to, so another branch's commits seem to be missing.",
        es: "Olvidar --all: git log solo muestra lo que alcanza tu branch, así que los commits de otro branch parecen no estar.",
      },
      lessons: ["git switch -c"],
      playground: { start: "branches", view: "graph", try: "git log --oneline --graph --all" },
      related: ["git log", "git branch -v", "git switch -c <branch>"],
    },
    {
      command: ".gitignore",
      picture: {
        before: desk({ folder: [{ name: "map.txt", state: "clean" }, { name: "sim-output/", state: "new" }] }),
        after: desk({ folder: [{ name: ".gitignore", state: "new", fresh: true }, { name: "map.txt", state: "clean" }, { name: "sim-output/", state: "ignored", fresh: true }] }),
      },
      runs: ["gitignore"],
      mistake: {
        en: "Adding a file to .gitignore after it is committed: Git keeps tracking it. Take it out with git rm --cached first.",
        es: "Agregar a .gitignore un archivo que ya tiene commit: Git lo sigue siguiendo. Primero sácalo con git rm --cached.",
      },
      lessons: [".gitignore"],
      playground: { start: "empty", view: "desk" },
      related: ["git status", "git add <file>", "git rm --cached <file>"],
    },
    {
      command: "git push -u origin <branch>",
      picture: {
        before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("scout", "c"), branch("main", "b"), bookmark("b")], "scout"),
        after: chain([commit("c", ["b"], { fresh: true }), commit("b", ["a"]), commit("a")], [branch("scout", "c"), { name: "origin/scout", on: "c", kind: "remote", fresh: true }, branch("main", "b"), bookmark("b")], "scout"),
      },
      runs: ["push-branch"],
      mistake: {
        en: "A plain git push on a new branch: it has no upstream yet, so Git stops and asks for one. Add -u origin <branch> the first time.",
        es: "Un git push solo en un branch nuevo: todavía no tiene upstream, así que Git se detiene y lo pide. La primera vez agrega -u origin <branch>.",
      },
      lessons: ["git push -u origin <branch>"],
      playground: { start: "branches", view: "history", try: "git push -u origin bright-lights" },
      related: ["git push", "git switch -c <branch>", "git branch -v"],
    },
    {
      command: "git pull --no-rebase",
      picture: {
        before: chain([commit("d", ["b"], { who: "mothership" }), commit("c", ["b"]), commit("b", ["a"]), commit("a")], [mothership("d"), branch("main", "c"), bookmark("b")]),
        after: chain([commit("m", ["c", "d"], { fresh: true, mark: "merge" }), commit("d", ["b"], { who: "alex" }), commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "m"), bookmark("d"), mothership("d")]),
      },
      runs: ["pull-no-rebase"],
      mistake: {
        en: "Pushing again and again after \"rejected\": the mothership has commits you lack. Pull them in first, then push.",
        es: "Hacer push una y otra vez después de \"rejected\": la nave nodriza tiene commits que tú no tienes. Primero tráelos con pull, luego haz push.",
      },
      lessons: ["git pull --no-rebase"],
      playground: { start: "both", view: "history", try: "git pull --no-rebase" },
      related: ["git pull", "git push", "git merge <branch>"],
    },
    {
      command: "git branch <name>",
      picture: {
        before: chain([commit("b", ["a"]), commit("a")], [branch("main", "b")]),
        after: chain([commit("b", ["a"]), commit("a")], [branch("main", "b"), { ...branch("test-run", "b"), fresh: true }]),
      },
      runs: ["branch"],
      mistake: {
        en: "Expecting to be on the new branch: git branch only puts the name there. git switch takes you to it.",
        es: "Esperar estar en el branch nuevo: git branch solo pone el nombre. git switch te lleva a él.",
      },
      lessons: ["git branch"],
      playground: { start: "branches", view: "chain", try: "git branch test" },
      related: ["git switch <branch>", "git switch -c <branch>", "git branch -v"],
    },
    {
      command: "git branch <name> <commit>",
      picture: {
        before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "c")]),
        after: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "c"), { ...branch("first-route", "a"), fresh: true }]),
      },
      runs: ["branch-at"],
      mistake: {
        en: "Typing a commit's message instead of its hash: Git needs the hash, the first word of each line of git log --oneline.",
        es: "Escribir el mensaje del commit en vez de su hash: Git necesita el hash, la primera palabra de cada línea de git log --oneline.",
      },
      lessons: ["git branch <name> <commit>"],
      playground: { start: "branches", view: "chain", try: "git branch first HEAD~2" },
      related: ["git branch <name>", "git branch -d <name>", "git log --oneline --graph --all"],
    },
    {
      command: "git branch -d <name>",
      picture: {
        before: chain([commit("b", ["a"]), commit("a")], [branch("main", "b"), branch("test-run", "a")]),
        after: chain([commit("b", ["a"]), commit("a")], [branch("main", "b"), { ...branch("test-run", "a"), gone: true }]),
      },
      runs: ["branch-d"],
      mistake: {
        en: "Thinking the commits go with the name: only the name goes. A commit another name leads to stays in the history.",
        es: "Creer que los commits se van con el nombre: solo se va el nombre. Un commit al que lleva otro nombre se queda en la historia.",
      },
      lessons: ["git branch <name> <commit>"],
      playground: { start: "branches", view: "chain", try: "git branch -d quiet-engine" },
      related: ["git branch <name>", "git branch -v", "git reflog"],
    },
    {
      command: "git branch -v",
      picture: { before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("scout", "c"), branch("main", "b"), bookmark("b")]) },
      runs: ["branch-v"],
      mistake: {
        en: "Looking for origin/main in the list: git branch shows your own names only. git branch -r shows your bookmarks of the remote.",
        es: "Buscar origin/main en la lista: git branch solo muestra tus propios nombres. git branch -r muestra tus marcadores del remoto.",
      },
      lessons: ["git branch -v"],
      playground: { start: "branches", view: "chain", try: "git branch -v" },
      related: ["git branch <name>", "git log --oneline --graph --all", "git status"],
    },
    {
      command: "git checkout -b <branch>",
      picture: {
        before: chain([commit("b", ["a"]), commit("a")], [branch("scout", "b")], "scout"),
        after: chain([commit("b", ["a"]), commit("a")], [branch("scout", "b"), { ...branch("night-watch", "b"), fresh: true }], "night-watch"),
      },
      runs: ["checkout-b"],
      mistake: {
        en: "Leaving out -b: git checkout <name> then looks for a branch or a file of that name, and does something else entirely.",
        es: "Olvidar -b: git checkout <name> busca entonces un branch o un archivo con ese nombre, y hace algo muy distinto.",
      },
      lessons: ["git switch -c"],
      playground: { start: "branches", view: "chain", try: "git checkout -b test" },
      related: ["git switch -c <branch>", "git checkout <branch>"],
    },
    {
      command: "git checkout <branch>",
      picture: {
        before: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("scout", "c"), branch("main", "b")]),
        after: chain([commit("c", ["b"]), commit("b", ["a"]), commit("a")], [{ ...branch("scout", "c"), fresh: true }, branch("main", "b")], "scout"),
      },
      runs: ["checkout"],
      mistake: {
        en: "Giving it a file name: git checkout <file> throws away that file's edits, like git restore. git switch only ever switches.",
        es: "Darle el nombre de un archivo: git checkout <file> descarta las ediciones de ese archivo, como git restore. git switch solo cambia de branch.",
      },
      lessons: ["git switch -c"],
      playground: { start: "branches", view: "chain", try: "git checkout quiet-engine" },
      related: ["git switch <branch>", "git checkout -b <branch>", "git restore <file>"],
    },
    {
      command: "git restore --theirs <file>",
      picture: {
        before: desk({ folder: [{ name: "checklist.txt", state: "conflict" }], staging: [] }),
        after: desk({ folder: [{ name: "checklist.txt", state: "edited", fresh: true }], staging: [] }),
      },
      runs: ["restore-theirs"],
      mistake: {
        en: "Expecting it to touch only the conflict: it takes Alex's whole file, so your full tanks went back to half. Read the file before git add.",
        es: "Esperar que solo toque el conflicto: toma el archivo entero de Alex, así que tus tanques llenos volvieron a la mitad. Lee el archivo antes de git add.",
      },
      lessons: ["git restore --theirs"],
      playground: { start: "conflict", view: "conflict", try: "git restore --theirs checklist.txt" },
      related: ["git merge <branch>", "git commit --no-edit", "git merge --abort"],
      conflict: true,
    },
    {
      command: "git mergetool",
      picture: {
        before: desk({ folder: [{ name: "checklist.txt", state: "conflict" }], staging: [] }),
        after: desk({ folder: [{ name: "checklist.txt", state: "clean" }], staging: [{ name: "checklist.txt", fresh: true }] }),
      },
      runs: ["mergetool"],
      mistake: {
        en: "Running it with no file in conflict: Git says No files need merging and opens no tool. It works only on files a merge left in conflict.",
        es: "Ejecutarlo sin ningún archivo en conflicto: Git dice No files need merging y no abre ninguna herramienta. Solo funciona con los archivos que un merge dejó en conflicto.",
      },
      lessons: ["git mergetool"],
      playground: { start: "conflict", view: "conflict", try: "git mergetool" },
      related: ["git restore --theirs <file>", "git commit --no-edit", "git merge --abort"],
      conflict: true,
    },
    {
      command: "git commit --no-edit",
      picture: {
        before: chain([commit("d", ["b"], { who: "alex" }), commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("alex-route", "d"), branch("main", "c")]),
        after: chain([commit("m", ["c", "d"], { fresh: true, mark: "merge" }), commit("d", ["b"], { who: "alex" }), commit("c", ["b"]), commit("b", ["a"]), commit("a")], [branch("main", "m"), branch("alex-route", "d")]),
      },
      runs: ["conflict-commit-yours"],
      mistake: {
        en: "Committing before git add: while a file still has conflict markers, Git refuses to make the merge commit.",
        es: "Hacer commit antes de git add: mientras un archivo tenga marcadores de conflicto, Git se niega a crear el commit de merge.",
      },
      lessons: ["git restore --theirs"],
      playground: { start: "conflict", view: "conflict", try: "git commit --no-edit" },
      related: ["git merge <branch>", "git restore --theirs <file>", "git log --oneline --graph --all"],
      conflict: true,
    },
  ];

  return Object.freeze({
    card: {
      open: { en: "More about {command}", es: "Más sobre {command}" },
      close: { en: "Close", es: "Cerrar" },
      before: { en: "Before", es: "Antes" },
      after: { en: "After", es: "Después" },
      onlyLooks: { en: "Nothing changes: it only looks.", es: "No cambia nada: solo mira." },
      prints: { en: "What git prints", es: "Lo que imprime git" },
      silent: { en: "(prints nothing)", es: "(no imprime nada)" },
      mistake: { en: "Common mistake", es: "Error común" },
      taught: { en: "Where you learn it", es: "Dónde lo aprendes" },
      taughtAt: { en: "Sector {sector}, mission {mission}: {title}", es: "Sector {sector}, misión {mission}: {title}" },
      taughtIn: { en: "Sector {sector}: {title}", es: "Sector {sector}: {title}" },
      taughtLater: { en: "A sector still to come", es: "Un sector que aún no llega" },
      related: { en: "Related", es: "Relacionados" },
      conflict: { en: "See a conflict, step by step", es: "Ver un conflicto, paso a paso" },
      chainKey: {
        en: "HEAD marks where you are; a dashed name is your bookmark of the mothership.",
        es: "HEAD marca dónde estás; un nombre con borde punteado es tu marcador de la nave nodriza.",
      },
      showAll: { en: "Show all {count} lines", es: "Mostrar las {count} líneas" },
      showLess: { en: "Show fewer lines", es: "Mostrar menos líneas" },
      tryIt: { en: "Try it in the playground", es: "Pruébalo en la zona de pruebas" },
    },
    pictures: {
      notYet: { en: "not there yet", es: "todavía no existe" },
      empty: { en: "empty", es: "vacío" },
      head: { en: "HEAD, you are here", es: "HEAD, estás aquí" },
      states: {
        new: { en: "new", es: "nuevo" },
        edited: { en: "edited", es: "editado" },
        conflict: { en: "conflict", es: "conflicto" },
        clean: { en: "saved", es: "guardado" },
        ignored: { en: "ignored", es: "ignorado" },
      },
      ghost: { en: "no name leads here", es: "ningún nombre lleva aquí" },
      marks: {
        merge: { en: "merge commit", es: "commit de merge" },
        revert: { en: "undoes the one below", es: "deshace el de abajo" },
      },
      gone: { en: "taken off", es: "quitado" },
      mothership: { en: "mothership", es: "nave nodriza" },
      notYours: { en: "on the mothership only", es: "solo en la nave nodriza" },
      by: { you: { en: "your commit", es: "tu commit" }, alex: { en: "Alex's commit", es: "commit de Alex" } },
    },
    cards,
    conflict: {
      title: { en: "When a merge stops: a conflict", es: "Cuando un merge se detiene: un conflicto" },
      lede: {
        en: "You aimed for the Moon on main; Alex aimed for Jupiter on alex-route. Both changed line 4, so git merge stopped. This is the real file git wrote.",
        es: "Tú pusiste rumbo a la Luna en main; Alex puso rumbo a Júpiter en alex-route. Los dos cambiaron la línea 4, así que git merge se detuvo. Este es el archivo real que escribió git.",
      },
      playground: { start: "conflict", view: "conflict" },
      tryIt: { en: "Try a conflict in the playground", es: "Prueba un conflicto en la zona de pruebas" },
      steps: [
        { en: "Git stopped the merge and wrote both versions of the course line into the file, between marker lines.", es: "Git detuvo el merge y escribió las dos versiones de la línea del rumbo en el archivo, entre líneas marcadoras." },
        { en: "From <<<<<<< HEAD to =======: your version. HEAD is the branch you are on, main.", es: "De <<<<<<< HEAD a =======: tu versión. HEAD es el branch donde estás, main." },
        { en: "From ======= to >>>>>>> alex-route: Alex's version, named after Alex's branch.", es: "De ======= a >>>>>>> alex-route: la versión de Alex, con el nombre de su branch." },
        { en: "Everything outside the markers is already merged: your full tanks and Alex's noodles.", es: "Todo lo que está fuera de los marcadores ya está mezclado: tus tanques llenos y los fideos de Alex." },
        { en: "Click the side you want to keep: yours, Alex's, or both. The markers go and the rest stays as Git merged it.", es: "Haz clic en el lado que quieres conservar: el tuyo, el de Alex o los dos. Los marcadores se van y el resto queda como Git lo mezcló." },
        { en: "git add tells Git this file is resolved: git add checklist.txt.", es: "git add le dice a Git que este archivo está resuelto: git add checklist.txt." },
        { en: "git commit makes the merge commit. It has two parents: your last commit and Alex's.", es: "git commit crea el commit de merge. Tiene dos padres: tu último commit y el de Alex." },
      ],
      silent: { en: "(prints nothing)", es: "(no imprime nada)" },
      back: { en: "Back", es: "Atrás" },
      next: { en: "Next", es: "Siguiente" },
      count: { en: "Step {step} of {steps}", es: "Paso {step} de {steps}" },
      hint: { en: "Point at, tap or Tab to any line of the file to see what it is.", es: "Señala o toca cualquier línea del archivo, o recórrelas con la tecla Tab, para ver qué es." },
      bothModified: {
        en: "\"both modified\" is git status's word for this file: you and Alex both changed it since your branches split.",
        es: "\"both modified\" es como git status llama a este archivo: tú y Alex lo cambiaron desde que se separaron sus branches.",
      },
      parts: {
        wrote: { title: { en: "What Git wrote", es: "Lo que escribió Git" }, text: { en: "Both versions of the course line, one after the other, between three marker lines. Git did not pick: it left the question in the file.", es: "Las dos versiones de la línea del rumbo, una después de la otra, entre tres líneas marcadoras. Git no eligió: dejó la pregunta en el archivo." } },
        "ours-start": { title: { en: "<<<<<<< HEAD", es: "<<<<<<< HEAD" }, text: { en: "Start of your side. HEAD is the branch you are on: main, at your commit {yourCommit}. This line is not part of the checklist; it goes when you resolve.", es: "Empieza tu lado. HEAD es el branch donde estás: main, en tu commit {yourCommit}. Esta línea no es parte de la lista; se va cuando resuelves." } },
        ours: { title: { en: "Your version", es: "Tu versión" }, text: { en: "What the line says on main (commit {yourCommit}).", es: "Lo que dice la línea en main (commit {yourCommit})." } },
        fence: { title: { en: "=======", es: "=======" }, text: { en: "The fence between the two sides. Above it: yours. Below it: Alex's. It goes when you resolve.", es: "La separación entre los dos lados. Arriba: el tuyo. Abajo: el de Alex. Se va cuando resuelves." } },
        theirs: { title: { en: "Alex's version", es: "La versión de Alex" }, text: { en: "What the line says on alex-route (commit {alexCommit}).", es: "Lo que dice la línea en alex-route (commit {alexCommit})." } },
        "theirs-end": { title: { en: ">>>>>>> alex-route", es: ">>>>>>> alex-route" }, text: { en: "End of Alex's side, named after the branch you are merging in. It goes when you resolve.", es: "Termina el lado de Alex, con el nombre del branch que estás mezclando. Se va cuando resuelves." } },
        "clean-you": { title: { en: "Merged already: your change", es: "Ya mezclado: tu cambio" }, text: { en: "Only you changed this line, so Git took your version without asking.", es: "Solo tú cambiaste esta línea, así que Git tomó tu versión sin preguntar." } },
        "clean-alex": { title: { en: "Merged already: Alex's change", es: "Ya mezclado: el cambio de Alex" }, text: { en: "Only Alex changed this line, so Git took Alex's version without asking.", es: "Solo Alex cambió esta línea, así que Git tomó la versión de Alex sin preguntar." } },
        clean: { title: { en: "Untouched", es: "Sin cambios" }, text: { en: "Nobody changed this line. It stays as it was.", es: "Nadie cambió esta línea. Se queda como estaba." } },
      },
      who: {
        you: { en: "You", es: "Tú" },
        alex: { en: "Alex", es: "Alex" },
        youMerged: { en: "You, merged", es: "Tú, ya mezclado" },
        alexMerged: { en: "Alex, merged", es: "Alex, ya mezclado" },
      },
      legend: {
        start: { en: "your side starts (HEAD = main)", es: "empieza tu lado (HEAD = main)" },
        fence: { en: "the fence between sides", es: "la separación entre los lados" },
        end: { en: "Alex's side ends", es: "termina el lado de Alex" },
      },
      keep: {
        title: { en: "Keep which side?", es: "¿Qué lado conservas?" },
        hint: { en: "Click a side in the file, or use these. Click again to change your mind.", es: "Haz clic en un lado del archivo, o usa estos botones. Vuelve a hacer clic para cambiar de idea." },
        yours: { en: "Mine", es: "El mío" },
        theirs: { en: "Alex's", es: "El de Alex" },
        both: { en: "Both: mine, then Alex's", es: "Los dos: el mío y luego el de Alex" },
        reset: { en: "Start over", es: "Empezar de nuevo" },
        pickYours: { en: "keep yours?", es: "¿conservar el tuyo?" },
        pickTheirs: { en: "keep Alex's?", es: "¿conservar el de Alex?" },
        kept: { en: "keep", es: "conservar" },
        pickLabel: { en: "{line}: {side}, keep it", es: "{line}: {side}, conservarlo" },
        yourSide: { en: "your side", es: "tu lado" },
        alexSide: { en: "Alex's side", es: "el lado de Alex" },
        both2: { en: "Two course lines. Git accepts whatever the file says, so check the checklist still makes sense.", es: "Dos líneas de rumbo. Git acepta lo que diga el archivo, así que revisa que la lista todavía tenga sentido." },
        byHand: { en: "In any editor you would do this by hand: delete the three marker lines and the side you don't keep, then save.", es: "En cualquier editor lo harías a mano: borra las tres líneas marcadoras y el lado que no conservas, y guarda." },
        none: { en: "Click a side in the file to keep it.", es: "Haz clic en un lado del archivo para conservarlo." },
      },
      file: {
        conflicted: { en: "both modified", es: "both modified" },
        nothing: { en: "nothing kept yet", es: "nada conservado todavía" },
        saved: { en: "markers gone, saved", es: "sin marcadores, guardado" },
        added: { en: "resolved (added)", es: "resuelto (agregado)" },
        committed: { en: "committed", es: "en un commit" },
        keptYours: { en: "kept: yours", es: "conservado: el tuyo" },
        keptTheirs: { en: "kept: Alex's", es: "conservado: el de Alex" },
        merged: { en: "merged by Git, untouched", es: "mezclado por Git, sin tocar" },
        withMarkers: { en: "checklist.txt with conflict markers", es: "checklist.txt con marcadores de conflicto" },
        resolved: { en: "checklist.txt resolved", es: "checklist.txt resuelto" },
      },
      diamond: {
        label: { en: "Merge commit {merge} with parents {first} and {second}", es: "Commit de merge {merge} con padres {first} y {second}" },
        top: { en: "main: the merge commit", es: "main: el commit de merge" },
        first: { en: "parent 1: yours", es: "padre 1: el tuyo" },
        second: { en: "parent 2: Alex's", es: "padre 2: el de Alex" },
        base: { en: "where you both started", es: "donde empezaron los dos" },
      },
    },
  });
})();
