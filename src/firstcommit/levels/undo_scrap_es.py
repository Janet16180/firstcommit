"""Scrap the workshop in Spanish (`undo_scrap`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Desecha el taller"
CARD = "Reemplaza un archivo de la carpeta de trabajo por la copia de Git: la del staging area si la hay, si no la del commit. Las líneas que nunca agregaste al staging area ni guardaste en un commit se pierden para siempre."
SCENE = [
    "El experimento de anoche recalentó el motor. En `engine.cfg` cambió una línea y se agregó otra: las dos líneas rojas.",
]

BRIEFING = """
El experimento de anoche en `engine.cfg` recalentó el motor. Deséchalo y vuelve a los ajustes del
commit. Tus notas en `notes.txt` están en el staging area para el próximo commit: consérvalas.

La misión termina cuando hayas mirado el experimento con `git diff`, `engine.cfg` haya vuelto a su
versión del commit y `git status` muestre `notes.txt` todavía en el staging area.
"""

HINTS = [
    "`git diff` muestra las líneas de la carpeta de trabajo que no están en el staging area: el experimento.",
    "`git restore engine.cfg` copia la copia de Git del archivo encima de la tuya. `engine.cfg` nunca estuvo en el staging area, así que la copia de Git es la del commit.",
    "Cada línea de la misión, en orden:\n\n    $ git diff\n    $ git restore engine.cfg\n    $ git status",
]

DEBRIEF = """
`git restore engine.cfg` copió la copia de Git encima de tu archivo: la del staging area cuando la
hay, si no la del commit. `engine.cfg` nunca estuvo en el staging area, así que recibió el
`power=80` del commit. Las líneas del experimento nunca se agregaron al staging area ni se
guardaron en un commit, así que Git no tenía copia de ellas, y ningún comando puede devolverlas.

`notes.txt` estuvo a salvo todo el tiempo: estaba dentro de "Git tiene una copia". Antes de
desechar un archivo, `git diff` muestra exactamente lo que vas a perder.

En el sector 2, `git restore --staged` sacó un archivo del staging area y dejó la copia de tu
carpeta como estaba. Sin `--staged`, `git restore` reemplaza la copia de tu carpeta: esa es la que
puede perder trabajo.

Comandos para recordar:

    $ git diff                 # lo que está en la carpeta de trabajo y no en el staging area
    $ git restore engine.cfg   # deséchalo: vuelve a la copia de Git
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Desechas el experimento con `git restore engine.cfg`. Mañana lo quieres de vuelta. ¿Puede Git devolverte las dos líneas rojas?",
        options=("Sí, Git guarda todas las versiones de un archivo", "No, se perdieron para siempre"),
        reveal="No. Git guarda solo lo que agregaste al staging area o guardaste en un commit. La línea punteada lo muestra: el staging area y tus commits están adentro. Las líneas rojas existen solo en tu carpeta de trabajo, así que Git nunca tuvo una copia.",
    ),
    "look": kit.StepText(text="Mira el experimento."),
    "scrap": kit.StepText(text="Deséchalo."),
    "status": kit.StepText(text="Comprueba que tus notas siguen en el staging area."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "`git diff` muestra lo que está en tu carpeta de trabajo y no en el staging area. `-` es la línea que tiene Git, `+` las líneas que solo tienes tú. Míralas antes de que se vayan."
NOT_LOOKED = "Primero mira lo que perderías: `git diff`."
NOT_SCRAPPED = "`engine.cfg` todavía tiene el experimento. Deséchalo: `git restore engine.cfg`."
NOTES_LOST = "Tus notas del staging area desaparecieron: no estaban en ningún commit. Vuelve a empezar la misión."
NOTES_UNSTAGED = "`notes.txt` ya no está en el staging area. Vuelve a agregarlo: `git add notes.txt`."
SCRAPPED = "`git restore` copió la copia de Git de `engine.cfg`, `power=80`, encima de la tuya. Las dos líneas rojas se perdieron para siempre. `git restore` no mostró nada: la mayoría de los comandos de git no dicen nada cuando funcionan."
STATUS_READ = "Tus notas siguen en el staging area, listas para el próximo commit. `git restore` cambió solo el archivo que nombraste."
NOT_STATUS = "Comprueba que tus notas siguen en el staging area: `git status`."
GONE = "Las líneas del experimento se perdieron para siempre: Git no tenía copia de ellas."
