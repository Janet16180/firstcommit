"""Welcome aboard in Spanish (`liftoff_aboard`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Bienvenida a bordo"
CARD = "Lista los archivos de la carpeta actual. `ls -a` también lista los ocultos: los que tienen un nombre que empieza con punto."
SCENE = [
    "Soy Rama, la computadora de la nave. Te acompañaré durante el entrenamiento.",
    "La misión: construir bases por toda la galaxia sin perder nunca ni una línea de trabajo.",
    "Para eso usamos Git. Cada vez que se lo pides, Git guarda una instantánea de tu proyecto, y puedes volver a cualquier instantánea que hayas guardado.",
    "A Git le das órdenes escribiendo en la terminal. Aquí equivocarse no tiene riesgo: es una carpeta de práctica, y cada mensaje de error te enseña algo.",
]

BRIEFING = """
Estás en tu base lunar, en la carpeta `project`. Mira qué hay en la carpeta y luego pregúntale
a Git cómo están las cosas.

La misión termina cuando hayas listado la carpeta con `ls` y hayas escrito `git status`.
"""

HINTS = [
    "Escribe `ls` y presiona Enter. Lista lo que hay en la carpeta.",
    "Ahora escribe `git status`. Si muestra un error, bien: lee lo que dice.",
    "Cada línea de la misión, en orden:\n\n    $ ls\n    $ git status",
]

DEBRIEF = """
`git status`, como la mayoría de los comandos de Git, solo funciona dentro de un repositorio: una
carpeta de la que Git guarda la historia. Tu carpeta todavía no lo es, así que `git status` se
detuvo con un error y no cambió nada. La próxima misión convierte esta carpeta en un repositorio
con `git init`.

Comandos para recordar:

    $ ls            # lista los archivos de esta carpeta
    $ git status    # pregunta a Git cómo están las cosas
"""

STEPS = {
    "look": kit.StepText(text="Mira qué hay en la carpeta."),
    "ask": kit.StepText(text="Pregúntale a Git cómo están las cosas."),
}

LISTED = "Estos son los archivos de la carpeta: `map.txt` y `journal.txt`, archivos normales que todavía no guarda ningún repositorio."
NOT_LISTED = "Escribe `ls` y presiona Enter para listar los archivos de la carpeta."
REFUSED = "Le preguntaste a Git: esta carpeta todavía no es un repositorio, así que se negó. La próxima misión la convierte en uno."
ANSWERED = "Le preguntaste a Git y te respondió: esta carpeta es un repositorio, así que `git status` puede decir cómo están las cosas."
REFUSED_EARLIER = (
    "Le preguntaste a Git antes de listar la carpeta: esta carpeta todavía no es un repositorio, así que se negó. "
    "La próxima misión la convierte en uno."
)
ANSWERED_EARLIER = "Le preguntaste a Git antes de listar la carpeta, y te respondió: esta carpeta es un repositorio."
NOT_ASKED = "Ahora pregúntale a Git cómo están las cosas: escribe `git status`."
NO_REPOSITORY_YET = (
    "Git no encontró ningún repositorio aquí, así que no tiene nada que contar. Esa es la lección: `git status` solo funciona dentro de un repositorio. "
    "La próxima misión convierte esta carpeta en uno."
)
