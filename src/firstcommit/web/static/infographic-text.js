"use strict";

/*
 * Every word of the infographics, in one place so it can be fact-checked and translated: the
 * commands the game teaches, grouped by what they do; Git's four places and the commands that
 * move work between them; a file's states and what moves a file from one to the next. Each
 * place has its real Git name (`name`, shown first), its space word (`space`, shown after it in
 * parentheses) and the zone panel's Git term (`git`). Every word is given as {en, es}; ids, lessons and
 * commands that are only a command are said once. Each item says where the game teaches it
 * (`taught`): a number of its chapter's levels finished ({chapter: id, levels: n}, in any order)
 * or the whole chapter ({chapter: id}); never a level's id, which the page does not know. The
 * guide shows every item from the start, and tags one not taught yet with its sector. A command
 * that looks like a neighbour has a `short` subtitle that tells them apart. Data
 * only. Defines one global, InfographicText.
 */

/* exported InfographicText */

const InfographicText = Object.freeze({
  title: { en: "Field guide", es: "Guía de campo" },
  lede: {
    en: "Everything the missions teach. Click a command for its picture, what git prints and the usual mistake. What a sector still ahead teaches is tagged with it.",
    es: "Todo lo que enseñan las misiones. Haz clic en un comando para ver su imagen, lo que imprime git y el error común. Lo que enseña un sector que aún tienes por delante lleva su marca.",
  },
  jump: {
    label: { en: "Jump to", es: "Ir a" },
    places: { en: "Places", es: "Lugares" },
    states: { en: "File states", es: "Estados" },
    commands: { en: "Commands", es: "Comandos" },
    conflict: { en: "Conflict", es: "Conflicto" },
  },
  upcoming: { en: "Coming up in sector {sector}", es: "Llega en el sector {sector}" },
  later: { en: "Coming up later", es: "Llega más adelante" },

  commands: {
    title: { en: "Every command, by what it does", es: "Todos los comandos, según lo que hacen" },
    groups: [
      {
        title: { en: "Look around", es: "Mirar a tu alrededor" },
        commands: [
          {
            command: "ls",
            what: { en: "Lists the files in the current folder; ls -a lists the hidden ones too.", es: "Muestra los archivos de la carpeta actual; ls -a muestra también los ocultos." },
            taught: { chapter: "liftoff", levels: 1 },
          },
          {
            command: "git status",
            what: { en: "Says which files are untracked, modified or staged, and which branch you are on.", es: "Dice qué archivos están sin seguimiento, modificados o en el staging area, y en qué branch estás." },
            taught: { chapter: "liftoff", levels: 1 },
          },
          {
            command: "git diff",
            what: { en: "Shows the lines you changed and have not staged; git diff --staged shows what is staged.", es: "Muestra las líneas que cambiaste y aún no pasaste al staging area; git diff --staged muestra lo que ya está en el staging area." },
            taught: { chapter: "vault" },
          },
          {
            command: "git log",
            what: { en: "Lists the commits, newest first, with their hash, author and message.", es: "Lista los commits, del más reciente al más antiguo, con su hash, su autor y su mensaje." },
            taught: { chapter: "vault" },
          },
          {
            command: "git log --oneline --graph --all",
            what: { en: "Draws every branch's commits as a tree, one line each, with the names on them.", es: "Dibuja los commits de todos los branches como un árbol, uno por línea, con sus nombres." },
            taught: { chapter: "names" },
          },
        ],
      },
      {
        title: { en: "Start a repository", es: "Crear un repositorio" },
        commands: [
          {
            command: "git init",
            what: { en: "Makes the current folder a repository: Git creates the hidden .git folder.", es: "Convierte la carpeta actual en un repositorio: Git crea la carpeta oculta .git." },
            taught: { chapter: "liftoff", levels: 2 },
          },
          {
            command: "git clone <url>",
            what: { en: "Copies a remote repository, its whole history included, into a new folder.", es: "Copia un repositorio remoto, con toda su historia, en una carpeta nueva." },
            taught: { chapter: "mothership" },
          },
        ],
      },
      {
        title: { en: "Stage and commit", es: "Agregar al staging area y hacer commit" },
        commands: [
          {
            command: "git add <file>",
            what: { en: "Copies a file, as it is now, from the working folder into the staging area.", es: "Copia un archivo, tal como está ahora, de la carpeta de trabajo al staging area." },
            taught: { chapter: "cargo", levels: 1 },
          },
          {
            command: "git rm --cached <file>",
            what: {
              en: "Takes a file out of the staging area and keeps it in the working folder. For a file the last commit holds, the next commit then deletes it from the repository.",
              es: "Saca un archivo del staging area y lo deja en la carpeta de trabajo. Si el último commit tiene ese archivo, el próximo commit lo borra del repositorio.",
            },
            taught: { chapter: "cargo" },
          },
          {
            command: ".gitignore",
            what: { en: "Not a command but a file: it lists names Git leaves alone, such as build output, so git status and git add . skip them.", es: "No es un comando sino un archivo: lista los nombres que Git deja en paz, como lo que genera un programa, así que git status y git add . los saltan." },
            taught: { chapter: "cargo" },
          },
          {
            command: "git restore --staged <file>",
            short: { en: "unstage a file", es: "sacar del staging area" },
            what: { en: "Unstages a file: the staging area gets back the version of the last commit.", es: "Saca un archivo del staging area: el staging area recupera la versión del último commit." },
            taught: { chapter: "cargo" },
          },
          {
            command: "git commit -m \"<message>\"",
            what: { en: "Saves the staging area as a new commit in your local repository.", es: "Guarda el staging area como un commit nuevo en tu repositorio local." },
            taught: { chapter: "vault" },
          },
        ],
      },
      {
        title: { en: "Share with the remote", es: "Compartir con el remoto" },
        commands: [
          {
            command: "git remote add origin <url>",
            what: { en: "Gives a remote repository's address a short name, usually origin. Nothing is sent.", es: "Da un nombre corto, normalmente origin, a la dirección de un repositorio remoto. No se envía nada." },
            taught: { chapter: "mothership" },
          },
          {
            command: "git push",
            short: { en: "send your commits", es: "enviar tus commits" },
            what: { en: "Sends your branch's new commits to the remote repository.", es: "Envía los commits nuevos de tu branch al repositorio remoto." },
            taught: { chapter: "mothership" },
          },
          {
            command: "git push -u origin <branch>",
            short: { en: "a new branch, the first time", es: "un branch nuevo, la primera vez" },
            what: { en: "Sends a new branch to the remote and makes origin/<branch> its upstream, so a plain git push works from then on.", es: "Envía un branch nuevo al remoto y hace de origin/<branch> su upstream, así que desde entonces basta con git push." },
            taught: { chapter: "branch" },
          },
          {
            command: "git fetch",
            what: { en: "Downloads the remote's new commits and updates origin/main; your branch and files stay as they are.", es: "Descarga los commits nuevos del remoto y actualiza origin/main; tu branch y tus archivos se quedan como están." },
            taught: { chapter: "mothership" },
          },
          {
            command: "git pull",
            short: { en: "fetch, then bring in", es: "fetch, y luego traerlos" },
            what: {
              en: "A fetch, then brings the remote's commits into your branch: a fast-forward when only the remote moved on; when both did, you choose a merge (--no-rebase) or a rebase (--rebase).",
              es: "Hace fetch y luego trae los commits del remoto a tu branch: un fast-forward si solo avanzó el remoto; si avanzaron los dos, eliges un merge (--no-rebase) o un rebase (--rebase).",
            },
            taught: { chapter: "mothership" },
          },
          {
            command: "git pull --no-rebase",
            short: { en: "when both moved on", es: "cuando los dos avanzaron" },
            what: { en: "When you and the remote both moved on, brings the remote's commits in with a merge commit.", es: "Cuando tú y el remoto avanzaron, trae los commits del remoto con un commit de merge." },
            taught: { chapter: "mothership" },
          },
        ],
      },
      {
        title: { en: "Name tags", es: "Etiquetas" },
        commands: [
          {
            command: "git branch <name>",
            short: { en: "a name where you are", es: "un nombre donde estás" },
            what: { en: "Puts a new name tag on the commit you are on. You stay where you are.", es: "Pone una etiqueta nueva en el commit donde estás. Tú te quedas donde estás." },
            taught: { chapter: "names" },
          },
          {
            command: "git branch <name> <commit>",
            short: { en: "a name on any commit", es: "un nombre en cualquier commit" },
            what: { en: "Puts a new name on any commit, given by its hash. You stay where you are.", es: "Pone un nombre nuevo en cualquier commit, indicado por su hash. Tú te quedas donde estás." },
            taught: { chapter: "names" },
          },
          {
            command: "git branch -d <name>",
            short: { en: "take a name off", es: "quitar un nombre" },
            what: { en: "Takes a name off; its commits stay. Git refuses to take off the name HEAD rides, or one whose work no other name leads to.", es: "Quita un nombre; sus commits se quedan. Git no quita el nombre en el que va HEAD, ni uno con trabajo al que no lleva ningún otro nombre." },
            taught: { chapter: "names" },
          },
          {
            command: "git branch -v",
            short: { en: "list the names", es: "listar los nombres" },
            what: { en: "Lists your branches with the commit each one names; * marks the one HEAD is on. git branch -r lists your origin/ bookmarks.", es: "Lista tus branches con el commit que nombra cada uno; * marca aquel donde está HEAD. git branch -r lista tus marcadores origin/." },
            taught: { chapter: "names" },
          },
        ],
      },
      {
        title: { en: "Branches and merges", es: "Branches y merges" },
        commands: [
          {
            command: "git switch -c <branch>",
            short: { en: "a new branch, and go there", es: "un branch nuevo, y vas a él" },
            what: { en: "Creates a branch, a movable label on a commit, and switches to it.", es: "Crea un branch, una etiqueta que se mueve de commit en commit, y te cambia a él." },
            taught: { chapter: "names" },
          },
          {
            command: "git switch <branch>",
            short: { en: "go to a branch", es: "ir a un branch" },
            what: { en: "Moves HEAD to another branch; the working folder takes that branch's files.", es: "Mueve HEAD a otro branch; la carpeta de trabajo pasa a tener los archivos de ese branch." },
            taught: { chapter: "names" },
          },
          {
            command: "git checkout -b <branch>",
            short: { en: "older form of switch -c", es: "forma antigua de switch -c" },
            what: { en: "The older form of git switch -c: creates a branch and switches to it.", es: "La forma antigua de git switch -c: crea un branch y te cambia a él." },
            taught: { chapter: "names" },
          },
          {
            command: "git checkout <branch>",
            short: { en: "older form of switch", es: "forma antigua de switch" },
            what: { en: "The older form of git switch: moves HEAD to another branch.", es: "La forma antigua de git switch: mueve HEAD a otro branch." },
            taught: { chapter: "names" },
          },
          {
            command: "git merge <branch>",
            what: { en: "Joins another branch's history into yours, with a merge commit when both moved on.", es: "Une la historia de otro branch a la tuya, con un commit de merge si los dos avanzaron." },
            taught: { chapter: "conflict" },
          },
          {
            command: "git merge --abort",
            what: { en: "Stops a merge in progress and puts everything back as it was before it.", es: "Detiene un merge a medias y deja todo como estaba antes de empezarlo." },
            taught: { chapter: "conflict" },
          },
          {
            command: "git restore --theirs <file>",
            what: { en: "During a conflict, takes the other side's whole file, the lines Git had merged from yours too; then git add it.", es: "Durante un conflicto, toma el archivo entero del otro lado, también las líneas que Git ya había mezclado del tuyo; luego haz git add." },
            taught: { chapter: "conflict" },
          },
          {
            command: "git commit --no-edit",
            what: { en: "Finishes a merge with the message Git prepared, without opening an editor.", es: "Termina un merge con el mensaje que preparó Git, sin abrir un editor." },
            taught: { chapter: "conflict" },
          },
        ],
      },
      {
        title: { en: "Undo", es: "Deshacer" },
        commands: [
          {
            command: "git restore <file>",
            short: { en: "drop your edits", es: "descartar tus ediciones" },
            what: { en: "Replaces the working copy with the staged or committed version. Unsaved lines are gone for good.", es: "Reemplaza la copia de trabajo por la versión del staging area o la del último commit. Las líneas sin guardar se pierden para siempre." },
            taught: { chapter: "undo" },
          },
          {
            command: "git revert <commit>",
            what: { en: "Adds a new commit that undoes an earlier one, safe for history others already have.", es: "Agrega un commit nuevo que deshace uno anterior; es seguro con una historia que otros ya tienen." },
            taught: { chapter: "undo" },
          },
          {
            command: "git reset --hard <commit>",
            what: {
              en: "Moves the current branch's label to another commit, and makes the staging area and the working folder match it: edits not committed are gone. Without --hard, your files stay as they are.",
              es: "Mueve la etiqueta del branch actual a otro commit, y hace que el staging area y la carpeta de trabajo coincidan con él: las ediciones sin commit se pierden. Sin --hard, tus archivos se quedan como están.",
            },
            taught: { chapter: "undo" },
          },
          {
            command: "git reflog",
            what: { en: "Lists where HEAD has been, so a commit no branch points to can be found again.", es: "Lista por dónde pasó HEAD, para volver a encontrar un commit al que ya no apunta ningún branch." },
            taught: { chapter: "undo" },
          },
        ],
      },
    ],
  },

  places: {
    title: { en: "Git's four places", es: "Los cuatro lugares de Git" },
    places: [
      {
        id: "workshop",
        name: { en: "Working folder", es: "Carpeta de trabajo" },
        space: { en: "Workshop", es: "Taller" },
        git: { en: "working folder", es: "carpeta de trabajo" },
        what: { en: "Your files as you edit them. Git saves nothing here until you add and commit.", es: "Tus archivos mientras los editas. Git no guarda nada aquí hasta que los agregas al staging area y haces un commit." },
        taught: { chapter: "liftoff", levels: 1 },
      },
      {
        id: "dock",
        name: { en: "Staging area", es: "Staging area" },
        space: { en: "Cargo dock", es: "Muelle de carga" },
        git: { en: "staging area", es: "staging area" },
        what: { en: "The files you chose for your next commit, as they were when you added them.", es: "Los archivos que elegiste para tu próximo commit, tal como estaban cuando los agregaste." },
        taught: { chapter: "cargo", levels: 1 },
      },
      {
        id: "vault",
        name: { en: "Repository", es: "Repositorio" },
        space: { en: "Vault", es: "Bóveda" },
        git: { en: "local repository", es: "repositorio local" },
        what: { en: "Every commit of your repository, yours and the ones you fetched, on this computer, in the hidden .git folder.", es: "Todos los commits de tu repositorio, los tuyos y los que trajiste con fetch, en esta computadora, dentro de la carpeta oculta .git." },
        taught: { chapter: "liftoff", levels: 2 },
      },
      {
        id: "mothership",
        name: { en: "Remote", es: "Remoto" },
        space: { en: "Mothership", es: "Nave nodriza" },
        git: { en: "remote repository", es: "repositorio remoto" },
        what: { en: "A copy of the repository on a server, such as GitHub, shared with your team.", es: "Una copia del repositorio en un servidor, como GitHub, que compartes con tu equipo." },
        taught: { chapter: "mothership" },
      },
    ],
    moves: [
      { from: "workshop", to: "dock", command: "git add", taught: { chapter: "cargo", levels: 1 } },
      { from: "dock", to: "workshop", command: "git restore --staged", taught: { chapter: "cargo" } },
      { from: "dock", to: "vault", command: "git commit", taught: { chapter: "vault" } },
      { from: "vault", to: "workshop", command: "git switch, git restore", taught: { chapter: "names" } },
      { from: "vault", to: "mothership", command: "git push", taught: { chapter: "mothership" } },
      { from: "mothership", to: "vault", command: "git fetch", taught: { chapter: "mothership" } },
      { from: "mothership", to: "workshop", command: { en: "git pull (fetch, then merge or rebase)", es: "git pull (fetch y luego merge o rebase)" }, taught: { chapter: "mothership" } },
    ],
  },

  states: {
    title: { en: "A file's states", es: "Los estados de un archivo" },
    states: [
      {
        id: "untracked",
        name: { en: "untracked", es: "sin seguimiento" },
        space: { en: "new in the workshop", es: "nuevo en el taller" },
        what: { en: "In the working folder, in no commit and not staged. Git does not follow it yet.", es: "Está en la carpeta de trabajo, en ningún commit y fuera del staging area. Git todavía no lo sigue." },
        taught: { chapter: "cargo", levels: 1 },
      },
      {
        id: "staged",
        name: { en: "staged", es: "en el staging area" },
        space: { en: "on the dock", es: "en el muelle" },
        what: { en: "Its current version is in the staging area, ready for the next commit.", es: "Su versión actual está en el staging area, lista para el próximo commit." },
        taught: { chapter: "cargo", levels: 1 },
      },
      {
        id: "committed",
        name: { en: "committed", es: "en un commit" },
        space: { en: "sealed in the vault", es: "sellado en la bóveda" },
        what: { en: "Saved in a commit, and the working copy matches it: nothing to do.", es: "Guardado en un commit, y la copia de trabajo coincide con él: no hay nada que hacer." },
        taught: { chapter: "vault" },
      },
      {
        id: "modified",
        name: { en: "modified", es: "modificado" },
        space: { en: "edited in the workshop", es: "editado en el taller" },
        what: { en: "Changed in the working folder since its last commit, and not staged.", es: "Cambió en la carpeta de trabajo desde su último commit y no está en el staging area." },
        taught: { chapter: "vault" },
      },
    ],
    moves: [
      { from: "untracked", to: "staged", how: "git add", taught: { chapter: "cargo", levels: 1 } },
      { from: "staged", to: "untracked", how: { en: "git rm --cached (before the file's first commit)", es: "git rm --cached (antes del primer commit del archivo)" }, taught: { chapter: "cargo" } },
      { from: "staged", to: "committed", how: "git commit", taught: { chapter: "vault" } },
      { from: "committed", to: "modified", how: { en: "edit the file", es: "editar el archivo" }, taught: { chapter: "vault" } },
      { from: "modified", to: "staged", how: "git add", taught: { chapter: "vault" } },
      { from: "staged", to: "modified", how: { en: "git restore --staged (a file the last commit holds)", es: "git restore --staged (un archivo que tiene el último commit)" }, taught: { chapter: "cargo" } },
      { from: "staged", to: "untracked", how: { en: "git restore --staged (a new file, once the repository has a commit)", es: "git restore --staged (un archivo nuevo, cuando el repositorio ya tiene un commit)" }, taught: { chapter: "cargo" } },
      { from: "modified", to: "committed", how: { en: "git restore (drops the edit)", es: "git restore (descarta la edición)" }, taught: { chapter: "undo" } },
    ],
  },
});
