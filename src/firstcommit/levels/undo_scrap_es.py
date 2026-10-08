"""Scrap the workshop in Spanish (`undo_scrap`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Desecha el taller"
CARD = "Reemplaza un archivo de la carpeta de trabajo por su versión del staging area. Las líneas que nunca agregaste al staging area ni guardaste en un commit se pierden para siempre."
SCENE = [
    "Git lleva un registro de vuelo: lo que agregaste al staging area, lo que guardaste en commits y lo que llegó a la nave nodriza.",
    "Tu carpeta de trabajo está fuera de la caja. Las líneas que solo escribiste ahí nunca quedaron registradas.",
]

BRIEFING = """
El experimento de anoche en `engine.cfg` recalentó el motor. Nunca se agregó al staging area ni se
guardó en un commit; deséchalo y vuelve a los ajustes del último commit. Tus notas en `notes.txt`
están en el staging area para el próximo commit: consérvalas.

La misión termina cuando hayas mirado el experimento con `git diff`, `engine.cfg` haya vuelto a su
versión del commit, y `notes.txt` siga en el staging area.
"""

HINTS = [
    "`git diff` muestra las líneas de la carpeta de trabajo que no están en el staging area: el experimento.",
    "`git restore engine.cfg` reemplaza el archivo por su versión del staging area, que es la del commit.",
    "Cada línea de la misión, en orden:\n\n    $ git diff\n    $ git restore engine.cfg",
]

DEBRIEF = """
`git restore engine.cfg` copió la versión del archivo que está en el staging area encima de la de
la carpeta de trabajo. Las líneas del experimento nunca se agregaron al staging area ni se
guardaron en un commit, así que no existía ninguna copia de ellas: Git no puede devolverlas, y
ningún comando lo hará.

`notes.txt` estuvo a salvo todo el tiempo: lo que está en el staging area o en un commit está
dentro del registro de vuelo de Git. Antes de desechar un archivo, `git diff` muestra exactamente
lo que vas a perder.

Comandos para recordar:

    $ git diff                 # lo que está en la carpeta de trabajo y no en el staging area
    $ git restore engine.cfg   # deséchalo: vuelve a la versión del staging area
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Desechas el experimento con `git restore engine.cfg`. ¿Podría Git devolverte sus líneas después?",
        options=("Sí, desde el último commit", "No: nunca se guardaron en Git"),
        reveal="No. El último commit tiene los ajustes viejos, no el experimento: sus líneas nunca se agregaron al staging area ni se guardaron en un commit, así que Git nunca tuvo una copia.",
    ),
    "look": kit.StepText(text="Mira el experimento que estás por desechar."),
    "scrap": kit.StepText(text="Desecha el experimento y conserva tus notas del staging area."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "`git diff` muestra el experimento: las líneas que están en la carpeta de trabajo y en ningún otro lugar."
NOT_LOOKED = "Primero mira lo que perderías: `git diff`."
NOT_SCRAPPED = "`engine.cfg` todavía tiene el experimento. Deséchalo: `git restore engine.cfg`."
NOTES_LOST = "Tus notas del staging area desaparecieron: no estaban en ningún commit. Vuelve a empezar la misión."
NOTES_UNSTAGED = "`notes.txt` ya no está en el staging area. Vuelve a agregarlo: `git add notes.txt`."
SCRAPPED = "`engine.cfg` volvió a los ajustes del commit, y tus notas siguen en el staging area."
GONE = (
    "Las líneas del experimento se perdieron para siempre: nunca se agregaron al staging area ni se guardaron en un commit, "
    "así que Git no tiene ninguna copia. Git guarda lo que está en el staging area o en un commit; estas líneas no estaban en ninguno."
)
