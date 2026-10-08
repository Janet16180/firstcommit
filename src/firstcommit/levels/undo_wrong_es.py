"""Wrong course in Spanish (`undo_wrong`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Rumbo equivocado"
CARD = "Mueve el branch donde estás a otro commit, y hace que el staging area y la carpeta de trabajo coincidan con él. Los commits que deja siguen en Git; una etiqueta hace que sea fácil encontrarlos."
SCENE = [
    "Dos cápsulas de un relevamiento cayeron en `main`. Les correspondía un rumbo propio.",
    "Mover una etiqueta deja una marca en la cinta del registro de vuelo, y las cápsulas se quedan donde estaban.",
]

BRIEFING = """
Hiciste por error dos commits de un relevamiento en `main`: les corresponde un branch propio, y la
nave nodriza todavía no los vio. Ponles una etiqueta, y después mueve `main` de vuelta a donde está
el `main` de la nave nodriza.

La misión termina cuando un branch `rescue` tenga tus dos commits, y `main` haya vuelto a
`origin/main` con la carpeta de trabajo igual a él.
"""

HINTS = [
    "`git branch rescue` pone una etiqueta nueva sobre el commit donde estás, así los dos commits conservan un nombre.",
    "`git reset --hard origin/main` mueve `main` de vuelta al `main` de la nave nodriza, con los archivos.",
    "Cada línea de la misión, en orden:\n\n    $ git branch rescue\n    $ git reset --hard origin/main",
]

DEBRIEF = """
`git reset --hard origin/main` movió la etiqueta `main` hacia atrás en la cadena, e hizo que el
staging area y la carpeta de trabajo coincidan con ese commit. No borró ningún commit: tus dos
commits siguen ahí, con la etiqueta `rescue`, listos para trabajar en ellos como un branch.

Sin una etiqueta, seguirían existiendo un tiempo, como fantasmas que ninguna etiqueta sostiene; el
reflog, el registro de vuelo de Git, recuerda dónde estaba `main`. Usa reset solo con commits que
nadie más tiene: en un branch con push, `git revert` es la forma segura de deshacer.

`--soft` y `--mixed` también mueven la etiqueta, pero conservan tus cambios en el staging area o en
la carpeta de trabajo; `--hard` es el que reescribe los archivos.

Comandos para recordar:

    $ git branch rescue              # primero, una etiqueta sobre los commits
    $ git reset --hard origin/main   # después, mueve main hacia atrás
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Le pones la etiqueta `rescue` a tus dos commits y después mueves `main` hacia atrás con `git reset --hard origin/main`. ¿Dónde están los dos commits después del reset?",
        options=("Borrados", "Siguen ahí, con la etiqueta rescue"),
        reveal="Siguen ahí, con la etiqueta `rescue`. Un reset mueve una etiqueta; no borra ningún commit.",
    ),
    "rescue": kit.StepText(text="Ponle una etiqueta a tus dos commits."),
    "reset": kit.StepText(text="Mueve `main` de vuelta al `main` de la nave nodriza."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_LABELLED = "Primero ponle una etiqueta a tus dos commits: `git branch rescue`."
LABELLED = "`rescue` tiene tus dos commits."
GHOSTS = (
    "`main` volvió atrás y ninguna etiqueta sostiene ahora tus dos commits, pero Git todavía los tiene: el reflog recuerda "
    "dónde estaba `main`. `git branch rescue HEAD@{1}` les pone la etiqueta."
)
NOT_RESET = "`main` todavía tiene los dos commits. Muévelo hacia atrás: `git reset --hard origin/main`."
DIRTY = "`main` volvió, pero la carpeta de trabajo no coincide con él. `git reset --hard origin/main` la hace coincidir."
RESET = "`main` volvió a `origin/main`, y `rescue` tiene tus dos commits."
SHARED = "El `main` de la nave nodriza ya tiene tus dos commits del relevamiento: otros pueden traerlos con pull. Vuelve a empezar la misión."
MOVED_BACK = (
    "`main` volvió atrás. Los commits que dejó siguen en Git: con una etiqueta si hiciste una, o como fantasmas que el "
    "reflog todavía alcanza."
)
