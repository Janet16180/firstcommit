"""Incoming transmission in Spanish (`mothership_incoming`)."""

from firstcommit import kit

TITLE = "Transmisión entrante"
CARD = "Pregunta al remoto qué tiene ahora y actualiza `origin/main`, la copia que guarda tu repositorio de sus noticias. Tu `main` y tus archivos se quedan como están."
SCENE = [
    "Alex, del turno de noche, acaba de enviar un informe a la nave nodriza.",
    "Tu repositorio no vigila la nave nodriza. Solo sabe lo que oyó la última vez que preguntó.",
]

BRIEFING = """
Alex acaba de hacer push de un informe a la nave nodriza. Averigua qué sabe tu repositorio de
eso, pide noticias a la nave nodriza y trae el informe a tu `main`.

La misión termina cuando hayas mirado con `git status` antes y después de `git fetch`, y el
commit de Alex esté en tu `main`.
"""

HINTS = [
    "`git status` compara tu `main` con `origin/main`, que solo cambia cuando haces fetch.",
    "`git fetch` trae las noticias; `git pull` trae el commit de Alex a tu `main`.",
]

DEBRIEF = """
`git status` dijo que estabas al día porque compara tu `main` con `origin/main`: la copia que
guarda tu repositorio del `main` de la nave nodriza, de la última vez que preguntó. `git fetch`
preguntó, y `origin/main` pasó al commit de Alex, así que `git status` dijo que ibas un commit por
detrás. `git pull` volvió a hacer fetch y trajo ese commit a tu `main`, y la línea de Alex a
`notes.txt`.

Comandos para recordar:

    $ git fetch     # pide noticias al remoto; tu main y tus archivos no cambian
    $ git pull      # hace fetch y trae las noticias a tu rama
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, haz tu predicción.",
        question="Alex hizo push hace un minuto. ¿Qué dirá `git status` de tu `main`?",
        options=("Al día con `origin/main`", "Un commit por detrás de `origin/main`"),
        reveal=(
            "Al día: `git status` compara tu `main` con `origin/main`, las últimas noticias que tiene tu repositorio de la nave nodriza, "
            "y no ha preguntado desde que Alex hizo push."
        ),
    ),
    "status": kit.StepText(text="Pregunta a tu repositorio cómo está `main`."),
    "fetch": kit.StepText(text="Pide noticias a la nave nodriza."),
    "again": kit.StepText(text="Vuelve a preguntar a `git status`."),
    "pull": kit.StepText(text="Trae el commit de Alex a tu `main`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` ha desaparecido. Sal del nivel y vuelve a empezarlo para recuperarlo."
WAITING = "La nave nodriza todavía no tiene noticias. Espera un momento al informe de Alex."
LOOKED = "`git status` dice que estás al día: compara con `origin/main`, que no sabe nada del push de Alex."
NOT_LOOKED = "Pregunta a tu repositorio qué sabe: escribe `git status`."
FETCHED = "`origin/main` ya tiene el commit de Alex: tu repositorio tiene las noticias."
NOT_FETCHED = "Tu repositorio no sabe nada del commit de Alex. Pregunta a la nave nodriza: `git fetch`."
BEHIND = "`git status` compara con el nuevo `origin/main`."
NOT_AGAIN = "Ahora vuelve a preguntar a `git status`: `origin/main` se ha movido."
PULLED = "El commit de Alex está en tu `main`, y su línea en `notes.txt`."
NOT_PULLED = "El commit de Alex todavía no está en tu `main`: `git pull` lo trae."
