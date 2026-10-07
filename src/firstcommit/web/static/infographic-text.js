"use strict";

/*
 * Every word of the infographics, in one place so it can be fact-checked and translated: the
 * commands the game teaches, grouped by what they do; Git's four places and the commands that
 * move work between them; a file's states and what moves a file from one to the next. Each
 * space word sits next to the real Git term. Every word is given as {en, es}; ids, unlocks,
 * the states' Git names and commands that are only a command are said once. Each item says
 * what unlocks it: a number of its chapter's levels finished ({chapter: id, levels: n}, in any
 * order) or the whole chapter ({chapter: id}); never a level's id, which the page does not
 * know. Data only. Defines one global, InfographicText.
 */

/* exported InfographicText */

const InfographicText = Object.freeze({
  title: { en: "Field guide", es: "Guía de campo" },
  lede: {
    en: "Everything the missions have taught you, in three pictures. What you have not learned yet stays locked.",
    es: "Todo lo que te enseñaron las misiones, en tres imágenes. Lo que aún no aprendiste sigue bloqueado.",
  },
  locked: { en: "Not learned yet", es: "Aún no lo aprendiste" },

  commands: {
    title: { en: "Every command, by what it does", es: "Todos los comandos, según lo que hacen" },
    groups: [
      {
        title: { en: "Look around", es: "Mirar a tu alrededor" },
        commands: [
          {
            command: "ls",
            what: { en: "Lists the files in the current folder; ls -a lists the hidden ones too.", es: "Muestra los archivos de la carpeta actual; ls -a muestra también los ocultos." },
            unlock: { chapter: "liftoff", levels: 1 },
          },
          {
            command: "git status",
            what: { en: "Says which files are untracked, modified or staged, and which branch you are on.", es: "Dice qué archivos están untracked, modified o staged, y en qué branch estás." },
            unlock: { chapter: "liftoff", levels: 1 },
          },
          {
            command: "git diff",
            what: { en: "Shows the lines you changed and have not staged; git diff --staged shows what is staged.", es: "Muestra las líneas que cambiaste y aún no pasaste al staging area; git diff --staged muestra lo que ya está en el staging area." },
            unlock: { chapter: "vault" },
          },
          {
            command: "git log",
            what: { en: "Lists the commits, newest first, with their hash, author and message.", es: "Lista los commits, del más reciente al más antiguo, con su hash, su autor y su mensaje." },
            unlock: { chapter: "vault" },
          },
        ],
      },
      {
        title: { en: "Start a repository", es: "Crear un repositorio" },
        commands: [
          {
            command: "git init",
            what: { en: "Makes the current folder a repository: Git creates the hidden .git folder.", es: "Convierte la carpeta actual en un repositorio: Git crea la carpeta oculta .git." },
            unlock: { chapter: "liftoff", levels: 2 },
          },
          {
            command: "git clone <url>",
            what: { en: "Copies a remote repository, its whole history included, into a new folder.", es: "Copia un repositorio remoto, con todo su historial, en una carpeta nueva." },
            unlock: { chapter: "branch" },
          },
        ],
      },
      {
        title: { en: "Stage and commit", es: "Staging y commit" },
        commands: [
          {
            command: "git add <file>",
            what: { en: "Copies a file, as it is now, from the working folder into the staging area.", es: "Copia un archivo, tal como está ahora, del directorio de trabajo al staging area." },
            unlock: { chapter: "cargo", levels: 1 },
          },
          {
            command: "git rm --cached <file>",
            what: { en: "Takes a file out of the staging area and leaves it in the working folder.", es: "Saca un archivo del staging area y lo deja en el directorio de trabajo." },
            unlock: { chapter: "cargo" },
          },
          {
            command: "git restore --staged <file>",
            what: { en: "Unstages a file: the staging area gets back the version of the last commit.", es: "Saca un archivo del staging area: el staging area recupera la versión del último commit." },
            unlock: { chapter: "cargo" },
          },
          {
            command: "git commit -m \"<message>\"",
            what: { en: "Saves the staging area as a new commit in your local repository.", es: "Guarda el staging area como un commit nuevo en tu repositorio local." },
            unlock: { chapter: "vault" },
          },
        ],
      },
      {
        title: { en: "Share with the remote", es: "Compartir con el remoto" },
        commands: [
          {
            command: "git remote add origin <url>",
            what: { en: "Gives a remote repository's address a short name, usually origin. Nothing is sent.", es: "Da un nombre corto, normalmente origin, a la dirección de un repositorio remoto. No se envía nada." },
            unlock: { chapter: "mothership" },
          },
          {
            command: "git push",
            what: { en: "Sends your branch's new commits to the remote repository.", es: "Envía los commits nuevos de tu branch al repositorio remoto." },
            unlock: { chapter: "mothership" },
          },
          {
            command: "git fetch",
            what: { en: "Downloads the remote's new commits and updates origin/main; your branch and files stay as they are.", es: "Descarga los commits nuevos del remoto y actualiza origin/main; tu branch y tus archivos se quedan como están." },
            unlock: { chapter: "mothership" },
          },
          {
            command: "git pull",
            what: { en: "A fetch, then a merge of the remote's branch into yours: your files update too.", es: "Un fetch y después un merge del branch del remoto en el tuyo: tus archivos también se actualizan." },
            unlock: { chapter: "mothership" },
          },
        ],
      },
      {
        title: { en: "Branches and merges", es: "Branches y merges" },
        commands: [
          {
            command: "git switch -c <branch>",
            what: { en: "Creates a branch, a movable label on a commit, and switches to it.", es: "Crea un branch, una etiqueta que se mueve de commit en commit, y te cambia a él." },
            unlock: { chapter: "branch" },
          },
          {
            command: "git switch <branch>",
            what: { en: "Moves HEAD to another branch; the working folder takes that branch's files.", es: "Mueve HEAD a otro branch; el directorio de trabajo pasa a tener los archivos de ese branch." },
            unlock: { chapter: "branch" },
          },
          {
            command: "git merge <branch>",
            what: { en: "Joins another branch's history into yours, with a merge commit when both moved on.", es: "Une el historial de otro branch al tuyo, con un commit de merge si los dos avanzaron." },
            unlock: { chapter: "conflict" },
          },
          {
            command: "git merge --abort",
            what: { en: "Stops a merge in progress and puts everything back as it was before it.", es: "Detiene un merge a medias y deja todo como estaba antes de empezarlo." },
            unlock: { chapter: "conflict" },
          },
        ],
      },
      {
        title: { en: "Undo", es: "Deshacer" },
        commands: [
          {
            command: "git restore <file>",
            what: { en: "Replaces the working copy with the staged or committed version. Unsaved lines are gone for good.", es: "Reemplaza la copia de trabajo por la versión del staging area o la del último commit. Las líneas sin guardar se pierden para siempre." },
            unlock: { chapter: "undo" },
          },
          {
            command: "git revert <commit>",
            what: { en: "Adds a new commit that undoes an earlier one, safe for history others already have.", es: "Agrega un commit nuevo que deshace uno anterior; es seguro con un historial que otros ya tienen." },
            unlock: { chapter: "undo" },
          },
          {
            command: "git reset <commit>",
            what: { en: "Moves the current branch's label back to an earlier commit.", es: "Mueve la etiqueta del branch actual hacia atrás, a un commit anterior." },
            unlock: { chapter: "undo" },
          },
          {
            command: "git reflog",
            what: { en: "Lists where HEAD has been, so a commit no branch points to can be found again.", es: "Lista por dónde pasó HEAD, para volver a encontrar un commit al que ya no apunta ningún branch." },
            unlock: { chapter: "undo" },
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
        git: { en: "working folder", es: "directorio de trabajo" },
        what: { en: "Your files as you edit them. Git watches but does not save them.", es: "Tus archivos mientras los editas. Git los vigila, pero no los guarda." },
        unlock: { chapter: "liftoff", levels: 1 },
      },
      {
        id: "dock",
        space: { en: "Cargo dock", es: "Muelle de carga" },
        git: { en: "staging area", es: "staging area" },
        what: { en: "The files you chose for your next commit, as they were when you added them.", es: "Los archivos que elegiste para tu próximo commit, tal como estaban cuando los agregaste." },
        unlock: { chapter: "cargo", levels: 1 },
      },
      {
        id: "vault",
        space: { en: "Vault", es: "Bóveda" },
        git: { en: "local repository", es: "repositorio local" },
        what: { en: "Every commit you made, on this computer only, in the hidden .git folder.", es: "Todos los commits que hiciste, solo en esta computadora, dentro de la carpeta oculta .git." },
        unlock: { chapter: "liftoff", levels: 2 },
      },
      {
        id: "mothership",
        space: { en: "Mothership", es: "Nave nodriza" },
        git: { en: "remote repository", es: "repositorio remoto" },
        what: { en: "A copy of the repository on a server, such as GitHub, shared with your team.", es: "Una copia del repositorio en un servidor, como GitHub, que compartes con tu equipo." },
        unlock: { chapter: "mothership" },
      },
    ],
    moves: [
      { from: "workshop", to: "dock", command: "git add", unlock: { chapter: "cargo", levels: 1 } },
      { from: "dock", to: "workshop", command: "git restore --staged", unlock: { chapter: "cargo" } },
      { from: "dock", to: "vault", command: "git commit", unlock: { chapter: "vault" } },
      { from: "vault", to: "workshop", command: "git switch, git restore", unlock: { chapter: "branch" } },
      { from: "vault", to: "mothership", command: "git push", unlock: { chapter: "mothership" } },
      { from: "mothership", to: "vault", command: "git fetch", unlock: { chapter: "mothership" } },
      { from: "mothership", to: "workshop", command: { en: "git pull (fetch, then merge)", es: "git pull (fetch y luego merge)" }, unlock: { chapter: "mothership" } },
    ],
  },

  states: {
    title: { en: "A file's states", es: "Los estados de un archivo" },
    states: [
      {
        id: "untracked",
        name: "untracked",
        space: { en: "new in the workshop", es: "nuevo en el taller" },
        what: { en: "In the working folder, in no commit and not staged. Git does not follow it yet.", es: "Está en el directorio de trabajo, en ningún commit y fuera del staging area. Git todavía no lo sigue." },
        unlock: { chapter: "cargo", levels: 1 },
      },
      {
        id: "staged",
        name: "staged",
        space: { en: "on the dock", es: "en el muelle" },
        what: { en: "Its current version is in the staging area, ready for the next commit.", es: "Su versión actual está en el staging area, lista para el próximo commit." },
        unlock: { chapter: "cargo", levels: 1 },
      },
      {
        id: "committed",
        name: "committed",
        space: { en: "sealed in the vault", es: "sellado en la bóveda" },
        what: { en: "Saved in a commit, and the working copy matches it: nothing to do.", es: "Guardado en un commit, y la copia de trabajo coincide con él: no hay nada que hacer." },
        unlock: { chapter: "vault" },
      },
      {
        id: "modified",
        name: "modified",
        space: { en: "edited in the workshop", es: "editado en el taller" },
        what: { en: "Changed in the working folder since its last commit, and not staged.", es: "Cambió en el directorio de trabajo desde su último commit y no está en el staging area." },
        unlock: { chapter: "vault" },
      },
    ],
    moves: [
      { from: "untracked", to: "staged", how: "git add", unlock: { chapter: "cargo", levels: 1 } },
      { from: "staged", to: "untracked", how: { en: "git rm --cached (before the file's first commit)", es: "git rm --cached (antes del primer commit del archivo)" }, unlock: { chapter: "cargo" } },
      { from: "staged", to: "committed", how: "git commit", unlock: { chapter: "vault" } },
      { from: "committed", to: "modified", how: { en: "edit the file", es: "editar el archivo" }, unlock: { chapter: "vault" } },
      { from: "modified", to: "staged", how: "git add", unlock: { chapter: "vault" } },
      { from: "staged", to: "modified", how: "git restore --staged", unlock: { chapter: "cargo" } },
      { from: "modified", to: "committed", how: { en: "git restore (drops the edit)", es: "git restore (descarta la edición)" }, unlock: { chapter: "undo" } },
    ],
  },
});
