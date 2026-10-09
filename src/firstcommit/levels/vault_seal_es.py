"""Seal the capsule in Spanish (`vault_seal`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Sella la cápsula"
CARD = "Sella lo que está en el staging area en un commit nuevo de tu repositorio, con tu mensaje. Se queda en esta computadora hasta que hagas push."
SCENE = [
    "Un commit sella el staging area en una cápsula: una instantánea de sus archivos, con tu mensaje.",
    "Cada cápsula nueva se engancha a la anterior. Esa cadena es la historia de tu proyecto, guardada en tu repositorio (la bóveda).",
]

BRIEFING = """
El mapa está en el staging area, y el diario todavía no está listo. Sella el mapa en tu primera
cápsula, con un mensaje que diga qué contiene.

La misión termina cuando un commit contenga `map.txt`, `journal.txt` siga solo en la carpeta de
trabajo y hayas mirado la historia con `git log`.
"""

HINTS = [
    "`git commit` recibe un mensaje con `-m`, entre comillas.",
    'Escribe `git commit -m "Add the map"` y luego `git log`.',
    'Cada línea de la misión, en orden:\n\n    $ git commit -m "Add the map"\n    $ git log',
]

DEBRIEF = """
`git commit` selló lo que estaba en el staging area, el mapa, en una cápsula con tu mensaje, tu
nombre y un hash. El diario nunca se agregó al staging area, así que se queda en la carpeta de
trabajo, sin seguimiento.

La cápsula está en tu bóveda, solo en esta computadora: el remoto (la nave nodriza) sigue vacío. Enviarle
cápsulas es el próximo capítulo.

Comandos para recordar:

    $ git commit -m "Add the map"   # sella el staging area en un commit
    $ git log                       # la historia, del commit más reciente al más antiguo
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, haz tu predicción.",
        question="Sellas el mapa en una cápsula. ¿Dónde está la cápsula después?",
        options=("Solo en tu bóveda, en esta computadora", "En tu bóveda y en la nave nodriza", "Solo en la nave nodriza"),
        reveal="Solo en tu bóveda: un commit va a tu repositorio, en esta computadora. Nada llega a la nave nodriza hasta que haces push.",
    ),
    "commit": kit.StepText(text="Sella el mapa en una cápsula."),
    "log": kit.StepText(text="Mira la historia."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NO_COMMIT = 'Todavía no hay ninguna cápsula. Sella el staging area con un mensaje: `git commit -m "Add the map"`.'
MAP_MISSING = "Tu commit no contiene `map.txt`. Agrégalo al staging area con `git add map.txt` y vuelve a hacer el commit."
JOURNAL_SEALED = (
    "`journal.txt` también está en un commit, y no estaba listo. Deshacer un commit llega en un capítulo posterior: "
    "vuelve a empezar la misión."
)
JOURNAL_STAGED = "`journal.txt` está en el staging area, y no está listo. `git rm --cached journal.txt` lo vuelve a sacar; el archivo se queda."
SEALED = "El mapa está sellado en una cápsula, y el diario se queda en la carpeta de trabajo."
LOOKED = "`git log` lista tu cápsula: su hash, tu nombre, la fecha y tu mensaje."
NOT_LOOKED = "Ahora mira la historia: escribe `git log`."
