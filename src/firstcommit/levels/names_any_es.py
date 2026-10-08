"""A name on any commit in Spanish (`names_any`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Un nombre en cualquier commit"
CARD = "Pone un nombre nuevo en cualquier commit, dado por su hash. Te quedas donde estás y tu carpeta no cambia."
SCENE = [
    "Después de tu pull, `main` subió al arreglo de Alex, y tu marcador y el pin del remoto (la nave nodriza) también están ahí. `test-run` sigue en Start the project.",
]

BRIEFING = """
Antes de esta misión hiciste `git pull`, el paso con el que terminó la misión anterior, así que
`main` está en el arreglo de Alex, Fix the route. `test-run`, un nombre viejo en Start the project,
ya puede irse. Después, el capitán quiere encontrar fácil el commit donde se trazó la ruta por
primera vez, con un nombre `first-route`.

La misión termina cuando `test-run` ya no esté, `first-route` nombre Plot the route y hayas
revisado la historia después de cada cambio.
"""

HINTS = [
    "`git branch -d <name>` quita un nombre. Cada línea de `git log --oneline` empieza con el hash del commit.",
    "`git branch <name> <hash>` pone un nombre en ese commit.",
    "Cada línea de la misión, en orden:\n\n    $ git log --oneline\n    $ git branch -d test-run\n    $ git log --oneline\n    $ git branch first-route {{route}}\n    $ git log --oneline",
]

DEBRIEF = """
`git branch -d test-run` quitó un nombre y el commit se quedó: los nombres apuntan a commits, no
son los commits. `git branch first-route <hash>` puso un nombre en un commit viejo sin moverte.

Cada commit recuerda el anterior, su padre, así que un nombre lleva hacia abajo a cada commit más
viejo: así `git log` empieza en `main` y baja hasta el primer commit.

Comandos para recordar:

    $ git branch -d test-run          # quita un nombre; el commit se queda
    $ git branch first-route <hash>   # un nombre en cualquier commit
"""

STEPS = {
    "log": kit.StepText(text="Lee la historia."),
    "guess-delete": kit.StepText(
        text="Primero, predice.",
        question="Quitas el nombre `test-run` con `git branch -d test-run`. ¿Qué le pasa al commit Start the project?",
        options=("También se borra", "Se queda"),
        reveal="Se queda. Un nombre apunta a un commit; no es el commit. Y `main` sigue llevando hasta él por las líneas.",
    ),
    "delete": kit.StepText(text="Quita el nombre viejo."),
    "log-again": kit.StepText(text="Revisa la historia."),
    "guess-name": kit.StepText(
        text="Primero, predice.",
        question="Pones un nombre nuevo `first-route` en Plot the route, por su hash. ¿Qué le pasa a tu carpeta?",
        options=("Muestra los archivos de ese commit", "No cambia nada"),
        reveal="No cambia nada. `git branch` solo escribe un nombre. `HEAD` se queda en `main`, así que tus archivos quedan como están.",
    ),
    "name": kit.StepText(text="Nombra el commit donde se trazó la ruta por primera vez."),
    "log-third": kit.StepText(text="Revisa la historia."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOGGED = (
    "Cada línea empieza con el hash del commit: la forma de nombrarle un commit a Git. Cada commit recuerda el anterior, "
    "su padre: `git log` empieza en el commit de `main` y sigue esas líneas hasta el primer commit, Start the project, con `test-run` encima."
)
NOT_LOGGED = "Lee la historia: `git log --oneline`."
NOT_DELETED = "`test-run` sigue ahí. Quita el nombre: `git branch -d test-run`."
DELETED = 'Git dice a qué commit apuntaba el nombre: mira "was" y el hash que sigue. El commit sigue ahí.'
LOGGED_AGAIN = "Siguen siendo cinco commits. Solo se fue un nombre. Ahora busca Plot the route, una línea más arriba: su hash es el que necesitas ahora."
NOT_LOGGED_AGAIN = "Revisa la historia: `git log --oneline`."
NOT_NAMED = "Todavía no hay `first-route`. Ponlo en Plot the route: `git branch first-route` y el hash de ese commit, que muestra `git log --oneline`."
ELSEWHERE = "`first-route` está en otro commit. Quítalo con `git branch -d first-route` y ponlo en Plot the route, con el hash que `git log --oneline` muestra para él."
NAMED = "Un nombre en un commit viejo, y nada más se movió. Sin hash, `git branch` pone el nombre donde estás."
LOGGED_THIRD = "`git log` muestra el nombre nuevo entre paréntesis en su commit."
NOT_LOGGED_THIRD = "Revisa la historia: `git log --oneline`."
MOVED_ONTO = "Llevaste `HEAD` a `first-route`, y tu carpeta ahora muestra los archivos de ese commit. `git switch main` te trae de vuelta."
