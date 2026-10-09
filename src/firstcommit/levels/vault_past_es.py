"""Look into the past in Spanish (`vault_past`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Mirar al pasado"
CARD = "Imprime el archivo exactamente como lo guardó ese commit. Tu carpeta de trabajo no cambia."
SCENE = [
    "El indicador marca 40% esta noche. La pregunta es sobre hace unos días.",
    "Cada commit de tu repositorio (la bóveda) guarda cada archivo como estaba cuando se hizo el commit, así que la respuesta está ahí.",
]

BRIEFING = """
Esta noche el indicador de combustible marca 40%. El capitán quiere saber cuánto marcaba después
de la parada en Phobos, hace unos días. Nadie lo anotó, pero la bóveda guarda cada commit.

La misión termina cuando hayas encontrado los commits que cambiaron `fuel.txt`, hayas mirado el
commit de Phobos, hayas leído `fuel.txt` como lo guardó ese commit y le hayas respondido al
capitán.
"""
QUESTION = "Respóndele al capitán: ¿cuánto marcaba el indicador de combustible después de la parada en Phobos?"
PLACEHOLDER = "una lectura, como 50%"

HINTS = [
    "`git log fuel.txt` lista solo los commits que cambiaron `fuel.txt`. El de Phobos lo dice en su mensaje.",
    "Junta el hash del commit, dos puntos y el nombre del archivo: `git show <hash>:fuel.txt`. Bastan los 7 primeros caracteres del hash.",
    "Cada línea de la misión, en orden; después responde 60%:\n\n    $ git log fuel.txt\n    $ git show ccf9485\n    $ git show ccf9485:fuel.txt",
]

DEBRIEF = """
Cada commit guarda cada archivo exactamente como estaba. `git log fuel.txt` encontró los commits
que cambiaron el archivo, y `git show <hash>:fuel.txt` lo imprimió como lo guardó uno de ellos,
mientras tu carpeta de trabajo seguía igual. Todo el pasado sigue ahí.

En Viajes en el tiempo también vas a traer una versión vieja de vuelta a tu carpeta.

Comandos para recordar:

    $ git log fuel.txt              # los commits que cambiaron un archivo
    $ git show <hash>               # lo que cambió un commit
    $ git show <hash>:fuel.txt      # el archivo como lo guardó ese commit
"""

STEPS = {
    "log": kit.StepText(text="Encuentra los commits que cambiaron el registro de combustible."),
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Escribes `git show` y el hash del commit de Phobos. ¿Qué imprime?",
        options=("`fuel.txt` como estaba entonces", "Lo que cambió ese commit", "Todos los archivos del proyecto"),
        reveal=(
            "Lo que cambió ese commit: su mensaje, y después el cambio en sí, donde una línea con `-` es lo que se quitó y una "
            "con `+` lo que se puso. Para leer un archivo entero como estaba, el siguiente paso agrega el nombre del archivo."
        ),
    ),
    "show": kit.StepText(text="Mira el commit de Phobos."),
    "file": kit.StepText(text="Lee el registro de combustible como estaba entonces."),
}

LOGGED = (
    "`git log fuel.txt` se salta los commits que no tocaron `fuel.txt`: quedan cuatro de los seis, del más reciente al más "
    "antiguo. El segundo es la parada en Phobos. Copia los 7 primeros caracteres de su hash, el código largo después de "
    "`commit`: `ccf9485`."
)
NOT_LOGGED = "Lista solo los commits que cambiaron el registro de combustible: `git log fuel.txt`."
SHOWN = (
    "El cambio: `-` quitó `75%`, `+` puso `60%`; las líneas de arriba solo dicen qué archivo es. Eso responde la pregunta de "
    "esta noche, pero solo porque el archivo tiene una línea. Para un archivo entero como estaba, pon dos puntos y el nombre "
    "del archivo después del hash."
)
NOT_SHOWN = "Mira el commit de Phobos: `git show` y su hash, `ccf9485`."
READ = (
    "El registro de combustible exactamente como lo guardó el commit de Phobos. Tu carpeta sigue diciendo 40%: leer el pasado "
    "no cambia nada.\n\n"
    "Ahora respóndele al capitán en el cuadro de respuesta: ¿cuánto marcaba el indicador después de Phobos?"
)
NOT_READ = "Lee el registro de combustible como lo guardó el commit de Phobos: `git show ccf9485:fuel.txt`."
RIGHT = "Correcto: 60% después de Phobos. El capitán tiene su respuesta, y la bóveda sigue tal como estaba."
OTHER_STOP = "Eso es lo que marcaba el indicador en otra parada. Busca el commit cuyo mensaje nombra Phobos."
NOT_A_READING = "Escribe la lectura como la imprimió `git show`, por ejemplo `50%`."
SPACE_NOT_COLON = "Con un espacio, git muestra lo que ese commit cambió en `fuel.txt`. Con dos puntos, el archivo mismo como estaba."
