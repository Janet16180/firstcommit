"use strict";

/*
 * Every word of the infographics, in one place so it can be fact-checked and translated: the
 * commands the game teaches, grouped by what they do; Git's four places and the commands that
 * move work between them; a file's states and what moves a file from one to the next. Each
 * space word sits next to the real Git term. Every word is given as {en, es}; ids, lessons and
 * commands that are only a command are said once. Each item says where the game teaches it
 * (`taught`): a number of its chapter's levels finished ({chapter: id, levels: n}, in any order)
 * or the whole chapter ({chapter: id}); never a level's id, which the page does not know. The
 * guide shows every item from the start, and tags one not taught yet with its sector. Data
 * only. Defines one global, InfographicText.
 */

/* exported InfographicText */

const InfographicText = Object.freeze({
  title: { en: "Field guide", es: "Guía de campo" },
  lede: {
    en: "Everything the missions teach, in three pictures. What a sector still ahead teaches is tagged with it.",
    es: "Todo lo que enseñan las misiones, en tres imágenes. Lo que enseña un sector que aún tienes por delante lleva su marca.",
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
            taught: { chapter: "branch" },
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
            command: "git restore --staged <file>",
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
            what: { en: "Sends your branch's new commits to the remote repository.", es: "Envía los commits nuevos de tu branch al repositorio remoto." },
            taught: { chapter: "mothership" },
          },
          {
            command: "git fetch",
            what: { en: "Downloads the remote's new commits and updates origin/main; your branch and files stay as they are.", es: "Descarga los commits nuevos del remoto y actualiza origin/main; tu branch y tus archivos se quedan como están." },
            taught: { chapter: "mothership" },
          },
          {
            command: "git pull",
            what: {
              en: "A fetch, then brings the remote's commits into your branch: a fast-forward when only the remote moved on; when both did, you choose a merge (--no-rebase) or a rebase (--rebase).",
              es: "Hace fetch y luego trae los commits del remoto a tu branch: un fast-forward si solo avanzó el remoto; si avanzaron los dos, eliges un merge (--no-rebase) o un rebase (--rebase).",
            },
            taught: { chapter: "mothership" },
          },
        ],
      },
      {
        title: { en: "Branches and merges", es: "Branches y merges" },
        commands: [
          {
            command: "git switch -c <branch>",
            what: { en: "Creates a branch, a movable label on a commit, and switches to it.", es: "Crea un branch, una etiqueta que se mueve de commit en commit, y te cambia a él." },
            taught: { chapter: "branch" },
          },
          {
            command: "git switch <branch>",
            what: { en: "Moves HEAD to another branch; the working folder takes that branch's files.", es: "Mueve HEAD a otro branch; la carpeta de trabajo pasa a tener los archivos de ese branch." },
            taught: { chapter: "branch" },
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
        ],
      },
      {
        title: { en: "Undo", es: "Deshacer" },
        commands: [
          {
            command: "git restore <file>",
            what: { en: "Replaces the working copy with the staged or committed version. Unsaved lines are gone for good.", es: "Reemplaza la copia de trabajo por la versión del staging area o la del último commit. Las líneas sin guardar se pierden para siempre." },
            taught: { chapter: "undo" },
          },
          {
            command: "git revert <commit>",
            what: { en: "Adds a new commit that undoes an earlier one, safe for history others already have.", es: "Agrega un commit nuevo que deshace uno anterior; es seguro con una historia que otros ya tienen." },
            taught: { chapter: "undo" },
          },
          {
            command: "git reset <commit>",
            what: { en: "Moves the current branch's label to another commit, and the staging area with it; the working folder keeps its files.", es: "Mueve la etiqueta del branch actual a otro commit, y el staging area con ella; la carpeta de trabajo conserva sus archivos." },
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
        space: { en: "Workshop", es: "Taller" },
        git: { en: "working folder", es: "carpeta de trabajo" },
        what: { en: "Your files as you edit them. Git saves nothing here until you add and commit.", es: "Tus archivos mientras los editas. Git no guarda nada aquí hasta que los agregas al staging area y haces un commit." },
        taught: { chapter: "liftoff", levels: 1 },
      },
      {
        id: "dock",
        space: { en: "Cargo dock", es: "Muelle de carga" },
        git: { en: "staging area", es: "staging area" },
        what: { en: "The files you chose for your next commit, as they were when you added them.", es: "Los archivos que elegiste para tu próximo commit, tal como estaban cuando los agregaste." },
        taught: { chapter: "cargo", levels: 1 },
      },
      {
        id: "vault",
        space: { en: "Vault", es: "Bóveda" },
        git: { en: "local repository", es: "repositorio local" },
        what: { en: "Every commit of your repository, yours and the ones you fetched, on this computer, in the hidden .git folder.", es: "Todos los commits de tu repositorio, los tuyos y los que trajiste con fetch, en esta computadora, dentro de la carpeta oculta .git." },
        taught: { chapter: "liftoff", levels: 2 },
      },
      {
        id: "mothership",
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
      { from: "vault", to: "workshop", command: "git switch, git restore", taught: { chapter: "branch" } },
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
