"""Abort the docking in Spanish (`conflict_abort`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Aborta el acople"
CARD = "Detiene un merge en pausa y deja el branch y sus archivos como estaban antes de empezar. Haz commit o guarda en el stash tus propios cambios antes de un merge, así nunca tiene que reconstruirlos."
SCENE = [
    "Viernes, seis de la tarde. Alex hizo push de líneas en los mismos dos archivos que cambiaste.",
    "Haz pull antes de irte. Si Git se detiene, puedes responderle ahora, o volver a donde estabas y responder el lunes.",
]

BRIEFING = """
Es viernes a las seis. Hiciste commit de una línea en `README.md` y `notes.txt`, y Alex hizo push
de sus propias líneas en los dos. Tu nota para el lunes en `todo.txt` no tiene commit. Trae el
trabajo de Alex con `git pull --no-rebase` antes de irte.

Alex, por el comunicador: "Los dos archivos también cambiaron de mi lado, y solo yo sé por qué. Si
el pull se detiene, no adivines mis líneas esta noche. Cancela el merge, y lo respondemos juntos el
lunes."

La misión termina cuando tu pull haya empezado el merge, hayas mirado con `git status`, no haya un
merge en curso, `main` y los dos archivos estén como los dejó tu commit, y `todo.txt` todavía tenga
tu nota.
"""

HINTS = [
    "`git pull --no-rebase` trae los commits de Alex y empieza el merge. Después, `git status` dice que hay un merge en curso y lista los archivos en conflicto.",
    "`git merge --abort` sale del merge en pausa.",
    "Cada línea de la misión, en orden:\n\n    $ git pull --no-rebase\n    $ git status\n    $ git merge --abort",
]

DEBRIEF = """
Tu `git pull --no-rebase` empezó el merge y se detuvo a mitad de camino: los dos habían cambiado
las mismas líneas. `git status` mostró el merge en pausa, con los dos archivos sin resolver. `git merge --abort`
salió de él: `main` quedó donde lo dejó tu commit, los dos archivos volvieron a tener tus líneas, y
tu nota en `todo.txt` siguió ahí, porque el merge nunca tocó ese archivo.

`git merge --abort` es la puerta segura, y el merge puede esperar al lunes: el commit de Alex sigue
en el remoto (la nave nodriza), y `git pull` lo intentará de nuevo. Git puede reconstruir tus cambios sin commit
solo en algunos casos, así que haz commit o guárdalos en el stash antes de un merge.
`git reset --hard` también terminaría el merge, pero descarta todo cambio sin commit en archivos
con seguimiento, también tu nota.

Comandos para recordar:

    $ git pull --no-rebase  # trae los commits del remoto; un conflicto pone el merge en pausa
    $ git status            # ¿hay un merge en curso, y qué archivos están en conflicto?
    $ git merge --abort     # vuelve a donde estabas antes del merge
"""

STEPS = {
    "pull": kit.StepText(text="Trae el trabajo de Alex."),
    "status": kit.StepText(text="Averigua dónde se detuvo el pull."),
    "abort": kit.StepText(text="Vuelve a donde estabas antes del pull."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_PULLED = "Primero trae el trabajo de Alex: `git pull --no-rebase`."
HOW_TO_JOIN = "Git trajo los commits de Alex y se detuvo: los dos agregaron commits, así que pregunta cómo unirlos. `git pull --no-rebase` los une con un merge."
PAUSED = "El pull se detuvo a mitad de camino: Git encontró conflictos en `README.md` y `notes.txt`, y el merge te espera."
REBASE_REFUSED = "Git se negó: un pull con `--rebase` necesita todos los cambios en un commit, y tu nota en `todo.txt` no lo está. `git pull --no-rebase` hace un merge, y un merge no toca los archivos que no cambia."
LOOKED = "`git status` muestra el merge en curso y los dos archivos en conflicto."
NOT_LOOKED = "Primero mira: `git status`."
STILL_PAUSED = "El merge sigue en pausa. Sal de él: `git merge --abort`."
MERGED = "El merge terminó: ahora `main` tiene el commit de Alex. La misión era volver atrás: empiézala de nuevo."
NOT_BACK = "`main` o sus archivos no están como los dejó tu commit. `git merge --abort` los devuelve."
NOTE_LOST = "Tu nota en `todo.txt` se perdió: no estaba en ningún commit, y nada puede traerla de vuelta. Vuelve a empezar la misión."
BACK = "No hay un merge en curso: `main` y los dos archivos están como los dejó tu commit, y tu nota sigue ahí."
RESET = "`git reset --hard` descarta todo cambio sin commit en archivos con seguimiento, no solo el merge. `git merge --abort` era la puerta segura."
