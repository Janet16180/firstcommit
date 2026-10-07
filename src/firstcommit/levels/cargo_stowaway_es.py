"""Stowaway in Spanish (`cargo_stowaway`)."""

from firstcommit import kit

TITLE = "Polizón"
CARD = "Saca un archivo del área de preparación y lo devuelve a su versión del último commit. La carpeta de trabajo conserva el archivo tal como está."

BRIEFING = """
Durante la noche, el turno de noche actualizó los ajustes del motor y la ruta, y ejecutó
`git add .` para prepararlos. Eso se llevó también la contraseña de la esclusa de `keys.txt`.

La misión termina cuando hayas mirado con `git status`, `keys.txt` esté fuera del área de
preparación y siga en la carpeta de trabajo, y `engine.cfg` y `route.txt` sigan preparados.
"""

HINTS = [
    "`git status` nombra el comando que saca un archivo del área de preparación.",
    "Escribe `git restore --staged keys.txt`. Conserva el archivo en la carpeta de trabajo.",
]

DEBRIEF = """
`git restore --staged keys.txt` devolvió el área de preparación al último commit para ese único
archivo: el commit no tiene `keys.txt`, así que las llaves salieron del área de preparación. La
carpeta de trabajo no se tocó, así que el archivo sigue ahí, sin seguimiento. El motor y la ruta
siguen preparados para el próximo commit.

Comandos para recordar:

    $ git status                        # mira qué está preparado
    $ git restore --staged keys.txt     # saca un archivo del área de preparación y lo conserva
"""

STEPS = {
    "look": kit.StepText(text="Averigua qué preparó el turno de noche."),
    "unstage": kit.StepText(text="Saca las llaves del área de preparación y conserva el archivo."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` ha desaparecido. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "`git status` lista los tres archivos preparados, `keys.txt` entre ellos, y el comando que saca uno del área de preparación."
NOT_LOOKED = "Mira primero: `git status` muestra lo que preparó el turno de noche."
KEYS_ABOARD = "`keys.txt` sigue preparado, así que el próximo commit se llevaría la contraseña. Sácalo del área de preparación y conserva el archivo."
DELETED = (
    "`keys.txt` ha desaparecido de la carpeta de trabajo, y sigue preparado. `git restore keys.txt` lo copia de vuelta "
    "desde el área de preparación; después, sácalo del área de preparación."
)
KEYS_LOST = (
    "`keys.txt` no está ni en la carpeta de trabajo ni en el área de preparación, y ningún commit lo tiene: esa copia de la "
    "contraseña se ha perdido. Sacar algo del área de preparación nunca exige borrarlo. Vuelve a empezar la misión."
)
KEYS_COMMITTED = (
    "`keys.txt` ya está en un commit, así que la contraseña está en la historia de este repositorio. Deshacer un commit "
    "llega en un capítulo posterior: vuelve a empezar la misión."
)
CARGO_UNSTAGED = "Los ajustes del motor y la ruta deben seguir preparados para el próximo commit: `git add engine.cfg route.txt` vuelve a prepararlos."
UNSTAGED = "`keys.txt` está fuera del área de preparación y sigue en la carpeta de trabajo, y el motor y la ruta siguen preparados."
RM_REFUSED = (
    "Git se negó, y así conservaste tu archivo: sin `--cached`, `git rm` borra el archivo también de la carpeta de trabajo. "
    "`git restore --staged keys.txt` lo saca solo del área de preparación."
)
