"""Cargo inspection in Spanish (`vault_inspection`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Inspección de carga"
CARD = "Muestra exactamente lo que se llevará el próximo commit. Míralo antes de cada commit."
SCENE = [
    "Inspección al amanecer. El inspector abre cada cápsula de tu repositorio (la bóveda), y en ninguna puede haber una contraseña.",
]

BRIEFING = """
El inspector llega al amanecer. Alguien ejecutó `git add .` para agregar el parche del reactor al
staging area, y eso también se llevó `keys.txt` y `debug.log`.

La misión termina cuando el parche del reactor esté guardado en una cápsula nueva, `keys.txt` no
esté en ninguna cápsula y siga en la carpeta de trabajo, y `debug.log` esté sin seguimiento.
"""

HINTS = [
    "Son el staging area (el muelle de carga) y la bóveda a la vez: lo que está en el staging area entra en la próxima cápsula.",
    "Primero saca a los polizones del muelle, conserva sus archivos, y luego sella lo que queda.",
    'Cada línea de la misión, en orden:\n\n    $ git restore --staged keys.txt\n    $ git restore --staged debug.log\n    $ git commit -m "Lower the reactor limit"',
]

DEBRIEF = """
Sacaste las llaves y el log de depuración del staging area, conservaste los dos archivos y
sellaste solo el parche del reactor. Una cápsula contiene exactamente lo que estaba en el staging
area cuando la sellaste, así que el momento de mirar es antes del commit: `git status`, o
`git diff --staged`.

Comandos para recordar:

    $ git restore --staged keys.txt    # saca un archivo del staging area y lo conserva
    $ git diff --staged                # lo que se llevará el próximo commit
    $ git commit -m "Lower the reactor limit"
"""

STEPS = {
    "keys": kit.StepText(text="`keys.txt` no está en ninguna cápsula, y sigue en la carpeta de trabajo."),
    "log": kit.StepText(text="`debug.log` está sin seguimiento."),
    "reactor": kit.StepText(text="El parche del reactor está guardado en una cápsula nueva."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
REACTOR_SAVED = "El parche del reactor está sellado en una cápsula nueva."
REACTOR_NOT_SAVED = "El parche del reactor todavía no está en ninguna cápsula nueva."
KEYS_SAFE = "`keys.txt` no está en ninguna cápsula, y sigue en la carpeta de trabajo."
KEYS_ABOARD = "`keys.txt` está en el staging area: la próxima cápsula se llevaría la contraseña."
KEYS_DELETED = "`keys.txt` desapareció de la carpeta de trabajo."
KEYS_LOST = "`keys.txt` no está en ninguna parte del repositorio ni en ninguna cápsula: esa copia de la contraseña se perdió. Vuelve a empezar la misión."
KEYS_SEALED = "La contraseña de `keys.txt` está sellada en una cápsula. Deshacer un commit llega en un capítulo posterior: vuelve a empezar la misión."
LOG_SAFE = "`debug.log` está sin seguimiento, en la carpeta de trabajo."
LOG_ABOARD = "`debug.log` está en el staging area: la próxima cápsula se lo llevaría."
LOG_DELETED = "`debug.log` desapareció de la carpeta de trabajo."
LOG_SEALED = "`debug.log` está sellado en una cápsula. Deshacer un commit llega en un capítulo posterior: vuelve a empezar la misión."
EVERYTHING_STAGED = "Eso volvió a agregar al staging area todos los archivos de la carpeta: `keys.txt` y `debug.log` están en el muelle."
