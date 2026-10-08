"""Base 7 in Spanish (`mothership_base7`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Base 7"
CARD = "Dice qué está en el staging area, qué cambió en la carpeta de trabajo y cómo está tu branch frente a su upstream. Pregúntale antes de cada commit y cada push."
SCENE = [
    "Impacto de meteorito en la Base 7. Su computadora desapareció, y su historia con ella.",
    "Los archivos sobrevivieron en un disco de respaldo, con restos del choque. Reconstruye la base y llévala a la nave nodriza.",
]

BRIEFING = """
Un meteorito destruyó la computadora de la Base 7. Sus archivos sobrevivieron en esta carpeta, y
también `crash-dump.bin`, restos del choque. La nave nodriza espera, vacía, en
`../github/project.git`.

La misión termina cuando la carpeta sea un repositorio, una cápsula contenga `blueprint.txt` y
`reactor.cfg` y ninguna cápsula contenga los restos, `origin` apunte a la nave nodriza y el `main`
de la nave nodriza sea el mismo que el tuyo.
"""

HINTS = [
    "Son todos los capítulos hasta ahora, en orden: el despegue, el muelle de carga, la bóveda y la nave nodriza.",
    "Primero un repositorio; luego elige la carga por su nombre, séllala, nombra la nave nodriza y lanza.",
    'Cada línea de la misión, en orden:\n\n    $ git init\n    $ git add blueprint.txt reactor.cfg\n    $ git commit -m "Rebuild Base 7"\n    $ git remote add origin ../github/project.git\n    $ git push -u origin main',
]

DEBRIEF = """
La Base 7 vuelve a ser un repositorio, con su plano y los ajustes del reactor sellados en una
cápsula, y la nave nodriza tiene la misma historia. Los restos nunca salieron de la carpeta de
trabajo.

Ese es el ciclo completo que usarás en el trabajo: `git init` (o un clone), `git add` por nombre,
`git commit`, `git remote add`, `git push -u`. Los próximos capítulos agregan branches, merges y
formas de deshacer.
"""

STEPS = {
    "repository": kit.StepText(text="La carpeta de la Base 7 es un repositorio."),
    "capsule": kit.StepText(text="Una cápsula contiene `blueprint.txt` y `reactor.cfg`; ninguna cápsula contiene los restos."),
    "contact": kit.StepText(text="`origin` apunta a la nave nodriza."),
    "launch": kit.StepText(text="El `main` de la nave nodriza es el mismo que el tuyo."),
}

NO_REPOSITORY = "La carpeta de la Base 7 todavía no es un repositorio."
REPOSITORY = "La carpeta de la Base 7 es un repositorio."
SEALED = "Una cápsula contiene el plano y los ajustes del reactor, y ninguna cápsula contiene los restos."
NOT_SEALED = "Todavía ninguna cápsula contiene a la vez `blueprint.txt` y `reactor.cfg`."
DEBRIS_SEALED = "`crash-dump.bin` está sellado en una cápsula. Deshacer un commit llega en un capítulo posterior: vuelve a empezar la misión."
CONTACT = "`origin` apunta a la nave nodriza."
NO_CONTACT = "Tu repositorio todavía no conoce la nave nodriza como `origin` en `../github/project.git`."
LAUNCHED = "El `main` de la nave nodriza es el mismo que el tuyo."
NOT_LAUNCHED = "El `main` de la nave nodriza todavía no es el mismo que el tuyo."
DEBRIS_LAUNCHED = "Los restos están en la nave nodriza, en una cápsula de su `main`. Vuelve a empezar la misión."
