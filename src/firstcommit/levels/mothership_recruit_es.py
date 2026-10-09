"""New recruit in Spanish (`mothership_recruit`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Recluta nuevo"
CARD = "Copia un repositorio en una carpeta nueva con su nombre: toda su historia, un remoto llamado `origin` con la dirección y un branch como `main` para trabajar."
SCENE = [
    "La Base avanzada 3 llama a un recluta nuevo: tú. Su repositorio te espera en el remoto (la nave nodriza).",
    "Un clone copia toda la cadena de cápsulas, no solo los archivos más recientes.",
]

BRIEFING = """
Hoy te unes a la Base avanzada 3. Su repositorio está en la nave nodriza, en `github.com/moonbase/project.git`
desde la carpeta donde se abre tu terminal. Consigue tu propia copia y averigua cuánta historia
de la base llegó con ella.

La misión termina cuando `project` sea tu clone de la base y hayas leído su historia y contado
sus commits.
"""

HINTS = [
    "`git clone` recibe la dirección y crea una carpeta con su nombre: `git clone github.com/moonbase/project.git` crea `project`.",
    "Primero entra al clone: `cd project && git log --oneline` muestra una línea por commit.",
    "Cada línea, en orden; la respuesta es la cantidad de líneas que muestra el log:\n\n    $ git clone github.com/moonbase/project.git\n    $ cd project && git log --oneline",
]

DEBRIEF = """
`git clone` copió toda la historia de la base en `project`: cada commit, no solo los archivos más
recientes. Llamó `origin` a la dirección y creó tu propio branch `main` en el commit donde estaba
el `main` de la base.

`git log --oneline` mostró nombres entre paréntesis en el commit más nuevo, como `main` y
`origin/main`. El sector Etiquetas, después de Base 7, explica qué son.

En el trabajo, lo primero que haces al llegar a un equipo es clonar su repositorio, con la
dirección que muestra GitHub.

Comandos para recordar:

    $ git clone github.com/moonbase/project.git   # copia un repositorio con toda su historia
    $ git log --oneline                           # una línea por commit, del más nuevo al más viejo
"""

STEPS = {
    "clone": kit.StepText(text="Clona el repositorio de la base."),
    "log": kit.StepText(text="Entra a tu clone y lee su historia."),
    "count": kit.StepText(
        text="Cuenta los commits que llegaron con el clone.",
        question="¿Cuántos commits tiene tu clone?",
        placeholder="un número",
    ),
}

NOT_CLONED = "Todavía no hay un clone en `project`. Copia la base: `git clone github.com/moonbase/project.git`."
NOT_A_CLONE = "`project` no es un clone de la base: su `origin` no es `github.com/moonbase/project.git`. Sal del nivel y vuelve a empezarlo."
CLONED = "`project` es tu clone de la base."
READ = "Esa es toda la historia de la base, del commit más nuevo al más viejo."
NOT_READ = "Lee la historia de tu clone: `cd project && git log --oneline`."
RIGHT_COUNT = "Correcto: tu clone tiene todos los commits de la base, no solo sus archivos más recientes."
WRONG_COUNT = "Tu clone no tiene esa cantidad de commits. `git log --oneline` muestra una línea por commit: cuéntalas."
NOT_A_NUMBER = "Escribe la cantidad de commits, por ejemplo 3."
NOT_CLONED_YET = "Todavía no hay un repositorio aquí. Primero clona la base: `git clone github.com/moonbase/project.git`."
OUTSIDE_THE_CLONE = "Tu terminal todavía no está en el clone: está en la carpeta que lo contiene. Entra a él: `cd project`."
