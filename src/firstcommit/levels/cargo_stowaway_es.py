"""Stowaway in Spanish (`cargo_stowaway`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Polizón"
CARD = "Saca un archivo del staging area y lo devuelve a su versión del último commit. La carpeta de trabajo conserva el archivo tal como está."

BRIEFING = """
Durante la noche, el turno de noche actualizó los ajustes del motor y la ruta, y ejecutó
`git add .` para agregarlos al staging area. Eso también se llevó la contraseña de la esclusa de
`keys.txt`.

La misión termina cuando hayas mirado con `git status`, `keys.txt` esté fuera del staging area y
siga en la carpeta de trabajo, y `engine.cfg` y `route.txt` sigan en el staging area.
"""

HINTS = [
    "`git status` nombra el comando que saca un archivo del staging area.",
    "Escribe `git restore --staged keys.txt`. Conserva el archivo en la carpeta de trabajo.",
    "Cada línea de la misión, en orden:\n\n    $ git status\n    $ git restore --staged keys.txt",
]

DEBRIEF = """
`git restore --staged keys.txt` devolvió el staging area al último commit para ese único archivo:
el commit no tiene `keys.txt`, así que las llaves salieron del staging area. La carpeta de trabajo
no se tocó, así que el archivo sigue ahí, sin seguimiento. El motor y la ruta siguen en el staging
area para el próximo commit.

Comandos para recordar:

    $ git status                        # mira qué está en el staging area
    $ git restore --staged keys.txt     # saca un archivo del staging area y lo conserva
"""

STEPS = {
    "look": kit.StepText(text="Averigua qué agregó al staging area el turno de noche."),
    "unstage": kit.StepText(text="Saca las llaves del staging area y conserva el archivo."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "`git status` lista los tres archivos del staging area, `keys.txt` entre ellos, y el comando que saca uno."
NOT_LOOKED = "Mira primero: `git status` muestra lo que el turno de noche agregó al staging area."
KEYS_ABOARD = "`keys.txt` sigue en el staging area, así que el próximo commit se llevaría la contraseña. Sácalo del staging area y conserva el archivo."
DELETED = (
    "`keys.txt` desapareció de la carpeta de trabajo, y sigue en el staging area. `git restore keys.txt` lo copia de vuelta "
    "desde el staging area; después, sácalo del staging area."
)
KEYS_LOST = (
    "`keys.txt` no está ni en la carpeta de trabajo ni en el staging area, y ningún commit lo tiene: esa copia de la "
    "contraseña se perdió. Sacar algo del staging area nunca exige borrarlo. Vuelve a empezar la misión."
)
KEYS_COMMITTED = (
    "`keys.txt` ya está en un commit, así que la contraseña está en la historia de este repositorio. Deshacer un commit "
    "llega en un capítulo posterior: vuelve a empezar la misión."
)
CARGO_UNSTAGED = "Los ajustes del motor y la ruta deben seguir en el staging area para el próximo commit: `git add engine.cfg route.txt` los vuelve a agregar."
UNSTAGED = "`keys.txt` está fuera del staging area y sigue en la carpeta de trabajo, y el motor y la ruta siguen en el staging area."
RM_REFUSED = (
    "Git se negó, y así conservaste tu archivo: sin `--cached`, `git rm` borra el archivo también de la carpeta de trabajo. "
    "`git restore --staged keys.txt` lo saca solo del staging area."
)
