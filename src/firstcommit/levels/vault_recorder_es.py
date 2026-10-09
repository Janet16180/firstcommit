"""Flight recorder in Spanish (`vault_recorder`)."""

from firstcommit import kit

TITLE = "Registro de vuelo"
CARD = "Lista los commits que cambiaron el archivo, del más reciente al más antiguo, cada uno con su hash, autor, fecha y mensaje."
SCENE = [
    "Alarma: el nivel de oxígeno de la base está bajo. Alguien cambió el ajuste hace unos días.",
    "Cada commit es una entrada del registro de vuelo de la base: quién cambió qué, y cuándo. Git las guarda todas.",
]

BRIEFING = """
Suena la alarma de oxígeno. `oxygen.cfg` estaba bien cuando se montó la base, y desde entonces un
commit lo cambió. Encuentra ese commit en la historia, y quién lo hizo.

La misión termina cuando hayas leído la historia con `git log`, hayas escrito el hash del commit
que cambió `oxygen.cfg` y hayas dicho quién es su autor.
"""
QUESTION = "¿Quién hizo el commit que cambió `oxygen.cfg`?"
PLACEHOLDER = "un nombre"

HINTS = [
    "`git log` lista todos los commits, del más reciente al más antiguo, con su hash, autor, fecha y mensaje.",
    "Dale a `git log` el nombre del archivo: `git log oxygen.cfg` lista solo los commits que lo cambiaron.",
    "El commit más reciente que lista `git log oxygen.cfg` es el que buscas: su línea `commit` tiene el hash, y su línea `Author`, el nombre.",
    "Cada línea, en orden; luego escribe el hash de la línea `commit` de la entrada más nueva, y el nombre de su línea `Author`:\n\n    $ git log\n    $ git log oxygen.cfg",
]

DEBRIEF = """
`git log oxygen.cfg` mostró solo los commits que cambiaron el archivo: el que montó la base y el
que bajó el oxígeno. Cada commit guarda su autor, su fecha y su mensaje, así que la historia dice
quién cambió qué, y cuándo.

Un mensaje puede decir poco (*Night tweaks*) o confundir; los cambios en sí, nunca.

Comandos para recordar:

    $ git log              # todos los commits, del más reciente al más antiguo
    $ git log oxygen.cfg   # solo los commits que cambiaron este archivo
"""

STEPS = {
    "read": kit.StepText(text="Lee la historia de la base."),
    "commit": kit.StepText(text="Encuentra el commit que cambió `oxygen.cfg`.", question="¿Cuál es su hash?", placeholder="un hash, como 3f9a2c1"),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
READ = "Esa es la historia de la base, del commit más reciente al más antiguo: cada uno con su hash, autor, fecha y mensaje."
NOT_READ = "Lee la historia: escribe `git log`."
FOUND = "Ese es el commit que bajó el oxígeno."
NOT_A_HASH = "Escribe el hash del commit tal como lo muestra `git log`, al menos sus 4 primeros caracteres."
NO_SUCH_COMMIT = "Ningún commit de esta base empieza por esos caracteres. Copia el hash de una línea `commit` de `git log`."
SET_UP = "Ese commit creó `oxygen.cfg` con el ajuste correcto, cuando se montó la base. El que buscas cambió el archivo después."
OTHER_COMMIT = "Ese commit no tocó `oxygen.cfg`. `git log oxygen.cfg` lista solo los commits que lo cambiaron."
RIGHT_AUTHOR = "Correcto: esa persona bajó el oxígeno."
WRONG_AUTHOR = "Esa persona no hizo ese commit. Su línea `Author` en `git log oxygen.cfg` dice quién fue."
