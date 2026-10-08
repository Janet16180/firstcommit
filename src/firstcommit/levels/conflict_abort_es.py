"""Abort the docking in Spanish (`conflict_abort`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Aborta el acople"
CARD = "Detiene un merge en pausa y deja el branch y sus archivos como estaban antes de empezar. Haz commit o guarda en el stash tus propios cambios antes de un merge, así nunca tiene que reconstruirlos."
SCENE = [
    "Viernes, seis de la tarde. Tu pull se detuvo a mitad de camino: Git encontró conflictos en dos archivos.",
    "Puedes responderle a Git ahora, o volver a donde estabas y responder el lunes.",
]

BRIEFING = """
Es viernes a las seis. Hiciste commit de una línea en `README.md` y `notes.txt`, Alex hizo push de
sus propias líneas en los dos, y tu `git pull` se detuvo a mitad de camino, con conflictos. Tu nota
para el lunes en `todo.txt` no tiene commit. Vuelve a donde estabas antes del pull y conserva la
nota.

Alex, por el comunicador: "Los dos archivos también cambiaron de mi lado, y solo yo sé por qué. No
adivines mis líneas esta noche. Cancela el merge, y lo respondemos juntos el lunes."

La misión termina cuando hayas mirado con `git status`, no haya un merge en curso, `main` y los
dos archivos estén como los dejó tu commit, y `todo.txt` todavía tenga tu nota.
"""

HINTS = [
    "`git status` dice que hay un merge en curso y lista los archivos en conflicto.",
    "`git merge --abort` sale del merge en pausa.",
    "Cada línea de la misión, en orden:\n\n    $ git status\n    $ git merge --abort",
]

DEBRIEF = """
`git status` mostró el merge en pausa, con los dos archivos sin resolver. `git merge --abort`
salió de él: `main` quedó donde lo dejó tu commit, los dos archivos volvieron a tener tus líneas, y
tu nota en `todo.txt` siguió ahí, porque el merge nunca tocó ese archivo.

`git merge --abort` es la puerta segura, y el merge puede esperar al lunes: el commit de Alex sigue
en el remoto (la nave nodriza), y `git pull` lo intentará de nuevo. Git puede reconstruir tus cambios sin commit
solo en algunos casos, así que haz commit o guárdalos en el stash antes de un merge.
`git reset --hard` también terminaría el merge, pero descarta todo cambio sin commit en archivos
con seguimiento, también tu nota.

Comandos para recordar:

    $ git status            # ¿hay un merge en curso, y qué archivos están en conflicto?
    $ git merge --abort     # vuelve a donde estabas antes del merge
"""

STEPS = {
    "status": kit.StepText(text="Averigua dónde se detuvo el pull."),
    "abort": kit.StepText(text="Vuelve a donde estabas antes del pull."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
WAITING = "El pull está en camino. Espera un momento."
LOOKED = "`git status` muestra el merge en curso y los dos archivos en conflicto."
NOT_LOOKED = "Primero mira: `git status`."
STILL_PAUSED = "El merge sigue en pausa. Sal de él: `git merge --abort`."
MERGED = "El merge terminó: ahora `main` tiene el commit de Alex. La misión era volver atrás: empiézala de nuevo."
NOT_BACK = "`main` o sus archivos no están como los dejó tu commit. `git merge --abort` los devuelve."
NOTE_LOST = "Tu nota en `todo.txt` se perdió: no estaba en ningún commit, y nada puede traerla de vuelta. Vuelve a empezar la misión."
BACK = "No hay un merge en curso: `main` y los dos archivos están como los dejó tu commit, y tu nota sigue ahí."
RESET = "`git reset --hard` descarta todo cambio sin commit en archivos con seguimiento, no solo el merge. `git merge --abort` era la puerta segura."
