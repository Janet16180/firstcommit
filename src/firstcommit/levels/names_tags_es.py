"""Name tags in Spanish (`names_tags`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Etiquetas"
CARD = "Lista tus branches, cada uno con el commit que nombra. `*` marca el branch donde está `HEAD`."
SCENE = [
    "Sector nuevo: Etiquetas. Desde que conociste la nave nodriza escribiste `main` y `origin/main` en `git push` y `git status`. Este sector dice qué son: nombres. Los commits son el trabajo; los nombres son cómo lo encuentras.",
    "Esta es la cadena: tus commits, el más nuevo arriba, cada uno unido por una línea al anterior. Los commits son el trabajo. Esta misión trata de los nombres que llevan.",
]

BRIEFING = """
Anotaste el nivel de combustible en `notes.txt`. Haz commit de la nota y envíala a la nave
nodriza; después busca noticias de la tripulación. Fíjate qué nombres se mueven.

La misión termina cuando tu nota esté en la nave nodriza, tu marcador de la nave nodriza se haya
puesto al día con las noticias de la tripulación y le hayas preguntado a `git status` cómo está
`main`.
"""

HINTS = [
    "`git log --oneline` muestra cada commit en una línea; los nombres entre paréntesis son los nombres de ese commit.",
    "`git commit -am` hace commit de cada archivo con seguimiento que cambiaste; `git push` envía `main`; `git fetch` le pide noticias a la nave nodriza.",
    'Cada línea de la misión, en orden:\n\n    $ git log --oneline\n    $ git branch -v\n    $ git commit -am "Note the fuel level"\n    $ git log --oneline\n    $ git push\n    $ git fetch\n    $ git status',
]

DEBRIEF = """
Un branch es un nombre para un commit. `HEAD` es "estás aquí", y va sobre el branch donde estás.
Cuando haces commit, ese branch sube al commit nuevo y `HEAD` va con él; ningún otro nombre se
mueve.

`origin/main` es tu marcador del `main` de la nave nodriza. La nave nodriza puede avanzar sin ti,
como cuando Alex hizo push; tu marcador se pone al día solo cuando hablas con la nave nodriza:
`git push`, `git fetch` o `git pull`.

Comandos para recordar:

    $ git log --oneline   # los nombres entre paréntesis están en ese commit
    $ git branch -v       # cada branch y el commit que nombra; * es donde va HEAD
    $ git fetch           # pone al día tu marcador de la nave nodriza
"""

STEPS = {
    "log": kit.StepText(text="Lee la historia."),
    "branches": kit.StepText(text="Lista tus branches."),
    "guess-commit": kit.StepText(
        text="Primero, predice.",
        question="Ahora haces commit de tu nota de combustible. ¿Qué nombres suben al commit nuevo?",
        options=("Solo `main`", "`main` y `origin/main`", "`main` y `test-run`"),
        reveal="Solo `main`, con `HEAD` encima. Un commit mueve el branch donde va `HEAD`. `test-run` nombra su propio commit, y el marcador se mueve solo cuando hablas con la nave nodriza.",
    ),
    "commit": kit.StepText(text="Haz commit de tu nota."),
    "log-again": kit.StepText(text="Lee la historia otra vez."),
    "push": kit.StepText(text="Envíala."),
    "guess-fetch": kit.StepText(
        text="Primero, predice.",
        question="Escribes `git fetch`, que le pide noticias a la nave nodriza. Después, ¿está el arreglo de Alex en tu carpeta?",
        options=("Sí", "No"),
        reveal="No. Un fetch trae el commit de Alex a tu repositorio y mueve tu marcador hasta él. `main` se queda donde estaba, así que tu carpeta, que muestra el commit de `main`, no cambia.",
    ),
    "fetch": kit.StepText(text="Pídele noticias a la nave nodriza."),
    "status": kit.StepText(text="Pregunta cómo está `main`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOGGED = (
    "Los nombres entre paréntesis están en ese commit. `main` es un branch: un nombre para un commit. `test-run` es otro "
    'branch, un nombre para un commit más viejo. `HEAD -> main` significa que `HEAD` está en `main`: `HEAD` es "estás aquí", el commit que muestra tu carpeta.'
)
NOT_LOGGED = "Lee la historia: `git log --oneline`."
LISTED = (
    "Eso es todo lo que es un branch: un nombre y el hash de un commit. Dos nombres, dos commits. El `*` marca el branch "
    "donde está `HEAD`. `origin/main` es tu marcador: donde estaba el `main` de la nave nodriza la última vez que hablaste con ella."
)
NOT_LISTED = "Lista tus branches: `git branch -v`."
NOT_COMMITTED = 'Haz commit de tu nota: `git commit -am "Note the fuel level"`.'
COMMITTED = "`main` subió al commit nuevo, y `HEAD` fue con él. `test-run` se quedó, y tu marcador también: la nave nodriza no sabe nada de este commit."
LOGGED_AGAIN = "`git log` dice lo mismo con palabras: `HEAD -> main` en el commit nuevo, `origin/main` uno más abajo."
NOT_LOGGED_AGAIN = "Lee la historia otra vez: `git log --oneline`."
NOT_PUSHED = "Envía tu nota: `git push`."
PUSHED = (
    "El push envió tu commit, y Git movió tu marcador en el mismo momento. Noticias: Alex acaba de hacer push de un arreglo, "
    "así que el `main` de la nave nodriza está en el commit de Alex. Tu marcador no se movió: no hablaste con la nave nodriza desde entonces."
)
NOT_FETCHED = "Pídele noticias a la nave nodriza: `git fetch`."
FETCHED = "Tu marcador se puso al día con la nave nodriza, y el commit de Alex está en tu repositorio. `main` y `HEAD` se quedaron en tu commit, así que tu carpeta no cambió."
STATUS_READ = '`git status` compara `main` con tu marcador: un commit atrás. "Fast-forwarded" significa que `main` puede simplemente subir hasta él; `git pull` lo haría.'
STATUS_PULLED = "`git status` compara `main` con tu marcador: tu pull ya subió `main` hasta él, así que coinciden."
NOT_STATUS = "Pregunta cómo está `main`: `git status`."
LISTS_NAMES = "Cada línea es un nombre y el commit al que apunta. `*` marca el branch donde va `HEAD`."
